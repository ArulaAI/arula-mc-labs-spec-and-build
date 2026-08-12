---
lesson_id: spec-to-build::lab-3-validate-and-review
estimated_min: 27
primitives_used:
  l1:
    - code-to-spec-validator
    - pr-reviewer
    - /build
  l2:
    - journey-recorder
  l3:
    - work-orchestrator
---

# Lab 3 — Validate and Review (Stages 4-5)

## Why this matters

This is the lab that makes "trust" real instead of a slogan. `code-to-spec-validator` and
`pr-reviewer` never saw why the diff from Lab 2 was written the way it was — only what it does.
Whether the pipeline catches a plausible-but-wrong capture-amount check gets decided here, in two
**visibly separate fresh-context checkpoints**, not one blended step.

## Objective

Get an independent validation verdict and an independent review verdict on the diff from Lab 2,
then a clean `mvn verify`.

---

## Stage 4 — Code-to-spec validation, fresh context (12 min)

**Objective.** Get an independent, context-blind verdict on whether the diff actually satisfies
the spec and the non-negotiables — not whether it looks like it was trying to.

**Command.**
```text
Validate the diff for each issue against specs/incremental-auth.spec.md and
specs/NON_NEGOTIABLES.md. Confirm: retries are idempotent, capture never exceeds the remaining
held amount, and no capture occurs after reverse or expiry. Return PASS or FAIL with the specific
criterion for any failure.
```

**What Claude is doing.** Dispatches `code-to-spec-validator` in a fresh context — it sees only
the spec, the issue, and the diff, nothing about why you wrote it the way you did. It defaults to
FAIL under any uncertainty and explicitly traces what happens on a *second* partial capture.

**Expected artifacts.** A `VALIDATION: PASS` or `VALIDATION: FAIL` verdict per issue, logged by
the validator itself to `docs/plans/validation-log.md` — not just left in the chat transcript.

**Inspect.** If it fails, does it name the exact rule and a concrete breaking scenario (e.g. "hold
100.00, capture 60.00, capture 50.00 — succeeds when it must not")? That specificity is the
signal it actually traced the code, not pattern-matched on variable names.

**Success / failure and return path.** `FAIL` sends you back to **Lab 2, Stage 3**
(`exercises/lab-2-plan-and-build/`) for the smallest fix — not a rewrite, and not straight to
Stage 5. Re-run the validator after the fix. `PASS` moves you to Stage 5.

**Human gate.** Did the verdict engage with what the diff actually does, or does it read like a
rubber stamp? If it's vague, don't trust it — look at the diff yourself.

**`/hand-off` checkpoint.** Run `/hand-off` once every issue has a validation verdict — even if
some issues looped back through Lab 2 first.

---

## Stage 5 — PR review and quality gates (15 min)

**Objective.** Get a second, independent judgment call, then run the hard, automated gates that
don't care about judgment at all.

**Command.** `pr-reviewer` runs as part of `/build`'s per-issue loop; then run:
```bash
mvn verify
```

**What Claude is doing.** `pr-reviewer` reviews the diff in a fresh context against
`.claude/rules/coding-standards.md` and `.claude/rules/payments-guardrails.md` — atomic
`HoldStore.update` transitions, no amount check against anything but the live remaining balance,
sequential-capture test coverage — without seeing the validator's verdict. `mvn verify` then runs
the JaCoCo coverage threshold, a Checkstyle lint check, and a secret/cardholder-data and
unknown-dependency scan.

**Expected artifacts.** A `REVIEW: APPROVE` or `REVIEW: BLOCKED` verdict, logged by the reviewer
itself to `docs/plans/review-log.md`; a clean or failing `mvn verify` run. If you try to write
`docs/plans/pr-body.md` before `mvn verify` is clean, a guard hook blocks the write outright.

**Inspect.** If blocked, are findings specific (file:line, concrete reason), not softened? If a
gate fails, which one — coverage, lint, or the secret/dependency scan — and why?

**Success / failure and return path.** `REVIEW: BLOCKED` sends you back to **Lab 2, Stage 3**. A
failed gate also sends you back to **Lab 2, Stage 3** (or to the test itself, if the gate is
coverage). Don't treat a passing validator as license to skip this stage — it's independent, not
confirmatory.

**Human gate.** Are you satisfied independent of what the validator already told you? This is a
second check, not a formality.

**`/hand-off` checkpoint.** Run `/hand-off` once review is clean and `mvn verify` passes. This
closes Lab 3 — PR assembly and grading happen in Lab 4 (`exercises/lab-4-ship/`).

---

## After Stage 5: reflect

Reopen `hypothesis.md` and fill in the reflection section — specifically, name which checkpoint
(your own test-writing in Lab 2, the validator, or the reviewer) actually caught the wrinkle, if
it showed up.

## Self-check: have you met the review gate?

Before moving to Lab 4, confirm — on your own, no facilitator required:

- [ ] `code-to-spec-validator` ran as a separate subagent dispatch for every issue, not as inline
      reasoning in this session
- [ ] `pr-reviewer` ran as a separate subagent dispatch, independent of the validator's verdict
- [ ] `mvn verify` passes clean
- [ ] `/hand-off` was run at the end of Stage 4 and at the end of Stage 5 — two separate entries
      in `docs/workflow-tracker.md`, not one

If you can't check all four, go back to the relevant stage before continuing.

## Acceptance criteria

- [ ] Every issue has a recorded `VALIDATION: PASS` from a fresh-context dispatch
- [ ] Every issue has a recorded `REVIEW: APPROVE` from a fresh-context dispatch
- [ ] `mvn verify` passes clean
- [ ] `exercises/lab-3-validate-and-review/spec.md` worksheet is filled in
- [ ] `exercises/lab-3-validate-and-review/hypothesis.md` was written before this lab's tools and
      reflected on after
- [ ] `docs/workflow-tracker.md` has two new entries, one per stage above
