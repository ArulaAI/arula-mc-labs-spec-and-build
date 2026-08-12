---
name: lab-grader
description: Score the current lab run against .forge/grader.yaml and the journey log, and produce a grade card. Thin wrapper over the shared lab_grader primitive. Use once validation, review, and quality gates are all clean and the PR body has been written, to close out the lab.
---

# grade

Run the lab grader against this lab's rubric and journey log, then report the result plainly.

## Procedure

1. Read the current run ID from `.forge/.current-run-id` if it exists.
2. Run:
   ```bash
   bash .forge/primitives/lab_grader/adapters/claude_code/invoke.sh . \
     --run-id "$(cat .forge/.current-run-id 2>/dev/null || true)"
   ```
   If `.forge/.current-run-id` doesn't exist, drop `--run-id` entirely and let the grader use the
   newest journey file.
3. On a non-zero exit, surface the error and the last few log lines — do not retry silently.
4. Parse `.forge/journey/<run-id>/grade.json`.

## Output

- The overall percentage and total score (`total_score / max_score`).
- For every criterion: id, title, pass/fail, and the evaluator's note.
- For any failed criterion, call out specifically what's missing so the participant knows exactly
  what to close before re-running — don't just say "some criteria failed."
- The path to `grade.json`.
- A reminder, if the participant hasn't done it yet, to transcribe the per-criterion result into
  the grade-summary table in `exercises/lab-4-ship/spec.md`.

## Invariants

Grading logic lives in `primitives/lab_grader/shared/grader.py` upstream. Do not reimplement or
second-guess a criterion's pass/fail here — report what the grader returned.
