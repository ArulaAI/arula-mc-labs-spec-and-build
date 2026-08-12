---
status: draft
---

# Spec: Incremental authorization with partial capture and strict idempotency

## Context

The authorization core currently supports creating a hold (`HoldService.createHold`) for the full
requested amount. Merchants need to capture (settle) against that hold incrementally — e.g. an
order that ships in parts — rather than only in one final capture. This must be safe to retry
under normal network failure conditions, and must never allow a merchant to collect more than what
was actually authorized.

## Scope

In scope: `HoldService.capture(CaptureRequest)`, `HoldService.reverse(String holdId)`, and whatever
`HoldStore` changes are needed to support them safely under concurrent calls. Out of scope: any
new HTTP endpoints, any change to `createHold`.

## Data

Uses the existing `AuthMessage`, `Hold`, `CaptureRequest`, `HoldStatus`, and `CaptureOutcome`
records in `com.mc.preauth.domain`. No new fields are anticipated, but confirm during planning
whether `HoldStore` needs additional state to track applied `(holdId, requestId)` pairs for
idempotency.

## Acceptance Criteria

- AC-1: A capture request with a `(holdId, requestId)` pair identical to one already applied
  returns the original outcome and does not increase `amountCaptured`.
- AC-2: A capture is rejected if its amount would cause `amountCaptured` to exceed
  `amountAuthorized`, checked against the hold's current remaining authorized amount at the time
  of the capture.
- AC-3: A capture against a hold in `REVERSED`, `EXPIRED`, or `CAPTURED` status is rejected.
- AC-4: The system should handle capture requests reasonably under load.

<!-- TODO: Interfaces section — what does capture() actually return/throw on rejection vs success?
     CaptureOutcome.Rejected exists in the domain but this section hasn't specified which
     rejection reasons map to which non-negotiable, or what reverse() returns. -->

<!-- TODO: Risks section — what's the concurrency risk if two captures for the same hold arrive
     at the same time from different threads? Needs to be spelled out before implementation. -->
