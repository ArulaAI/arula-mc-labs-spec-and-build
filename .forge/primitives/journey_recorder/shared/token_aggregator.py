"""token_aggregator.py — aggregate token usage from journey JSONL files.

Reads .forge/journey/<run-id>.jsonl, collects token_usage fields from each
event, and produces a structured report with totals, per-model breakdown,
and per-tool breakdown.

Usage (CLI):
    python -m primitives.journey_recorder.shared.token_aggregator \\
        /path/to/lab --run-id run_abc123 [--write]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Engineer resolution
# ---------------------------------------------------------------------------


def _get_engineer() -> str:
    """Resolve the current engineer identity.

    Resolution order:
    1. FORGE_USER_ID environment variable
    2. ``git config user.email``
    3. Literal string ``"unknown"``
    """
    env_val = os.environ.get("FORGE_USER_ID", "").strip()
    if env_val:
        return env_val

    try:
        git_exe = subprocess.run(
            ["git", "config", "user.email"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if git_exe.returncode == 0:
            email = git_exe.stdout.strip()
            if email:
                return email
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "unknown"


# ---------------------------------------------------------------------------
# Core aggregation helpers
# ---------------------------------------------------------------------------


def _process_event(
    event: dict[str, Any],
    totals: dict[str, Any],
    by_model: dict[str, dict[str, Any]],
    by_tool: dict[str, dict[str, Any]],
) -> None:
    """Update running totals / breakdowns from a single *event* dict."""
    usage = event.get("token_usage")
    if not isinstance(usage, dict):
        return

    inp = int(usage.get("input_tokens", 0))
    out = int(usage.get("output_tokens", 0))
    cache_r = int(usage.get("cache_read_tokens", 0))
    cache_w = int(usage.get("cache_write_tokens", 0))
    cost = float(usage.get("cost_usd", 0.0))
    model = str(usage.get("model", "unknown"))
    tool_name_raw = event.get("tool_name")
    tool_name: str | None = str(tool_name_raw) if tool_name_raw else None

    totals["input_tokens"] += inp
    totals["output_tokens"] += out
    totals["cache_read_tokens"] += cache_r
    totals["cache_write_tokens"] += cache_w
    totals["estimated_cost_usd"] += cost

    if model not in by_model:
        by_model[model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
    by_model[model]["input_tokens"] += inp
    by_model[model]["output_tokens"] += out
    by_model[model]["calls"] += 1

    if tool_name:
        if tool_name not in by_tool:
            by_tool[tool_name] = {"calls": 0, "total_tokens": 0}
        by_tool[tool_name]["calls"] += 1
        by_tool[tool_name]["total_tokens"] += inp + out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def aggregate_tokens(*, lab_root: Path, run_id: str) -> dict[str, Any]:
    """Read .forge/journey/<run-id>.jsonl and return an aggregated token report.

    Parameters
    ----------
    lab_root:
        Root directory of the lab (the directory that contains ``.forge/``).
    run_id:
        The run identifier.  The JSONL file is expected at
        ``<lab_root>/.forge/journey/<run_id>.jsonl``.

    Returns
    -------
    dict with keys:
        session_id, engineer, timestamp_start, timestamp_end,
        totals, by_model, by_tool

    Raises
    ------
    FileNotFoundError
        When the JSONL file for *run_id* does not exist.
    """
    jsonl_path = lab_root / ".forge" / "journey" / f"{run_id}.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Journey file not found: {jsonl_path}")

    totals: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    by_model: dict[str, dict[str, Any]] = {}
    by_tool: dict[str, dict[str, Any]] = {}

    timestamp_start: str | None = None
    timestamp_end: str | None = None
    session_id: str = run_id

    for raw_line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        try:
            event: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed lines (e.g. truncated writes)

        ts = event.get("timestamp")
        if ts:
            if timestamp_start is None:
                timestamp_start = str(ts)
            timestamp_end = str(ts)

        if session_id == run_id and event.get("run_id"):
            session_id = str(event["run_id"])

        _process_event(event, totals, by_model, by_tool)

    return {
        "session_id": session_id,
        "engineer": _get_engineer(),
        "timestamp_start": timestamp_start or "",
        "timestamp_end": timestamp_end or "",
        "totals": totals,
        "by_model": by_model,
        "by_tool": by_tool,
    }


def write_token_report(*, lab_root: Path, report: dict[str, Any]) -> Path:
    """Write *report* to .forge/token-usage/<session-id>.json.

    Parameters
    ----------
    lab_root:
        Root directory of the lab.
    report:
        The dict returned by :func:`aggregate_tokens`.

    Returns
    -------
    Path to the written JSON file.
    """
    session_id = report["session_id"]
    out_dir = lab_root / ".forge" / "token-usage"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{session_id}.json"
    out_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for the token aggregator.

    Usage::

        python -m primitives.journey_recorder.shared.token_aggregator \\
            <lab_root> --run-id <run_id> [--write]
    """
    parser = argparse.ArgumentParser(
        description="Aggregate token usage from a journey JSONL file.",
        prog="token_aggregator",
    )
    parser.add_argument(
        "lab_root",
        type=Path,
        help="Path to the lab root directory (contains .forge/).",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run ID whose JSONL file should be aggregated.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write the report to .forge/token-usage/<session-id>.json.",
    )

    args = parser.parse_args(argv)
    report = aggregate_tokens(lab_root=args.lab_root, run_id=args.run_id)

    if args.write:
        out_path = write_token_report(lab_root=args.lab_root, report=report)
        print(f"Report written to: {out_path}", file=sys.stderr)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
