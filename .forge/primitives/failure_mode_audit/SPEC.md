# U1: /failure-mode-audit — Forge primitive contract

## Purpose

Scan a diff or directory for the 5 AI Failure Modes. Emit structured findings.

## Layer

L2 Universal (every modernized Forge lab MUST ship this primitive — see Project 2 §4.2).

## Inputs

- `path` (positional) — directory or file to audit. Default: current working directory.
- `--diff` (optional) — limit scan to lines added/modified vs `HEAD` (uses `git diff`).
- `--modes` (optional, comma-separated) — restrict to specific failure modes (`fm1`, `fm2`, `fm3`, `fm4`, `fm5`). Default: all 5.
- `--max-severity` (optional) — fail (exit 1) on findings above severity (`low`, `medium`, `high`, `critical`). Default: no exit-code gate.
- `--format` (optional) — `json` or `markdown` (default).

## Outputs

- **stdout:** human-readable markdown report (or JSON if `--format json`)
- **exit code:** 0 if no findings above `--max-severity` threshold; 1 if any.
- **structured event** (when invoked from a hook/lab context): emits `failure_mode_finding` event per finding to `.forge/journey/<run-id>.jsonl` (per Spec A §8.2).

## Failure modes detected

| ID | Name | Detection strategy |
|---|---|---|
| FM1 | Hallucinated Dependencies | Static: import statements / package references not present in declared dependencies |
| FM2 | Context Window Blindness | Static: cross-file references where target file > N lines or > N hops away |
| FM3 | Training Data Bias | LLM-judged: snippet patterns that look like outdated stack-version idioms |
| FM4 | Overconfident Completions | LLM-judged: docstrings/comments asserting behavior that doesn't match implementation |
| FM5 | Security Vulnerability Propagation | Static: hardcoded secrets, SQL string concatenation, eval(), XSS sinks; LLM-judged for context-dependent vulns |

## When to invoke

- **Standalone debugging:** `forge audit src/` to spot-check a directory before commit
- **In a lab grader (U2):** `evidence: { type: failure-mode-clean, target: src/, modes: [fm5], max_severity: low }` in `.forge/grader.yaml`
- **In a `PreToolUse` hook (Forge convention):** before a write tool fires, audit the target file
- **In CI (when GH Actions budget refreshes):** PR check via dormant `.github/workflows/audit.yml`

## Rules file

Detection rules are data-driven from `shared/failure_mode_rules.yaml`. Adding a new pattern = edit the YAML, add a test in `tests/`, no Python changes required.

## Adapters

- Claude Code: `adapters/claude_code/SKILL.md` + `invoke.sh`
- Copilot: `adapters/copilot/SKILL.md` + `github-bundle/skills/failure-mode-audit/SKILL.md` + `github-bundle/prompts/failure-mode-audit.prompt.md`
