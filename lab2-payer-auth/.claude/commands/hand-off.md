---
name: hand-off
description: "Close out the lab stage that just finished. Appends a dated entry to boost-authentication-service/docs/workflow-tracker.md and records a hand-off event in the journey. Run it at every stage boundary (Stages 0-6)."
---

# hand-off

You are closing out the stage the participant just finished. You are not starting the next one
and you are not writing a project report. Keep it short and factual.

## Procedure

1. From the conversation so far, identify:
   - **which stage just closed** — 0 Ground · 1 Compress the legacy edge · 2 Author and validate
     the spec · 3 Plan: spec to issues · 4 TDD and correct the draft · 5 Validate against spec
     (fresh context) · 6 Review, gates, ship and close,
   - what artifact(s) it produced or changed, and **which repo** each lives in,
   - what verdict or decision was reached — a tool verdict where one exists
     (`spec.status.json valid:true`, `PLAN: <n> issues`, `VALIDATION: PASS/FAIL`,
     `REVIEW: APPROVE / REQUEST CHANGES / BLOCKER`, a `mvn verify` result), or the participant's
     explicit call where the stage had no tool verdict,
   - what the participant confirmed at the stage's **human gate**.
2. If any of that is ambiguous, ask the participant in one line rather than guessing.
3. Append one entry to `boost-authentication-service/docs/workflow-tracker.md` in exactly this
   format:

   ```
   ## Stage <n> — <stage name>
   - **Closed:** <UTC timestamp>
   - **Artifacts:** <files created or changed this stage, with their repo>
   - **Verdict / decision:** <the tool verdict, or the participant's explicit call>
   - **Human gate:** <one line — what the participant confirmed before moving on>
   - **Invariant:** <the stage's end invariant, and whether it holds>
   ```

4. Record the boundary in the journey so grading can see it:

   ```
   python3 .claude/scripts/journey_event.py hand-off --stage <n> --name "<stage name>"
   ```

   Run it from the workspace root. This is the graded evidence; the tracker entry is the
   human-readable record.
5. Confirm back to the participant in one line that the stage is recorded and it is safe to
   continue.

Do not restate the spec, the diff or the code. Do not summarise the whole lab so far. This is one
stage's close-out record.
