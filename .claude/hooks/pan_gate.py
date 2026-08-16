#!/usr/bin/env python3
"""
Lab-local PreToolUse guard: block a write that would add a PAN or a secret.

WORKBENCH ISSUE L2-9 (mitigation). The plugin's PAN/secret gate (`quality_gates.py`) scans
`git diff HEAD` in Claude Code's working directory. In this lab that directory is the
*workspace* root, while the Java code lives in two independent git repos beneath it — so the
plugin gate never sees an edit to either service and silently reports "skip" for the whole
session. This guard restores the control by scanning the pending write itself, which is
strictly earlier than a diff-based scan.

Patterns are the same ones the plugin uses (`references/pan-patterns.txt`).
"""
import json
import re
import sys

PAN_PATTERNS = [
    re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}"
        r"|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}"
        r"|(?:2131|1800|35\d{3})\d{11})\b"
    ),
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    re.compile(r";[0-9]{13,19}=[0-9]{4}[0-9]*\?"),
]
SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|api_key|apikey|token)\s*[=:]\s*[\"']?\S{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}"),
]
CONTENT_KEYS = ("content", "new_string", "new_str")


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
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = event.get("tool_input") or {}
    pending = "\n".join(str(tool_input[k]) for k in CONTENT_KEYS if tool_input.get(k))
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and edit.get("new_string"):
            pending += "\n" + str(edit["new_string"])
    if not pending:
        sys.exit(0)

    for pattern in PAN_PATTERNS:
        if pattern.search(pending):
            deny(
                "Payments guardrail: this write adds something that matches a PAN pattern. "
                "Cardholder data never goes into source, tests, fixtures, logs or docs. "
                "Use a placeholder, or read the value from the existing fixture instead of "
                "restating it."
            )
    for pattern in SECRET_PATTERNS:
        if pattern.search(pending):
            deny(
                "Payments guardrail: this write adds something that matches a credential or "
                "token pattern. Secrets are read from the platform secret store at runtime, "
                "never committed."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
