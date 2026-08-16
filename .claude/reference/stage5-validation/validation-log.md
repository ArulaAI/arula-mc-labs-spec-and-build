# Validation log — Stage 5

| Issue | Validator verdict | Failure mode | Criterion | Action |
|---|---|---|---|---|
| 1 Mapping | PASS | — | AC-1 | — |
| 2 Error semantics | PASS | — | AC-4, AC-5, AC-6 | — |
| 3 Scope | PASS | — | AC-7 | — |
| 4 Tracing headers | PASS | — | AC-8 | — |
| 5 Logging | PASS | — | AC-2 | — |
| 6 Read-only retrieval | **FAIL** | Spec drift / broken contract | AC-3 (AC-INCOMPLETE), Non-Negotiable 2 | Return to Stage 4: write `NoSecondAuthenticatePayerCallTest` (RED), remove the `authenticatePayer` call from the incomplete-record branch, re-validate |
| 6 Read-only retrieval (re-validated) | PASS | — | AC-3 | — |
| 7 Consumer wiring | PASS | — | AC-9 | — |

**Smallest fix applied:** delete the refresh branch in `PayerAuthenticationService.retrieve(...)`
and return the stored record as-is. No other file changed. The mapper already maps a null
authentication value through as null.

**Evidence:** `NoSecondAuthenticatePayerCallTest` RED before the fix (`authenticatePayer` invoked
once), GREEN after; `NoBillableCallThroughLegacyStubTest` shows the stub's billable-call counter
at 0 for both the complete and the incomplete record.
