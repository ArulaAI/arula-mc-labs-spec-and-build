---
name: lab-grader
description: Grade a Forge lab against its rubric YAML. Evaluates each criterion (LLM-assisted + structural), computes a weighted total score, writes grade.json, and emits a lab_grader_run journey event. Use after a learner finishes a lab, in sim-content pipelines, or to regenerate a scorecard.
---

# /lab-grader

Claude Code adapter for the Forge primitive library U2 primitive.

## When invoked

1. Determine the lab root — user-mentioned path, else `.`
2. Determine the run ID — user-supplied `--run-id`, else auto-generated UUID
3. Run: `bash <skill_dir>/invoke.sh <lab_root> --run-id <id>`
4. Parse output. On non-zero exit, surface the error and the last log lines.

## Output expectations

- Always surface the final percentage and pass/fail verdict from `grade.json`
- For failed criteria, list criterion ID + reason so the learner knows what to address
- For a passing grade (>= rubric threshold), confirm success and mention the scorecard path

## Invariants

- Logic lives in `primitives/lab_grader/shared/grader.py` in the Forge primitive library
- DO NOT modify `invoke.sh` or duplicate grader logic — primitive library upgrades flow through `forge sync`
