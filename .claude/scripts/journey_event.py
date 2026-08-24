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


def resolve_session_id() -> str:
    """The real session id, resolved the same way the plugin's hook-driven journey writer
    sees it — so a hand-off lands in the same file as the tool-call events instead of a
    separate `lab2-local.jsonl` the grader can't reconcile with the real session.

    `CLAUDE_SESSION_ID` is only exported into hook subprocesses, never into a plain
    `Bash` invocation like this one, so it is almost never set here. By the time any
    `/hand-off` runs, Stage 0's `/lab` has already caused the hook to write tool events
    under the real session id, so that file already exists and is the most recently
    modified one in the journey directory.
    """
    env_session = os.environ.get("CLAUDE_SESSION_ID")
    if env_session:
        return env_session
    existing = sorted(
        journey_dir().glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return existing[0].stem if existing else "lab2-local"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", help="event type, e.g. hand-off")
    parser.add_argument("--stage", type=int, required=False)
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    session = resolve_session_id()
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
