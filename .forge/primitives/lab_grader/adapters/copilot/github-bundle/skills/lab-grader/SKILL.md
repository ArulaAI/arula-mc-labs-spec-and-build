---
name: lab-grader
description: Grade a Forge lab against its rubric YAML. Evaluates each criterion, computes a weighted total score, writes grade.json, and emits a lab_grader_run journey event. Available to coding agent + CLI + chat.
tools:
  - shell
---

# Skill: lab-grader

Grade a Forge lab workspace against its `rubric.yaml`, producing a weighted score, per-criterion verdicts, and a `grade.json` scorecard.

## How to invoke

Run from repo root:

```bash
python -m primitives.lab_grader.shared.grader <lab_root> --run-id <id> --format json
```

Or use the slash command `/lab-grader <lab_root>` from `prompts/lab-grader.prompt.md`.

## Output

`grade.json` written to `<lab_root>/grade.json` containing:
- `total_score` / `max_score` / `percentage`
- `criteria_results`: list of `{criterion_id, score, max_score, passed, reason}`
- `run_id`, `graded_at`

## When to use

- After a learner signals completion — grade before generating scorecard
- In sim-content pipeline — auto-grade each snapshot
- In CI via `workflow_dispatch:` for batch re-grading
- Manually when regenerating a scorecard for a known run ID

## Invariants

- Wraps `.forge/primitives/lab_grader/shared/grader.py` — DO NOT duplicate logic
- Updates land via `forge sync` per the lab's `.forge/manifest.yaml` pin
