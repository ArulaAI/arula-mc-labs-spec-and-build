"""U4 journey-curator — structured-prompt LLM call that writes journey.md.

Public API::

    from primitives.journey_curator.shared.curator import curate

    path = curate(lab_root=Path("."), run_id="run_abc123", llm_backend=backend)
    # path -> Path(".forge/journey/run_abc123/journey.md")

The curator:

1. Reads ``.forge/journey/<run-id>.jsonl`` (each line is one event).
2. Optionally reads ``.forge/journey/<run-id>/grade.json`` if present (U2 output).
3. Builds a structured 8-section system prompt.
4. Builds a user message from the JSONL content + optional grade summary,
   prefixed with the lab_slug context, truncated to 6000 chars.
5. Calls ``llm_backend.complete(system=..., user=..., model_logical="default")``.
6. Writes the LLM response to ``.forge/journey/<run-id>/journey.md``.
7. Appends a ``journey_curator_run`` event to the JSONL.
8. Returns the path to ``journey.md``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
import uuid
from pathlib import Path

from primitives._llm import LLMBackend, get_backend

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

CURATOR_SYSTEM_PROMPT = """
You are a learning coach reviewing an AI-native engineering lab session.
Analyze the journey events and produce a concise student artifact in Markdown.
Your output MUST be valid Markdown covering these 8 sections in order:

1. Session Timeline (chronological event summary)
2. Primitives Used (by layer: L1 native / L2 Forge / L3 per-lab)
3. Workflows Attempted (map to W1-W15 from the curriculum)
4. Failure Modes Encountered (any FM1-FM5 findings from events)
5. Golden Prompts (prompts that produced the highest-quality results)
6. Stuck Points (where the session stalled or backtracked)
7. Harness Comparison (what worked differently in Claude Code vs Copilot stats)
8. What to Try Next (3-5 concrete next actions)

Be concise. Students keep this artifact. Coaches read it.
""".strip()

# Maximum combined character length of JSONL + grade content passed to LLM.
_MAX_USER_CONTENT_CHARS = 6000


# ---------------------------------------------------------------------------
# curate()
# ---------------------------------------------------------------------------


def curate(
    lab_root: Path,
    run_id: str,
    llm_backend: LLMBackend,
) -> Path:
    """Synthesise a ``journey.md`` student artifact from journey events.

    Args:
        lab_root:    Root directory of the lab (must contain ``.forge/``).
        run_id:      Session run identifier — determines which JSONL to read.
        llm_backend: LLM backend instance (``BedrockBackend`` or ``MockBackend``).

    Returns:
        Path to the written ``journey.md`` file.

    Raises:
        FileNotFoundError: If the JSONL for ``run_id`` does not exist.
    """
    start_ms = int(time.monotonic() * 1000)

    journey_dir = lab_root / ".forge" / "journey"
    jsonl_path = journey_dir / f"{run_id}.jsonl"

    if not jsonl_path.exists():
        raise FileNotFoundError(
            f"Journey JSONL not found: {jsonl_path}. Run a session with U3 journey-recorder first."
        )

    # ------------------------------------------------------------------
    # 1. Read the JSONL events
    # ------------------------------------------------------------------
    raw_jsonl = jsonl_path.read_text(encoding="utf-8")
    events = []
    for raw_line in raw_jsonl.splitlines():
        stripped = raw_line.strip()
        if stripped:
            try:
                events.append(json.loads(stripped))
            except json.JSONDecodeError:
                pass  # skip malformed lines silently

    # Extract lab_slug from first event for context
    lab_slug: str = "unknown-lab"
    if events:
        lab_slug = str(events[0].get("lab_slug") or "unknown-lab")

    # ------------------------------------------------------------------
    # 2. Optionally read grade.json
    # ------------------------------------------------------------------
    grade_summary: str = ""
    grade_path = journey_dir / run_id / "grade.json"
    if grade_path.exists():
        try:
            grade_data: object = json.loads(grade_path.read_text(encoding="utf-8"))
            if isinstance(grade_data, dict):
                pct = grade_data.get("percentage", "n/a")
                total = grade_data.get("total_score", "n/a")
                max_score = grade_data.get("max_score", "n/a")
                grade_summary = (
                    f"\n\n--- Grade Summary ---\nScore: {total}/{max_score} ({pct:.1f}%)\n"
                    if isinstance(pct, (int, float))
                    else f"\n\n--- Grade Summary ---\n{json.dumps(grade_data, indent=2)[:500]}\n"
                )
        except (json.JSONDecodeError, OSError):
            grade_summary = ""

    # ------------------------------------------------------------------
    # 3. Build user message — truncate to _MAX_USER_CONTENT_CHARS
    # ------------------------------------------------------------------
    prefix = f"Lab: {lab_slug}\nRun ID: {run_id}\n\n--- Journey Events (JSONL) ---\n"
    combined = prefix + raw_jsonl + grade_summary
    if len(combined) > _MAX_USER_CONTENT_CHARS:
        combined = combined[:_MAX_USER_CONTENT_CHARS]

    user_message = combined

    # ------------------------------------------------------------------
    # 4. Call the LLM
    # ------------------------------------------------------------------
    markdown_content = llm_backend.complete(
        system=CURATOR_SYSTEM_PROMPT,
        user=user_message,
        model_logical="default",
    )

    # ------------------------------------------------------------------
    # 5. Write journey.md
    # ------------------------------------------------------------------
    run_dir = journey_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    journey_md_path = run_dir / "journey.md"
    journey_md_path.write_text(markdown_content, encoding="utf-8")

    # ------------------------------------------------------------------
    # 6. Emit journey_curator_run event
    # ------------------------------------------------------------------
    duration_ms = int(time.monotonic() * 1000) - start_ms
    event: dict[str, object] = {
        "event_id": f"evt_{uuid.uuid4().hex[:20]}",
        "run_id": run_id,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "type": "journey_curator_run",
        "harness": "curator",
        "journey_md_lines": len(markdown_content.splitlines()),
        "duration_ms": duration_ms,
    }
    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")

    # ------------------------------------------------------------------
    # 7. Return path
    # ------------------------------------------------------------------
    return journey_md_path


# ---------------------------------------------------------------------------
# CLI entry-point (for adapter invoke.sh)
# ---------------------------------------------------------------------------


def _main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="U4 journey-curator: synthesise a journey.md student artifact."
    )
    parser.add_argument("--run-id", required=True, help="Session run identifier")
    parser.add_argument(
        "--lab-root",
        default=".",
        help="Path to lab root (default: current directory)",
    )
    args = parser.parse_args()

    lab_root = Path(args.lab_root).resolve()
    backend = get_backend()
    output = curate(lab_root=lab_root, run_id=args.run_id, llm_backend=backend)
    print(f"journey.md written to: {output}")


if __name__ == "__main__":  # pragma: no cover
    _main()
