---
name: hand-off
description: Close out the stage the participant just finished — appends a dated entry to docs/workflow-tracker.md summarizing the artifacts produced and the verdict or decision reached, then confirms it's safe to move on. Use at the end of every stage in the spec-to-build flow (context, spec, plan, TDD/codegen, validation, review/gates, PR/grade).
---

# hand-off

You are closing out the stage the participant just finished, not starting a new one, and not
producing a project report. Keep this short and factual.

## Procedure

1. From the conversation so far, identify:
   - which stage just closed — Context or Spec (Lab 1, `exercises/lab-1-spec/`); Plan or
     TDD/Codegen (Lab 2, `exercises/lab-2-plan-and-build/`); Validation or Review/Gates (Lab 3,
     `exercises/lab-3-validate-and-review/`); or PR/Grade (Lab 4, `exercises/lab-4-ship/`) — these
     are six separate checkpoints across four exercises, not one hand-off per exercise,
   - what artifact(s) it produced or changed,
   - what verdict or decision was reached — a tool verdict if one exists (`SPEC STATUS: READY`,
     `PLAN: <N> issues...`, `VALIDATION: PASS/FAIL`, `REVIEW: APPROVE/BLOCKED`, a gate exit code),
     or the participant's explicit call if the stage had no tool verdict (e.g. Stage 0 context).
2. If any of this is ambiguous from context, ask the participant in one line rather than guessing.
3. Append one entry to `docs/workflow-tracker.md` (create it with a one-line header if it somehow
   doesn't exist) in exactly this format:

   ```
   ## Stage <n> — <stage name>
   - **Closed:** <UTC timestamp>
   - **Artifacts:** <files touched or created this stage>
   - **Verdict / decision:** <the tool verdict, or the human's explicit call>
   - **Human gate:** <one line — what the participant confirmed before moving on>
   ```

4. Confirm back to the participant, in one line, that the stage is recorded and it's safe to
   continue.

Do not restate the spec, the diff, or the code. Do not summarize the whole lab so far — that's
what `journey-curator`/`/grade` are for. This is a single stage's close-out record.
