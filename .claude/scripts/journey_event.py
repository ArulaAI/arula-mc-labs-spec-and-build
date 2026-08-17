#!/usr/bin/env python3
"""
Append a lab-local event to the journey.

The Workbench plugin records tool events automatically, but a stage boundary is not a tool
event — nothing in the automatic stream says "Stage 3 closed". `/hand-off` calls this so the
seven stage boundaries are deterministic, gradeable evidence rather than prose in a tracker file.

Usage:
  python3 .claude/scripts/journey_event.py hand-off --stage 3 --name "Plan: spec to issues"

Runnable from anywhere in the workspace: the workspace root is resolved from `.claude/lab.json`,
so a hand-off recorded while the shell happens to sit inside one of the owned repos still lands
in the single workspace-root journey the grader reads.
"""
import argparse
import json
import os
import time
from pathlib import Path


def workspace_root() -> Path:
    """The directory holding `.claude/lab.json` — the Claude Code project root for this lab."""
    explicit = os.environ.get("CLAUDE_PROJECT_DIR")
    if explicit and (Path(explicit) / ".claude" / "lab.json").exists():
        return Path(explicit)
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / ".claude" / "lab.json").exists():
            return candidate
    # Last resort: this script lives at <root>/.claude/scripts/journey_event.py
    return Path(__file__).resolve().parents[2]


def journey_dir() -> Path:
    override = os.environ.get("WORKBENCH_JOURNEY_DIR")
    return Path(override) if override else workspace_root() / "journey"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", help="event type, e.g. hand-off")
    parser.add_argument("--stage", type=int, required=False)
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    session = os.environ.get("CLAUDE_SESSION_ID", "lab2-local")
    target = journey_dir()
    target.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": int(time.time()),
        "event": args.event,
        "session": session,
        "lab": 2,
    }
    if args.stage is not None:
        event["stage"] = args.stage
    if args.name:
        event["stage_name"] = args.name

    with (target / f"{session}.jsonl").open("a") as handle:
        handle.write(json.dumps(event) + "\n")

    print(json.dumps({"recorded": event, "journey": str(target)}))


if __name__ == "__main__":
    main()
