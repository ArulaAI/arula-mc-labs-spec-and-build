#!/usr/bin/env python3
"""
Lab-local PreToolUse guard: the PR artifact cannot be written while a required gate is red.

Lab 2's "PR" is a local file — `boost-authentication-service/docs/PR_DESCRIPTION.md`. No
`gh pr create` runs anywhere in this lab, so the control is a path-based Write guard on that
file (the same shape as `reference_guard.py`).

Required gates, all of which must be green before the write is allowed:

  1. `mvn -B verify` green in `boost-authentication-service` (tests + ArchUnit + JaCoCo)
  2. `mvn -B verify` green in `boost-order-processing` (tests incl. the contract test)
  3. no PAN / CAVV / secret in the service log sinks

WORKBENCH ISSUE L2-2: the shared Workbench has no PR-gate guard. This is the lab-local
mitigation; it should be promoted into the plugin.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PR_ARTIFACT = "docs/PR_DESCRIPTION.md"
REPOS = ("boost-authentication-service", "boost-order-processing")
LOG_SINKS = (
    "boost-authentication-service/logs/auth-service.log",
    "boost-order-processing/logs/order-processing.log",
)
PAN_PATTERN = re.compile(
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
)
CAVV_PATTERN = re.compile(r"\bcavv=[A-Za-z0-9+/=]{8,}|authenticationValue=[A-Za-z0-9+/=]{8,}")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def workspace_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))


def maven_verify(repo: Path) -> tuple[bool, str]:
    if not (repo / "pom.xml").exists():
        return False, f"{repo} is not a Maven repo — gate cannot be evaluated"
    result = subprocess.run(
        ["mvn", "-B", "-q", "verify"],
        cwd=repo, capture_output=True, text=True,
    )
    if result.returncode == 0:
        return True, ""
    tail = (result.stdout + result.stderr).strip().splitlines()[-12:]
    return False, "\n".join(tail)


def scan_logs(root: Path) -> list[str]:
    findings = []
    for sink in LOG_SINKS:
        path = root / sink
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        if PAN_PATTERN.search(text) or CAVV_PATTERN.search(text):
            findings.append(sink)
    return findings


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = event.get("tool_input") or {}
    target = str(tool_input.get("file_path") or tool_input.get("path") or "")
    if not target.replace("\\", "/").endswith(PR_ARTIFACT):
        sys.exit(0)

    root = workspace_root()
    failures = []

    for repo in REPOS:
        ok, tail = maven_verify(root / repo)
        if not ok:
            failures.append(f"- `mvn verify` RED in {repo}:\n{tail}")

    leaking = scan_logs(root)
    if leaking:
        failures.append(
            "- sensitive-data scan RED: PAN or authentication value found in "
            + ", ".join(leaking)
        )

    if failures:
        deny(
            "PR gate: the PR description cannot be written while a required gate is red.\n\n"
            + "\n".join(failures)
            + "\n\nClose the gates, then write the PR description again."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
