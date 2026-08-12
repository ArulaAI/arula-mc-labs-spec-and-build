---
name: failure-mode-audit
description: Scan a directory or file for the 5 AI Failure Modes (Hallucinated Dependencies, Context-Window Blindness, Training-Data Bias, Overconfident Completions, Security Vulnerability Propagation). Returns structured findings with severity. Use before commits, in PR review, in lab grader rubrics, or as a hook on PreToolUse.
---

# /failure-mode-audit

Claude Code adapter for the Forge primitive library U1 primitive.

## When invoked

1. Determine the audit target — user-mentioned path, else `.`
2. Determine the failure modes — default `fm1,fm3,fm4,fm5` (FM2 deferred to Plan 2 LLM path)
3. Run: `bash <skill_dir>/invoke.sh <path> [--modes <list>] [--max-severity <level>]`
4. Parse output. On exit code 1, surface findings as structured action items.

## Output expectations

- Always emit a structured findings list (severity + file:line + message)
- For critical (e.g. hardcoded secrets), make user STOP and address before proceeding
- For medium/low, surface as opportunities

## Invariants

- Logic lives in `primitives/failure_mode_audit/shared/auditor.py` in the Forge primitive library
- DO NOT modify `invoke.sh` or duplicate auditor logic — primitive library upgrades flow through `forge sync`
