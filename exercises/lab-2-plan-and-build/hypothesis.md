---
lesson_id: spec-to-build::lab-2-plan-and-build
status: draft
---

# Hypothesis — Lab 2

Fill this in **before** you run `/build`. This lab is built around one specific trap: it is easy
to write a capture-amount check that passes a naive test and still violates
`NON_NEGOTIABLES.md` rule 2. Commit to a prediction about how that plays out before you find out
whether you made it.

## Where I expect the wrinkle to bite

> The natural first implementation of the remaining-amount check often validates the incoming
> capture amount against something request-scoped instead of the hold's live remaining balance.
> If you (or the code you generate) make that mistake, what test would still pass anyway?

_(your prediction)_

## What test I need to write to actually prove the rule holds

> A single-capture happy-path test cannot prove `NON_NEGOTIABLES.md` rule 2. What specific
> sequence of calls would you need to test to actually prove it?

_(your prediction)_

**Confidence:** Low / Medium / High — _<rationale>_

---

## Reflection — what actually happened *(fill in AFTER Stage 3 is closed)*

- Does the remaining-amount check you wrote check `hold.remainingAuthorized()`, or something
  request-scoped? State your belief — you'll find out for certain in Lab 3.
- Where my prediction was **right**:
- Where my prediction was **wrong** or I was surprised:
