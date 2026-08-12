# Facilitator key — Spec to Trusted Build (lab-preauth)

Not for participants. Reference solutions and expected outcomes for grading and troubleshooting.

**Exercise map.** SPEC → BUILD → TRUST → SHIP. The lab is delivered as four `exercises/` folders,
each with its own `hypothesis.md` / `instructions.md` / `spec.md` (the exercise's evidence
worksheet — distinct from the technical spec below): `exercises/lab-1-spec/` (Stages 0-1, SPEC),
`exercises/lab-2-plan-and-build/` (Stages 2-3, BUILD), `exercises/lab-3-validate-and-review/`
(Stages 4-5, TRUST — kept as two separate checkpoints), `exercises/lab-4-ship/` (Stage 6, SHIP).
Stage numbers below refer to the original stage numbering, still used internally.

## 1. The complete, correct spec

The gaps seeded in `specs/incremental-auth.spec.md` should be closed to something equivalent to:

- **Interfaces:** `capture(CaptureRequest)` returns `CaptureOutcome` — `Captured(Hold updatedHold)`
  on success, `Rejected(String reason)` on any of: idempotent replay (still `Captured` with the
  original hold, not `Rejected` — a replay is a success, not a failure), over-capture attempt, or
  capture against a non-`ACTIVE`/non-`PARTIALLY_CAPTURED` hold. `reverse(String holdId)` returns
  the updated `Hold` with status `REVERSED`, or throws if the hold doesn't exist.
- **Risks:** concurrent captures against the same hold must be serialized per-hold (the
  `HoldStore.update` atomic-compute pattern already scaffolded is the intended mechanism — the
  transition function must do the idempotency check, the remaining-amount check, and the status
  check *inside* the compute, not before it, or two racing captures can both read a stale
  `amountCaptured` and both pass validation).
- AC-4 should be replaced or dropped — "reasonably under load" isn't testable. If a participant
  keeps a load-related AC, it should become something concrete (e.g. "N concurrent capture calls
  against the same hold result in no overcapture and no lost update") or be removed as out of
  scope for this exercise.

## 2. The invariant set

See `specs/NON_NEGOTIABLES.md` — idempotency, capture ≤ remaining held amount, no capture after
reverse/expiry. All three should map 1:1 to acceptance criteria in the closed-out spec.

## 3. The wrinkle — where it bites, and how it's caught

**This wrinkle is not seeded into the starter code.** `capture()` and `reverse()` ship as
`UnsupportedOperationException` stubs (see `HoldService`), exactly per the lab's starter-state
requirement. The wrinkle below describes the failure mode participants are expected to produce
*themselves* during Stage 3 (TDD/codegen), and what should catch it in Stages 4–5.

**The wrinkle:** the natural first implementation of the remaining-amount check
(`NON_NEGOTIABLES.md` rule 2) validates the incoming `CaptureRequest.amount` against something
request-scoped — e.g. re-reading `AuthMessage.requestedAmount`, or checking only that
`amount > 0` and `amount <= amountAuthorized` — instead of checking against
`hold.remainingAuthorized()` computed fresh at the moment of this specific capture. This passes a
naive happy-path test (a single capture within the original authorized amount looks fine) but
fails the moment a *second* partial capture is attempted: e.g. hold for 100.00, capture 60.00
(succeeds), capture 50.00 (should be rejected — only 40.00 remains — but the buggy check sees
50.00 ≤ 100.00 and allows it, producing 110.00 captured against a 100.00 hold).

**Where it should get caught:**
- A test derived directly from `NON_NEGOTIABLES.md` rule 2 / spec AC-2 — two sequential partial
  captures summing over the authorized amount — should fail against the buggy implementation.
  If the participant's TDD pass in Stage 3 only wrote a single-capture happy-path test, this
  invariant test is missing, and that's a legitimate finding for `code-to-spec-validator`.
- `code-to-spec-validator` (Stage 4, fresh context): given only the spec, the issue, and the diff,
  it should identify that the capture check is not evaluated against `remainingAuthorized()` and
  return FAIL against AC-2 / NON_NEGOTIABLES rule 2.
- `pr-reviewer` (Stage 5, fresh context) is a second, independent chance to catch the same thing
  if the validator somehow passed it — this is the "no sycophancy" backstop the lab is built to
  demonstrate.

## 4. Expected planner issue breakdown

A reasonable ordered breakdown from the closed spec:
1. `HoldStore`: add idempotency-key tracking (applied `(holdId, requestId)` pairs) so capture can
   detect replays before or as part of its atomic update.
2. `HoldService.capture`: implement the three checks (idempotent replay, remaining-amount ceiling,
   status gate) inside a single `HoldStore.update` transition.
3. `HoldService.reverse`: implement the status transition to `REVERSED`, guarding against
   reversing an already-`CAPTURED` or already-`REVERSED` hold.
4. Tests for all three `NON_NEGOTIABLES.md` rules, including the two-sequential-partial-captures
   case that exercises the wrinkle.

## 5. Expected gate outcomes

- `/spec` on the unmodified stub: reports the two missing sections and the non-testable AC-4.
  Passes once closed per section 1 above.
- `/build`: if the capture implementation has the wrinkle, `code-to-spec-validator` returns FAIL
  on AC-2; the PR is blocked until fixed. Once fixed, `mvn verify` (quality gates) should pass
  cleanly — no planted lint/secret/dependency issues exist in this lab (unlike the wrinkle, which
  is a logic defect, not a static-analysis-catchable one).
