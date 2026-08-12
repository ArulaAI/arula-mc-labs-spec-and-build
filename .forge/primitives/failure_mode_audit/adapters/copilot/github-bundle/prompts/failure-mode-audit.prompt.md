---
mode: agent
description: Run the Forge U1 /failure-mode-audit primitive on a path.
---

# /failure-mode-audit

Scan {input:path} for the 5 AI Failure Modes.

If no path provided, default to current working directory (`.`).

Run:

```bash
python .forge/primitives/failure_mode_audit/shared/auditor.py {input:path|.} --format markdown
```

Surface critical and high-severity findings as action items the user should address before proceeding. For medium/low findings, mention them but do not block.

If exit code is 1, the audit found findings above the configured `--max-severity` threshold — STOP and surface them.
