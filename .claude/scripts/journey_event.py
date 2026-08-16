#!/usr/bin/env python3
"""
Append a lab-local event to the journey.

The Workbench plugin records tool events automatically, but a stage boundary is not a tool
event — nothing in the automatic stream says "Stage 3 closed". `/hand-off` calls this so the
seven stage boundaries are deterministic, gradeable evidence rather than prose in a tracker file.

Usage:
  python3 .claude/scripts/journey_event.py hand-off --stage 3 --name "Plan: spec to issues"
"""
import argparse
import json
import os
import time
from pathlib import Path

JOURNEY_DIR = Path(os.environ.get("WORKBENCH_JOURNEY_DIR", "journey"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", help="event type, e.g. hand-off")
    parser.add_argument("--stage", type=int, required=False)
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    session = os.environ.get("CLAUDE_SESSION_ID", "lab2-local")
    JOURNEY_DIR.mkdir(parents=True, exist_ok=True)
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

    with (JOURNEY_DIR / f"{session}.jsonl").open("a") as handle:
        handle.write(json.dumps(event) + "\n")

    print(json.dumps({"recorded": event}))


if __name__ == "__main__":
    main()
