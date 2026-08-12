---
mode: agent
description: Run the Forge U2 /lab-grader primitive on a lab workspace.
---

# /lab-grader

Grade {input:lab_root} against its rubric YAML.

If no lab root provided, default to current working directory (`.`).

Run:

```bash
python -m primitives.lab_grader.shared.grader {input:lab_root|.} --run-id {input:run_id|auto} --format markdown
```

Surface the final percentage and pass/fail verdict. For each failed criterion, list the criterion ID and reason so the learner knows what to address. For a passing grade, confirm success and mention the path to `grade.json`.

If exit code is non-zero, STOP and surface the error output — do not attempt to interpret partial results.
