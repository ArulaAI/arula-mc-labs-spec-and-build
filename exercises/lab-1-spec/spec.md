---
lesson_id: spec-to-build::lab-1-spec
status: draft
---

# Spec — Lab 1: Gap closure and traceability worksheet

This is **not** the technical spec — that's `specs/incremental-auth.spec.md`. This worksheet is
your evidence that you closed the gaps yourself and can trace every invariant, not just that
`spec-craft` stopped complaining.

## Gaps found and how they were closed

| Section / AC | What was wrong | How it was closed |
| --- | --- | --- |
| Interfaces |  |  |
| Risks |  |  |
| AC-4 |  |  |

## Traceability — NON_NEGOTIABLES.md rule → acceptance criterion

| Rule | One-line statement | Acceptance criterion it maps to |
| --- | --- | --- |
| 1 | Idempotency: a retried capture must never apply twice |  |
| 2 | Partial capture must never exceed the remaining held amount |  |
| 3 | No capture after reverse or expiry |  |

## Final `spec-craft` verdict

> Paste the final `SPEC STATUS: READY` line here.

_(paste)_

## Acceptance criteria

- [ ] Every row above is filled in, not left as a placeholder
- [ ] Every `NON_NEGOTIABLES.md` rule maps to a specific, named acceptance criterion
- [ ] The final verdict pasted is `SPEC STATUS: READY`, not `GAPS`
