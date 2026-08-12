"""Evidence evaluators for the lab-grader rubric DSL.

Implements evaluators for Task 7 (shell, file-exists) and Task 8
(failure-mode-clean, journey-event-present, primitive-authored).

Each evaluator returns an :class:`EvidenceResult` dataclass:
  - ``passed``: whether the criterion is satisfied
  - ``score``:  0.0-1.0 (1.0 = full credit, 0.0 = zero credit)
  - ``note``:   human-readable explanation for the student/reviewer
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from primitives._llm import LLMBackend
from primitives.failure_mode_audit.shared.auditor import SEVERITY_ORDER, audit_path
from primitives.lab_grader.shared.parser import (
    CompoundEvidence,
    EvidenceUnion,
    FailureModeCleanEvidence,
    FileExistsEvidence,
    JourneyEventPresentEvidence,
    LlmJudgedEvidence,
    PrimitiveAuthoredEvidence,
    ShellEvidence,
)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class EvidenceResult:
    """Outcome of evaluating a single evidence node."""

    passed: bool
    score: float  # 0.0-1.0
    note: str


# ---------------------------------------------------------------------------
# Shell evaluator
# ---------------------------------------------------------------------------


def evaluate_shell(ev: ShellEvidence, lab_root: Path) -> EvidenceResult:
    """Run ``ev.cmd`` in ``lab_root`` and check the exit code.

    Args:
        ev:       A :class:`ShellEvidence` model from the parsed rubric.
        lab_root: Absolute path to the lab root directory (cwd for the subprocess).

    Returns:
        :class:`EvidenceResult` with ``passed=True`` when the process exit
        code matches ``ev.expect_exit``.
    """
    try:
        proc = subprocess.run(  # noqa: S602
            ev.cmd,
            shell=True,
            executable="/bin/sh",
            cwd=lab_root,
            capture_output=True,
            timeout=ev.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Command timed out after {ev.timeout}s: {ev.cmd!r}",
        )

    if proc.returncode == ev.expect_exit:
        return EvidenceResult(
            passed=True,
            score=1.0,
            note=(f"Command exited {proc.returncode} (expected {ev.expect_exit}): {ev.cmd!r}"),
        )

    return EvidenceResult(
        passed=False,
        score=0.0,
        note=(f"Command exited {proc.returncode} (expected {ev.expect_exit}): {ev.cmd!r}"),
    )


# ---------------------------------------------------------------------------
# File-exists evaluator
# ---------------------------------------------------------------------------


def evaluate_file_exists(ev: FileExistsEvidence, lab_root: Path) -> EvidenceResult:
    """Check that a file exists (and optionally meets ``min_length``).

    Args:
        ev:       A :class:`FileExistsEvidence` model from the parsed rubric.
        lab_root: Absolute path to the lab root directory.

    Returns:
        :class:`EvidenceResult` with ``passed=True`` when the file is found
        and all optional checks pass.
    """
    target = lab_root / ev.path

    if not target.exists():
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"File not found: {ev.path!r} (resolved to {target})",
        )

    if not target.is_file():
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Path exists but is not a regular file: {ev.path!r}",
        )

    if ev.min_length > 0:
        actual_len = target.stat().st_size
        if actual_len < ev.min_length:
            return EvidenceResult(
                passed=False,
                score=0.0,
                note=(
                    f"File {ev.path!r} is {actual_len} bytes; min_length={ev.min_length} required"
                ),
            )

    return EvidenceResult(
        passed=True,
        score=1.0,
        note=f"File exists: {ev.path!r}",
    )


# ---------------------------------------------------------------------------
# Failure-mode-clean evaluator
# ---------------------------------------------------------------------------


def evaluate_failure_mode_clean(
    ev: FailureModeCleanEvidence,
    lab_root: Path,
) -> EvidenceResult:
    """Invoke U1 ``audit_path()`` and pass if no findings exceed ``max_severity``.

    Args:
        ev:       A :class:`FailureModeCleanEvidence` model from the parsed rubric.
        lab_root: Absolute path to the lab root directory.

    Returns:
        :class:`EvidenceResult` -- ``passed=True`` when zero findings survive
        the severity filter after mode filtering.
    """
    target = lab_root / ev.target if ev.target != "." else lab_root
    all_findings = audit_path(target, modes=ev.modes)

    # Keep only findings whose severity is STRICTLY ABOVE max_severity.
    # e.g. max_severity="low" means "flag anything medium or higher".
    threshold = SEVERITY_ORDER[ev.max_severity]
    excess = [f for f in all_findings if SEVERITY_ORDER[f.severity] > threshold]

    if not excess:
        total = len(all_findings)
        return EvidenceResult(
            passed=True,
            score=1.0,
            note=(
                f"No findings exceed max_severity={ev.max_severity!r} "
                f"({total} finding(s) at or below threshold)"
            ),
        )

    critical_count = sum(1 for f in excess if f.severity == "critical")
    return EvidenceResult(
        passed=False,
        score=0.0,
        note=(
            f"{len(excess)} finding(s) exceed max_severity={ev.max_severity!r} "
            f"({critical_count} critical); "
            f"modes checked: {ev.modes or ['fm1', 'fm2', 'fm3', 'fm4', 'fm5']}"
        ),
    )


# ---------------------------------------------------------------------------
# Safe predicate parser for journey-event-present ``where`` clauses
# ---------------------------------------------------------------------------
#
# Grammar (tokens separated by whitespace):
#
#   expr     ::= and_expr ("or" and_expr)*
#   and_expr ::= atom ("and" atom)*
#   atom     ::= field "==" quoted_value
#              | field "in" "[" quoted_value ("," quoted_value)* "]"
#
# No code-execution primitives are used anywhere in this parser.

# Minimum token counts needed for a valid atom
_EQ_MIN_TOKENS: int = 3  # field == value
_IN_MIN_TOKENS: int = 4  # field in [ ...


def _safe_eval_predicate(expr: str, event: dict[str, Any]) -> bool:
    """Evaluate a restricted predicate string against an event dict.

    Supported forms:
    - ``field == 'value'``
    - ``field in ['a', 'b']``
    - ``and`` / ``or`` joining of the above atoms

    Raises:
        ValueError: if the expression cannot be parsed.
    """
    tokens = _tokenize(expr)
    result, remaining = _parse_or(tokens, event)
    if remaining:
        raise ValueError(f"Unexpected tokens after expression: {remaining!r}")
    return result


def _tokenize(expr: str) -> list[str]:
    """Break a predicate string into tokens."""
    token_re = re.compile(
        r"'[^']*'"  # single-quoted string
        r'|"[^"]*"'  # double-quoted string
        r"|=="  # equality operator
        r"|[a-zA-Z_]\w*"  # identifier / keyword
        r"|\["  # open bracket
        r"|\]"  # close bracket
        r"|,"  # comma
    )
    return token_re.findall(expr)


def _parse_or(tokens: list[str], event: dict[str, Any]) -> tuple[bool, list[str]]:
    result, tokens = _parse_and(tokens, event)
    while tokens and tokens[0] == "or":
        tokens = tokens[1:]
        right, tokens = _parse_and(tokens, event)
        result = result or right
    return result, tokens


def _parse_and(tokens: list[str], event: dict[str, Any]) -> tuple[bool, list[str]]:
    result, tokens = _parse_atom(tokens, event)
    while tokens and tokens[0] == "and":
        tokens = tokens[1:]
        right, tokens = _parse_atom(tokens, event)
        result = result and right
    return result, tokens


def _parse_atom(tokens: list[str], event: dict[str, Any]) -> tuple[bool, list[str]]:
    if len(tokens) < _EQ_MIN_TOKENS:
        raise ValueError(f"Incomplete predicate expression near: {tokens!r}")

    field = tokens[0]
    op = tokens[1]

    if op == "==":
        value = _unquote(tokens[2])
        actual = event.get(field)
        return (str(actual) == value), tokens[_EQ_MIN_TOKENS:]

    if op == "in":
        return _parse_in_list(tokens, field, event)

    raise ValueError(f"Unknown operator {op!r} in predicate; expected '==' or 'in'")


def _parse_in_list(tokens: list[str], field: str, event: dict[str, Any]) -> tuple[bool, list[str]]:
    """Parse ``field in [v1, v2, ...]`` atom starting from the full token list."""
    if len(tokens) < _IN_MIN_TOKENS or tokens[2] != "[":
        raise ValueError(f"Expected '[' after 'in' in: {tokens!r}")
    remaining = tokens[_EQ_MIN_TOKENS:]  # past field, 'in', '['
    values: list[str] = []
    while remaining and remaining[0] != "]":
        if remaining[0] == ",":
            remaining = remaining[1:]
            continue
        values.append(_unquote(remaining[0]))
        remaining = remaining[1:]
    if not remaining or remaining[0] != "]":
        raise ValueError("Unterminated list in predicate")
    remaining = remaining[1:]  # past ']'
    actual = event.get(field)
    return (str(actual) in values), remaining


def _unquote(token: str) -> str:
    """Strip surrounding single or double quotes from a string token."""
    if (token.startswith("'") and token.endswith("'")) or (
        token.startswith('"') and token.endswith('"')
    ):
        return token[1:-1]
    raise ValueError(f"Expected a quoted string, got: {token!r}")


# ---------------------------------------------------------------------------
# Journey-event-present evaluator
# ---------------------------------------------------------------------------


def _resolve_jsonl_path(
    journey_dir: Path, run_id: str | None
) -> tuple[Path | None, EvidenceResult | None]:
    """Return (jsonl_path, None) on success or (None, error_result) on failure."""
    if run_id is not None:
        jsonl_path = journey_dir / f"{run_id}.jsonl"
        if not jsonl_path.exists():
            return None, EvidenceResult(
                passed=False,
                score=0.0,
                note=f"Journey file not found: {jsonl_path}",
            )
        return jsonl_path, None

    if not journey_dir.exists():
        return None, EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Journey directory not found: {journey_dir}",
        )
    candidates = sorted(journey_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        return None, EvidenceResult(
            passed=False,
            score=0.0,
            note=f"No journey JSONL files found in {journey_dir}",
        )
    return candidates[-1], None


def _load_events(jsonl_path: Path) -> tuple[list[dict[str, Any]], EvidenceResult | None]:
    """Parse JSONL events; return (events, None) or ([], error_result)."""
    events: list[dict[str, Any]] = []
    try:
        for line in jsonl_path.read_text().splitlines():
            stripped = line.strip()
            if stripped:
                events.append(json.loads(stripped))
    except (OSError, json.JSONDecodeError) as exc:
        return [], EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Failed to read journey file {jsonl_path}: {exc}",
        )
    return events, None


def _filter_matched_indices(
    events: list[dict[str, Any]], ev: JourneyEventPresentEvidence
) -> tuple[list[int], EvidenceResult | None]:
    """Return indices of events matching type + optional where predicate."""
    matched: list[int] = []
    for idx, event in enumerate(events):
        if event.get("type") != ev.event:
            continue
        if ev.where is not None:
            try:
                if not _safe_eval_predicate(ev.where, event):
                    continue
            except ValueError as exc:
                return [], EvidenceResult(
                    passed=False,
                    score=0.0,
                    note=f"Predicate parse error in where={ev.where!r}: {exc}",
                )
        matched.append(idx)
    return matched, None


def evaluate_journey_event_present(
    ev: JourneyEventPresentEvidence,
    lab_root: Path,
    run_id: str | None = None,
) -> EvidenceResult:
    """Scan a JSONL journey file and check that a matching event is present.

    Args:
        ev:       A :class:`JourneyEventPresentEvidence` model.
        lab_root: Absolute path to the lab root directory.
        run_id:   Run identifier used to locate ``.forge/journey/<run_id>.jsonl``.
                  If ``None``, the newest ``.jsonl`` file is used.

    Returns:
        :class:`EvidenceResult` -- ``passed=True`` when ``occurrences_min``
        matching events are found (and the optional ``before`` ordering
        constraint is satisfied).
    """
    journey_dir = lab_root / ".forge" / "journey"
    jsonl_path, err = _resolve_jsonl_path(journey_dir, run_id)
    if err is not None:
        return err

    assert jsonl_path is not None  # guaranteed by _resolve_jsonl_path contract
    events, err = _load_events(jsonl_path)
    if err is not None:
        return err

    matched_indices, err = _filter_matched_indices(events, ev)
    if err is not None:
        return err

    # Apply `before` ordering constraint
    if ev.before is not None and matched_indices:
        before_indices = [i for i, e in enumerate(events) if e.get("type") == ev.before]
        if before_indices:
            earliest_before = min(before_indices)
            matched_indices = [i for i in matched_indices if i < earliest_before]

    count = len(matched_indices)
    if count >= ev.occurrences_min:
        return EvidenceResult(
            passed=True,
            score=1.0,
            note=(
                f"Found {count} occurrence(s) of event type {ev.event!r} "
                f"(min required: {ev.occurrences_min})"
            ),
        )

    return EvidenceResult(
        passed=False,
        score=0.0,
        note=(
            f"Found only {count} occurrence(s) of event type {ev.event!r}; "
            f"needed {ev.occurrences_min}"
        ),
    )


# ---------------------------------------------------------------------------
# Primitive-authored evaluator
# ---------------------------------------------------------------------------

#: Adapter files that indicate a specific primitive kind.
_KIND_MARKERS: dict[str, str] = {
    "skill": "SKILL.md",
    "agent": "AGENT.md",
    "hook": "hook.sh",
}


def evaluate_primitive_authored(
    ev: PrimitiveAuthoredEvidence,
    lab_root: Path,
) -> EvidenceResult:
    """Check that at least ``min_count`` primitives exist in ``.forge/local/primitives/``.

    Detection rules:
    - Each sub-directory that contains a ``SPEC.md`` counts as a primitive.
    - ``primitive_name`` (if set) filters by directory-name prefix.
    - ``primitive_kind`` (if set, one of ``skill`` / ``agent`` / ``hook``) further
      requires the presence of the corresponding adapter marker file anywhere
      under the primitive directory.

    Args:
        ev:       A :class:`PrimitiveAuthoredEvidence` model.
        lab_root: Absolute path to the lab root directory.

    Returns:
        :class:`EvidenceResult` -- ``passed=True`` when found count >= ``min_count``.
    """
    primitives_root = lab_root / ".forge" / "local" / "primitives"

    if not primitives_root.exists():
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Primitives directory not found: {primitives_root}",
        )

    matched: list[Path] = []
    for candidate in primitives_root.iterdir():
        if not candidate.is_dir():
            continue
        if not (candidate / "SPEC.md").exists():
            continue
        if ev.primitive_name is not None and not candidate.name.startswith(ev.primitive_name):
            continue
        if ev.primitive_kind is not None:
            kind_result = _check_primitive_kind(candidate, ev.primitive_kind)
            if kind_result is False:
                continue
            if isinstance(kind_result, EvidenceResult):
                return kind_result
        matched.append(candidate)

    count = len(matched)
    min_required = ev.min_count

    if count >= min_required:
        names = ", ".join(sorted(p.name for p in matched))
        return EvidenceResult(
            passed=True,
            score=1.0,
            note=f"Found {count} primitive(s) (required {min_required}): {names}",
        )

    return EvidenceResult(
        passed=False,
        score=0.0,
        note=(
            f"Found only {count} primitive(s) in {primitives_root}; "
            f"needed {min_required}"
            + (f" (name prefix filter: {ev.primitive_name!r})" if ev.primitive_name else "")
            + (f" (kind filter: {ev.primitive_kind!r})" if ev.primitive_kind else "")
        ),
    )


def _check_primitive_kind(candidate: Path, primitive_kind: str) -> bool | EvidenceResult:
    """Return True if kind marker found, False if absent, EvidenceResult if kind is unknown."""
    kind = primitive_kind.lower()
    marker = _KIND_MARKERS.get(kind)
    if marker is None:
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=(
                f"Unknown primitive_kind {primitive_kind!r}; "
                f"expected one of {sorted(_KIND_MARKERS)}"
            ),
        )
    return any(candidate.rglob(marker))


# ---------------------------------------------------------------------------
# LLM-judged evaluator
# ---------------------------------------------------------------------------

#: Maximum characters of input content sent to the LLM.
_LLM_INPUT_MAX_CHARS: int = 4000

#: Expected number of parts after splitting a scoring string like "0-20".
_SCORING_PARTS_COUNT: int = 2


def _parse_scoring_max(scoring: str) -> float:
    """Parse a ``"0-20"``-style scoring string and return the max value.

    Args:
        scoring: A string of the form ``"<min>-<max>"`` (e.g. ``"0-20"``).

    Returns:
        The maximum score as a float.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    parts = scoring.split("-", 1)
    if len(parts) != _SCORING_PARTS_COUNT:
        raise ValueError(f"scoring must be '<min>-<max>', got: {scoring!r}")
    try:
        return float(parts[1])
    except ValueError as exc:
        raise ValueError(f"Could not parse max from scoring={scoring!r}: {exc}") from exc


def _read_llm_file(path: Path, label: str) -> tuple[str | None, EvidenceResult | None]:
    """Read a file for the llm-judged evaluator; return (content, None) or (None, error_result).

    Args:
        path:  Absolute path to the file.
        label: Human-readable label (``"rubric"`` or ``"input"``) for error messages.

    Returns:
        ``(content, None)`` on success; ``(None, EvidenceResult)`` on failure.
    """
    if not path.exists():
        return None, EvidenceResult(
            passed=False,
            score=0.0,
            note=f"{label.capitalize()} file not found: {path}",
        )
    try:
        return path.read_text(), None
    except OSError as exc:
        return None, EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Could not read {label} file {path}: {exc}",
        )


def _call_llm(
    rubric_content: str,
    input_content: str,
    model_logical: str,
    llm_backend: LLMBackend,
) -> tuple[str | None, EvidenceResult | None]:
    """Invoke the LLM backend; return (response_text, None) or (None, error_result)."""
    system_prompt = (
        f"{rubric_content}\n\n"
        "Respond with a JSON object: "
        '{"score": <numeric score>, "rationale": "<brief explanation>"}. '
        "Do not include anything else in your response."
    )
    user_prompt = f"Session artifact to grade:\n\n{input_content}"
    try:
        return (
            llm_backend.complete(
                system=system_prompt,
                user=user_prompt,
                model_logical=model_logical,
            ),
            None,
        )
    except Exception as exc:  # any backend error is surfaced as a non-fatal EvidenceResult
        return None, EvidenceResult(passed=False, score=0.0, note=f"LLM call failed: {exc}")


def _parse_llm_response(response_text: str) -> tuple[float | None, str, EvidenceResult | None]:
    """Parse a JSON LLM response; return (score, rationale, None) or (None, '', error_result)."""
    try:
        data = json.loads(response_text)
        return float(data["score"]), str(data.get("rationale", "")), None
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return (
            None,
            "",
            EvidenceResult(
                passed=False,
                score=0.0,
                note=f"Malformed LLM response (JSON parse error: {exc}): {response_text!r}",
            ),
        )


def _compute_llm_score(scoring: str, raw_score: float, rationale: str) -> EvidenceResult:
    """Validate scoring range and compute the final EvidenceResult for llm-judged.

    Args:
        scoring:   Raw scoring string from the rubric evidence (e.g. ``"0-20"``).
        raw_score: Numeric score extracted from the LLM response.
        rationale: Human-readable rationale from the LLM response.

    Returns:
        :class:`EvidenceResult` — either an error result or the computed grade.
    """
    try:
        scoring_max = _parse_scoring_max(scoring)
    except ValueError as exc:
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Could not parse scoring range {scoring!r}: {exc}",
        )

    if scoring_max <= 0:
        return EvidenceResult(
            passed=False,
            score=0.0,
            note=f"Invalid scoring max={scoring_max}; must be positive",
        )

    return EvidenceResult(
        passed=raw_score >= (scoring_max * 0.5),
        score=raw_score / scoring_max,
        note=rationale,
    )


def evaluate_llm_judged(
    ev: LlmJudgedEvidence,
    lab_root: Path,
    run_id: str | None,
    llm_backend: LLMBackend,
) -> EvidenceResult:
    """Grade an artifact using an LLM with a rubric as the system prompt.

    The evaluator:
    1. Reads the rubric markdown from ``ev.rubric`` (absolute or lab-root-relative path).
    2. Reads the input file from ``ev.input``, substituting ``<run-id>`` with ``run_id``.
    3. Calls ``llm_backend.complete()`` with rubric as system and input content as user.
    4. Parses the JSON response (expects ``{"score": N, "rationale": "..."}``).
    5. Returns ``passed = score >= scoring_max * 0.5``, ``score = score / scoring_max``.

    Args:
        ev:          A :class:`LlmJudgedEvidence` model from the parsed rubric.
        lab_root:    Absolute path to the lab root directory.
        run_id:      Run identifier used to substitute ``<run-id>`` in ``ev.input``.
        llm_backend: Backend that satisfies the :class:`~primitives._llm.LLMBackend` protocol.

    Returns:
        :class:`EvidenceResult` with fractional score and LLM-provided rationale as note.
    """
    # 1. Resolve and read rubric file
    rubric_path = Path(ev.rubric)
    if not rubric_path.is_absolute():
        rubric_path = lab_root / rubric_path
    rubric_content, err = _read_llm_file(rubric_path, "rubric")
    if err is not None:
        return err

    # 2. Resolve and read input file (substitute <run-id>)
    raw_input = ev.input if run_id is None else ev.input.replace("<run-id>", run_id)
    input_path = Path(raw_input)
    if not input_path.is_absolute():
        input_path = lab_root / input_path
    input_content_full, err = _read_llm_file(input_path, "input")
    if err is not None:
        return err

    assert rubric_content is not None  # guaranteed above
    assert input_content_full is not None
    input_content = input_content_full[:_LLM_INPUT_MAX_CHARS]

    # 3. Call LLM
    response_text, err = _call_llm(rubric_content, input_content, ev.model_logical, llm_backend)
    if err is not None:
        return err

    assert response_text is not None

    # 4. Parse response
    raw_score, rationale, err = _parse_llm_response(response_text)
    if err is not None:
        return err

    assert raw_score is not None

    # 5. Compute result
    scoring_result = _compute_llm_score(ev.scoring, raw_score, rationale)
    return scoring_result


# ---------------------------------------------------------------------------
# Compound (AND / OR) evaluator
# ---------------------------------------------------------------------------


def evaluate_compound(
    ev: CompoundEvidence,
    lab_root: Path,
    run_id: str | None = None,
    llm_backend: LLMBackend | None = None,
) -> EvidenceResult:
    """Recursively evaluate compound AND/OR evidence nodes.

    AND semantics:
    - ``passed`` = all children passed
    - ``score``  = min child score (partial credit only if all passed)

    OR semantics:
    - ``passed`` = any child passed
    - ``score``  = max child score

    Args:
        ev:          A :class:`CompoundEvidence` model.
        lab_root:    Absolute path to the lab root directory.
        run_id:      Run identifier forwarded to child evaluators that need it.
        llm_backend: Backend forwarded to ``llm-judged`` child evaluators.

    Returns:
        :class:`EvidenceResult` aggregating child results per the op.
    """
    child_results: list[EvidenceResult] = [
        evaluate(child, lab_root=lab_root, run_id=run_id, llm_backend=llm_backend)
        for child in ev.children
    ]

    scores = [r.score for r in child_results]
    passed_flags = [r.passed for r in child_results]

    child_summary = "; ".join(
        f"child[{i}]={'PASS' if r.passed else 'FAIL'}({r.score:.2f}): {r.note[:60]}"
        for i, r in enumerate(child_results)
    )

    if ev.op == "AND":
        overall_passed = all(passed_flags)
        overall_score = min(scores) if overall_passed else 0.0
        return EvidenceResult(
            passed=overall_passed,
            score=overall_score,
            note=f"AND({len(child_results)} children): {child_summary}",
        )

    # OR
    overall_passed = any(passed_flags)
    overall_score = max(scores)
    return EvidenceResult(
        passed=overall_passed,
        score=overall_score,
        note=f"OR({len(child_results)} children): {child_summary}",
    )


# ---------------------------------------------------------------------------
# Single-dispatch evaluate() — maps evidence type to evaluator
# ---------------------------------------------------------------------------


def _evaluate_simple(
    ev: EvidenceUnion, lab_root: Path, run_id: str | None
) -> EvidenceResult | None:
    """Dispatch simple (non-LLM, non-compound) evidence types. Returns None on miss."""
    if isinstance(ev, ShellEvidence):
        return evaluate_shell(ev, lab_root)
    if isinstance(ev, FileExistsEvidence):
        return evaluate_file_exists(ev, lab_root)
    if isinstance(ev, FailureModeCleanEvidence):
        return evaluate_failure_mode_clean(ev, lab_root)
    if isinstance(ev, JourneyEventPresentEvidence):
        return evaluate_journey_event_present(ev, lab_root, run_id=run_id)
    if isinstance(ev, PrimitiveAuthoredEvidence):
        return evaluate_primitive_authored(ev, lab_root)
    return None


def evaluate(
    ev: EvidenceUnion,
    *,
    lab_root: Path,
    run_id: str | None = None,
    llm_backend: LLMBackend | None = None,
) -> EvidenceResult:
    """Dispatch an evidence node to its evaluator.

    Args:
        ev:          Any evidence model from the rubric DSL.
        lab_root:    Absolute path to the lab root directory.
        run_id:      Run identifier (required by journey-event-present, llm-judged, compound).
        llm_backend: LLM backend (required by llm-judged and compound with llm-judged children).

    Returns:
        :class:`EvidenceResult` from the appropriate evaluator.

    Raises:
        TypeError: if ``llm_backend`` is None and an llm-judged evaluator is reached.
    """
    simple = _evaluate_simple(ev, lab_root, run_id)
    if simple is not None:
        return simple
    if isinstance(ev, LlmJudgedEvidence):
        if llm_backend is None:
            raise TypeError("llm_backend must be provided for llm-judged evidence")
        return evaluate_llm_judged(ev, lab_root, run_id=run_id, llm_backend=llm_backend)
    if isinstance(ev, CompoundEvidence):
        return evaluate_compound(ev, lab_root, run_id=run_id, llm_backend=llm_backend)
    # Exhaustive — Pydantic discriminated union guarantees no other types
    raise TypeError(f"Unknown evidence type: {type(ev).__name__}")
