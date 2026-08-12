"""grade() orchestrator for the U2 lab-grader primitive (Plan 2 Task 10).

Reads the rubric YAML, evaluates each criterion, computes a weighted total
score, writes ``grade.json``, and emits a ``lab_grader_run`` journey event.

Usage (module-level entry-point for adapters)::

    grade(lab_root, run_id="run-abc", llm_backend=BedrockBackend())

or via the CLI adapter::

    python -m primitives.lab_grader.shared.grader <lab_root> --run-id <id>
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from primitives._llm import LLMBackend, get_backend
from primitives.lab_grader.shared.evaluators import EvidenceResult, evaluate
from primitives.lab_grader.shared.parser import parse_rubric

# ---------------------------------------------------------------------------
# GradeResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class GradeResult:
    """Outcome of grading an entire rubric against a lab snapshot.

    Attributes:
        total_score:     Weighted sum of (weight * ev_result.score) for all criteria.
        max_score:       Sum of all criterion weights (used to compute percentage).
        percentage:      ``total_score / max_score * 100`` (0-100 scale).
        criteria_results: List of ``(criterion_id, EvidenceResult)`` pairs in rubric order.
        run_id:          The run identifier used for this grading session.
    """

    total_score: float
    max_score: float
    percentage: float
    criteria_results: list[tuple[str, EvidenceResult]] = field(default_factory=list)
    run_id: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _append_event(lab_root: Path, run_id: str, event: dict[str, object]) -> None:
    """Append a single JSON event to ``.forge/journey/<run_id>.jsonl``.

    Creates the directory if it does not exist.

    Args:
        lab_root: Absolute path to the lab root.
        run_id:   Run identifier used as the JSONL filename stem.
        event:    Mapping that will be serialised as a single JSONL line.
    """
    journey_dir = lab_root / ".forge" / "journey"
    journey_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = journey_dir / f"{run_id}.jsonl"
    with jsonl_path.open("a") as fh:
        fh.write(json.dumps(event) + "\n")


def _write_grade_json(lab_root: Path, run_id: str, result: GradeResult) -> None:
    """Write ``grade.json`` to ``.forge/journey/<run_id>/grade.json``.

    Args:
        lab_root: Absolute path to the lab root.
        run_id:   Run identifier used to locate the output directory.
        result:   The :class:`GradeResult` to serialise.
    """
    out_dir = lab_root / ".forge" / "journey" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    grade_data = {
        "run_id": result.run_id,
        "total_score": result.total_score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "criteria": [
            {
                "id": cid,
                "passed": ev_result.passed,
                "score": ev_result.score,
                "note": ev_result.note,
            }
            for cid, ev_result in result.criteria_results
        ],
    }
    (out_dir / "grade.json").write_text(json.dumps(grade_data, indent=2))


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def grade(
    lab_root: Path,
    run_id: str,
    llm_backend: LLMBackend,
    rubric_path: Path | None = None,
) -> GradeResult:
    """Grade a lab snapshot against its rubric.

    Steps:
    1. Locate and parse the rubric YAML (default: ``lab_root/.forge/grader.yaml``).
    2. Evaluate each criterion using :func:`~.evaluators.evaluate`.
    3. Aggregate weighted scores: ``total = sum(weight * score)`` across all criteria.
    4. Write ``grade.json`` to ``lab_root/.forge/journey/<run_id>/grade.json``.
    5. Append a ``lab_grader_run`` event to ``lab_root/.forge/journey/<run_id>.jsonl``.

    Args:
        lab_root:    Absolute path to the lab root directory.
        run_id:      Run identifier for the grading session (used for artifacts).
        llm_backend: LLM backend for ``llm-judged`` criteria.
        rubric_path: Override path to the grader YAML (default: ``<lab_root>/.forge/grader.yaml``).

    Returns:
        :class:`GradeResult` with total/max/percentage and per-criterion outcomes.
    """
    if rubric_path is None:
        rubric_path = lab_root / ".forge" / "grader.yaml"

    rubric = parse_rubric(rubric_path)

    criteria_results: list[tuple[str, EvidenceResult]] = []
    total_score: float = 0.0
    max_score: float = 0.0

    for criterion in rubric.criteria:
        ev_result = evaluate(
            criterion.evidence,
            lab_root=lab_root,
            run_id=run_id,
            llm_backend=llm_backend,
        )
        weighted = criterion.weight * ev_result.score
        total_score += weighted
        max_score += criterion.weight
        criteria_results.append((criterion.id, ev_result))

    percentage = (total_score / max_score * 100.0) if max_score > 0 else 0.0

    result = GradeResult(
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        criteria_results=criteria_results,
        run_id=run_id,
    )

    # Write grade.json artifact
    _write_grade_json(lab_root, run_id, result)

    # Emit lab_grader_run journey event
    passed_count = sum(1 for _, r in criteria_results if r.passed)
    _append_event(
        lab_root,
        run_id,
        {
            "event_id": f"evt_{uuid.uuid4().hex[:20]}",
            "run_id": run_id,
            "type": "lab_grader_run",
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "criteria_count": len(criteria_results),
            "criteria_passed": passed_count,
        },
    )

    return result


# ---------------------------------------------------------------------------
# CLI entry-point (used by adapters/claude_code/invoke.sh)
# ---------------------------------------------------------------------------


def _cli() -> None:
    """Minimal CLI: ``python -m primitives.lab_grader.shared.grader <lab_root> [opts]``."""
    parser = argparse.ArgumentParser(description="Grade a lab using its .forge/grader.yaml rubric")
    parser.add_argument("lab_root", type=Path, help="Path to the lab root directory")
    parser.add_argument("--run-id", default=None, help="Run ID (generated if omitted)")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    lab_root: Path = args.lab_root.resolve()
    run_id: str = args.run_id or f"run_{uuid.uuid4().hex[:20]}"

    backend = get_backend()
    result = grade(lab_root, run_id=run_id, llm_backend=backend)

    if args.format in ("json", "both"):
        output = {
            "run_id": result.run_id,
            "total_score": result.total_score,
            "max_score": result.max_score,
            "percentage": result.percentage,
            "criteria": [
                {
                    "id": cid,
                    "passed": r.passed,
                    "score": r.score,
                    "note": r.note,
                }
                for cid, r in result.criteria_results
            ],
        }
        print(json.dumps(output, indent=2))

    if args.format in ("markdown", "both"):
        score_line = f"{result.percentage:.1f}% ({result.total_score:.1f} / {result.max_score:.1f})"
        lines = [
            f"# Grade Report — {lab_root.name}",
            "",
            f"**Run ID:** `{result.run_id}`  ",
            f"**Score:** {score_line}",
            "",
            "## Criteria",
            "",
            "| ID | Passed | Score | Note |",
            "|---|---|---|---|",
        ]
        for cid, r in result.criteria_results:
            status = "✓" if r.passed else "✗"
            lines.append(f"| {cid} | {status} | {r.score:.2f} | {r.note[:80]} |")
        print("\n".join(lines))

    sys.exit(0)


if __name__ == "__main__":
    _cli()
