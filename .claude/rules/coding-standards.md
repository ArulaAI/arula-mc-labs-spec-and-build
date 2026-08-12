# Coding standards

The general review bar for `lab-preauth`. Not payments-specific — these apply to any change in
this codebase. `pr-reviewer` reviews every diff against this file and against
`payments-guardrails.md`.

1. **Atomic state transitions.** Every state transition on a `Hold` goes through
   `HoldStore.update`'s atomic compute — never a read-then-write pattern that can race. Two
   concurrent calls reading the same state and writing independently is a defect regardless of
   whether a specific test happens to catch it.
2. **No unhandled exception paths.** No unhandled exception may leak an internal error to a
   caller instead of a typed result (`CaptureOutcome.Rejected` for this service). A caller should
   never see a stack trace where a rejection reason belongs.
3. **No silently swallowed checks.** Public methods on `HoldService` should not silently swallow a
   status check — if a precondition fails, that failure must be visible in the return value, not
   absorbed.
4. **Coverage must prove the claim, not just exist.** A single happy-path test is not coverage of
   a multi-step invariant. If the behavior being tested only matters across a *sequence* of calls
   (e.g. two captures against the same hold), the test suite needs a test that actually exercises
   that sequence — a single-call test passing is not evidence, even if the implementation happens
   to be correct. Flag missing sequential coverage as a defect in the test suite, not a nitpick.
5. **Flag the test gap, not just the code gap.** If an implementation is correct but only a
   single-call test protects it, that is still a finding — nothing proves the behavior stays
   correct on the next change.
