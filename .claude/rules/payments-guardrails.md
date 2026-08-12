# Payments guardrails

Payments-domain review bar for `lab-preauth`, grounded in `specs/NON_NEGOTIABLES.md`.
`pr-reviewer` and `code-to-spec-validator` both check diffs against these — the guardrail exists
whether or not a test happens to catch a violation.

## The remaining-amount rule (the wrinkle)

**No capture or reverse logic may check any amount against a value captured earlier in the
request lifecycle** — the original `AuthMessage.requestedAmount`, the hold's original
`amountAuthorized` taken alone, or the incoming `CaptureRequest.amount` in isolation. The only
value that may gate a capture decision is the hold's **live, current**
`Hold.remainingAuthorized()` (`amountAuthorized - amountCaptured`), computed fresh at the moment
of *that specific capture*.

This is the guardrail this lab is built to exercise. The natural first implementation gets this
wrong in a way that still passes a naive single-capture test: it validates the incoming amount
against something request-scoped instead of the hold's live remaining balance. It only fails on a
*second* partial capture — hold for 100.00, capture 60.00 (succeeds), capture 50.00 (must be
rejected — only 40.00 remains — but the buggy check sees 50.00 ≤ 100.00 and wrongly allows it).

**If you see a check against anything other than the hold's current remaining amount, that is a
defect — flag it even if a test happens to pass, because it means the test coverage is the gap,
not just the code.**

## The three non-negotiables, as a review checklist

1. **Idempotency.** A repeated `(holdId, requestId)` capture must return the original outcome
   without a second increment to `amountCaptured`. Trace the actual code path — don't assume a
   check exists because a variable is named `requestId`.
2. **Remaining-amount ceiling.** See above — this is the rule most likely to be subtly wrong.
   Require a sequential-partial-capture test (capture, then capture again, summing past the
   authorized amount) in the diff's test coverage — a single-capture happy-path test does not
   prove this rule holds.
3. **Status gate.** Capture must be rejected outright when the hold is `REVERSED`, `EXPIRED`, or
   already `CAPTURED` — checked before or as part of the same atomic update as rules 1-2, not as
   an afterthought a race could skip.

## Concurrency

All three checks above must happen **inside the same atomic `HoldStore.update` compute**, not as
separate reads followed by a write. Two racing captures that each read a stale `amountCaptured`
independently can both pass validation and both apply — that is a guardrail violation regardless
of how the individual checks read in isolation.
