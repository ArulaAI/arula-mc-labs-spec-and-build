---
name: failure-mode-audit
description: Scan a directory or file for the 5 AI Failure Modes. Returns structured findings with severity. Available to coding agent + CLI + chat.
tools:
  - shell
---

# Skill: failure-mode-audit

Scan code for AI Failure Modes (Hallucinated Dependencies, Context-Window Blindness, Training-Data Bias, Overconfident Completions, Security Vulnerability Propagation).

## How to invoke

Run from repo root:

```bash
python .forge/primitives/failure_mode_audit/shared/auditor.py <path> --format json
```

Or use the slash command `/failure-mode-audit <path>` from `prompts/failure-mode-audit.prompt.md`.

## Output

JSON list of findings: `{mode, severity, file, line, message, snippet}`.

Severity ordering: `low < medium < high < critical`.

## When to use

- Before opening a PR — audit the diff
- In code review — audit changed files
- As a hook (`.github/hooks/failure-mode-audit.json` `PreToolUse`) — audit before write tool fires
- In CI when budget allows (`.github/workflows/audit.yml` is dormant `workflow_dispatch:` until then)

## Invariants

- Wraps `.forge/primitives/failure_mode_audit/shared/auditor.py` — DO NOT duplicate logic
- Updates land via `forge sync` per the lab's `.forge/manifest.yaml` pin
