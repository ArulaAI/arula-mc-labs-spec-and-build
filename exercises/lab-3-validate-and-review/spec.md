---
lesson_id: spec-to-build::lab-3-validate-and-review
status: draft
---

# Spec — Lab 3: Validate and review evidence worksheet

This is **not** the technical spec — that's `specs/incremental-auth.spec.md`. This worksheet is
your evidence that the two fresh-context checkpoints ran independently and caught what they were
supposed to catch.

## Stage 4 — Code-to-spec validation, per issue

| Issue ID | Verdict (PASS/FAIL) | If FAIL: rule violated and the concrete breaking scenario |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |

## Stage 5 — PR review and quality gates

| Issue ID | Reviewer verdict (APPROVE/BLOCKED) | Blocker findings (if any) |
| --- | --- | --- |
|  |  |  |
|  |  |  |

`mvn verify` final result: _____ (paste the pass/fail summary)

## The wrinkle — did it show up, and who caught it?

> If your capture-amount check had the request-scoped-instead-of-remaining-balance bug at any
> point, name which checkpoint actually caught it — your own test in Lab 2, the validator, or the
> reviewer — and why the others didn't (or would not have).

_(your answer)_

## Acceptance criteria

- [ ] Every table row above is filled in, not left as a placeholder
- [ ] Every Stage 4 row ends in PASS (after any FAIL → fix → re-validate loop back to Lab 2)
- [ ] Every Stage 5 row ends in APPROVE, and `mvn verify` is clean
- [ ] The wrinkle question is answered even if the wrinkle never actually appeared in your code
