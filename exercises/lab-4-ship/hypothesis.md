---
lesson_id: spec-to-build::lab-4-ship
status: draft
---

# Hypothesis — Lab 4

Fill this in **before** you run the PR-creation stage of `/build` or `/grade`.

## What I expect the grade to reflect

> `.forge/grader.yaml` scores more than "does the code compile" — it checks that the fresh-context
> subagents actually ran, that gates were green, and that hand-offs were recorded. Which criteria
> do you predict you'll pass easily, and which do you predict is riskiest for you?

_(your prediction)_

## Why the PR body should only exist after gates are green

> `docs/plans/pr-body.md` is assembled only once validation, review, and `mvn verify` are all
> clean, regardless of whether a real PR ever gets opened from it. What would go wrong if the
> orchestrator wrote it earlier — say, right after code generation, before the fresh-context
> checks ran?

_(your prediction)_

**Confidence:** Low / Medium / High — _<rationale>_

---

## Reflection — what actually happened *(fill in AFTER `/grade` runs)*

- Where my prediction about the grade was **right**:
- Where my prediction was **wrong** or I was surprised:
- One thing the grade card showed about my *process*, not just my output:
- Did a real PR get opened, or did the lab fall back to `docs/plans/pr-body.md` as the
  deliverable? Was that made explicit, or did you have to check?
