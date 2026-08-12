---
lesson_id: spec-to-build::lab-4-ship
estimated_min: 11
primitives_used:
  l1:
    - /build
    - /grade
  l2:
    - journey-recorder
    - lab-grader
  l3:
    - work-orchestrator
---

# Lab 4 — Ship (Stage 6)

## Why this matters

A good spec plus fresh-context judgment — not raw code-generation speed — is what turned a
plausible implementation into a trusted one. This lab is where that gets closed out: the PR body
is assembled only once everything upstream is clean, and the grade is evidence of the process, not
just the output.

## Objective

Assemble the change record and get a reproducible score, with nothing implied that didn't actually
happen.

## Steps

1. Open `hypothesis.md` in this directory and fill in the pre-tool prediction section.
2. Confirm Lab 3 is fully closed: `docs/workflow-tracker.md` has entries for Stages 2-5, and
   `mvn verify` is clean.
3. Continue `/build` into its PR-creation stage. It **always** assembles the spec link, the
   validator's verdicts, the reviewer's notes, and the gate results into `docs/plans/pr-body.md` —
   this is the body of record regardless of what happens next.
4. **Then it checks whether it can go further.** If a GitHub remote is configured and you approve
   opening a PR, `/build` opens one using `docs/plans/pr-body.md` as the body. If no remote is
   configured (the default for this lab environment) or you don't approve, `docs/plans/pr-body.md`
   stands on its own as the deliverable. **Either way, be explicit about which happened** — don't
   describe a written PR body as an opened pull request unless one actually was opened.
5. Run `/grade` (or `make grade`). It scores the run against `.forge/grader.yaml`, including
   whether the fresh-context stages, the quality gates, and the hand-off checkpoints actually
   happened — not just whether the right files exist.
6. Fill in `spec.md` in this directory with the PR-body checklist and the grade summary.
7. Reopen `hypothesis.md` and fill in the reflection section.
8. Run `/hand-off` one last time to close the lab.

## What you'll see (so you know it worked)

- `docs/plans/pr-body.md` contains the spec link, per-issue validator verdicts, the reviewer's
  notes, and the `mvn verify` result — not a generic summary. This file exists whether or not a
  real PR was opened.
- If a real PR was opened, `/build` reports the PR URL/number explicitly. If not, it says plainly
  that no remote was configured or no approval was given.
- `.forge/journey/<run-id>/grade.json` has a percentage and a per-criterion pass/fail with a note
  for each.

## Self-check: have you met the review gate?

Before calling the lab done, confirm — on your own, no facilitator required:

- [ ] `docs/plans/pr-body.md` exists and was written only after Lab 3's gates were green
- [ ] You correctly state whether a real PR was opened, or explicitly that it wasn't — nothing is
      implied either way
- [ ] `/grade` ran and produced `grade.json`
- [ ] Any failed grading criterion is understood, not just noted
- [ ] `hypothesis.md`'s reflection section is filled in

## Acceptance criteria

- [ ] `docs/plans/pr-body.md` exists, references the spec, validator, reviewer, and gate results
- [ ] `.forge/journey/<run-id>/grade.json` exists
- [ ] `exercises/lab-4-ship/spec.md` worksheet is filled in
- [ ] `exercises/lab-4-ship/hypothesis.md` was written before this lab's tools and reflected on
      after
- [ ] `/hand-off` was run to close the lab
