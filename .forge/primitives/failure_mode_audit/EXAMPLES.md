# /failure-mode-audit — Examples

## Example 1: Audit a directory before commit

```bash
$ python -m primitives.failure_mode_audit.shared.auditor src/
# Failure-mode audit: src/

## FM5 (1 findings)

- **critical** `src/auth.py:14` — Possible hardcoded secret
```

## Example 2: Audit only for security issues, fail on critical

```bash
$ python -m primitives.failure_mode_audit.shared.auditor src/ --modes fm5 --max-severity critical
$ echo $?
1   # exit 1 because there's a critical finding
```

## Example 3: JSON output for piping

```bash
$ python -m primitives.failure_mode_audit.shared.auditor src/ --format json | jq '.[] | select(.severity == "critical")'
{
  "mode": "fm5",
  "severity": "critical",
  "file": "src/auth.py",
  "line": 14
}
```

## Example 4: Use in a U2 lab grader rubric

```yaml
# .forge/grader.yaml
criteria:
  - id: zero-secrets
    title: No critical secrets in submission
    weight: 30
    evidence:
      type: failure-mode-clean
      target: src/
      modes: [fm5]
      max_severity: high
```

## Example 5: Use in a Claude Code PreToolUse hook

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tool": "Write" },
        "command": "python .forge/primitives/failure_mode_audit/shared/auditor.py $CLAUDE_TOOL_PATH --modes fm5 --max-severity critical"
      }
    ]
  }
}
```

If audit exits 1, the hook blocks the Write tool from firing.
