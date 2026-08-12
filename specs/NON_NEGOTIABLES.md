# Non-negotiables — incremental authorization, partial capture, idempotency

These three invariants are the ground truth for this feature. Every acceptance criterion in
`incremental-auth.spec.md` must trace back to one of these. The `code-to-spec-validator` and
`pr-reviewer` check every change against these directly, not against the happy path.

## 1. Idempotency: a retried capture must never apply twice

A `CaptureRequest` is uniquely identified by `(holdId, requestId)`. If a request with a
`(holdId, requestId)` pair that has already been successfully applied is submitted again — the
same network retry, the same client resubmission after a timeout — the system must return the
**original outcome** without capturing a second time. `amountCaptured` on the hold must not
increase as a result of the retry.

**Testable as:** submit the same `CaptureRequest` (same `holdId`, same `requestId`, same amount)
twice. `hold.amountCaptured()` after both calls must equal `hold.amountCaptured()` after the first
call alone.

## 2. Partial capture must never exceed the *remaining* held amount

A capture's amount must be checked against the hold's **current remaining authorized amount**
(`amountAuthorized - amountCaptured`, i.e. `Hold.remainingAuthorized()`), evaluated at the moment
of that capture — not against the original `AuthMessage.requestedAmount`, not against the hold's
original `amountAuthorized` alone, and not by looking at the incoming `CaptureRequest` in
isolation. Two partial captures that individually look valid can still be invalid together if
their sum exceeds what remains held.

**Testable as:** create a hold for 100.00. Capture 60.00 (succeeds, remaining is now 40.00).
Attempt to capture 50.00 (must be rejected — only 40.00 remains, even though 50.00 is less than
the original 100.00 request amount).

## 3. No capture after reverse or expiry

Once a hold's status is `REVERSED`, `EXPIRED`, or `CAPTURED` (fully captured), no further capture
may succeed — regardless of whether the remaining-amount math in rule 2 would otherwise allow it.

**Testable as:** reverse a hold, then attempt any capture against it — must be rejected. Advance
past `expiresAt`, then attempt any capture — must be rejected.
