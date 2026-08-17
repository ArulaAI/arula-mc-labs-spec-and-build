#!/usr/bin/env python3
"""
Lab-local PreToolUse guard: protect the answer material under .claude/reference/.

Denies Read/Edit/Write/Bash access to anything under the workspace `.claude/reference/`
directory unless the facilitator has set WORKBENCH_FACILITATOR=1.

`docs/FACILITATOR_KEY.md` is guarded by the same rule. The key itself lives under
`.claude/reference/`; the file at the documented path is a pointer stub, and guarding it keeps
an agent that lists `docs/` from wandering into facilitator material.

Hook contract: event JSON arrives on stdin; a permission decision is returned on stdout.
"""
import json
import os
import sys

GUARDED = (".claude/reference", "docs/FACILITATOR_KEY.md")
PATH_KEYS = ("file_path", "path", "notebook_path", "filePath")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main() -> None:
    if os.environ.get("WORKBENCH_FACILITATOR") == "1":
        sys.exit(0)

    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = event.get("tool_input") or {}
    targets = [str(tool_input[k]) for k in PATH_KEYS if tool_input.get(k)]
    command = str(tool_input.get("command", ""))
    if command:
        targets.append(command)
    targets.extend(str(p) for p in (tool_input.get("paths") or []))

    for target in targets:
        normalized = target.replace("\\", "/")
        if any(guarded in normalized for guarded in GUARDED):
            deny(
                "Lab 2 reference guard: this path holds the facilitator answer material for "
                "the lab (facilitator key, completed spec, TDD tests, corrected implementation, "
                "expected validator output). It is not readable or writable during a session. "
                "If you are stuck, ask the facilitator to restore the stage you need."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
