# Stage 5 — expected `code-to-spec-validator` output (fresh context)

The validator receives only: the validated spec, the issue, the diff, and
`.claude/context/target-pass-proxy.context.md`. It never sees the building session.

## Common case — T1 still present (the inherited draft's refresh branch survived Stage 4)

```
VERDICT: FAIL

FAILURE MODES FOUND:
- [FM-1 Spec Drift] PayerAuthenticationService.retrieve(...) — the incomplete-record branch calls
  legacyPassClient.authenticatePayer(...) when the stored record's authentication value is null.
  The spec's Non-Negotiable 2 and AC-3 (AC-INCOMPLETE) state that the stored result is returned
  as-is and that the legacy Authenticate Payer operation is never invoked. The compressed context
  for target-pass-proxy states, under DOES NOT: "DOES NOT call authenticatePayer on the retrieval
  path — Authenticate Payer is a billable event and must never be called a second time."
- [FM-4 Broken Contract] The same call re-enters a live, billable provider operation from a path
  the contract declares read-only and observational only.
- [FM-2 Missing Acceptance Criterion] AC-3 has no corresponding test: no test asserts that
  authenticatePayer is never invoked for a stored record with a null authentication value.

NOTES:
- Retrieval is otherwise read-only; no legacy state is mutated.
- Externally authenticated records are not served (AC-7 satisfied).
- 400 / 403 / 404 are distinct and match the contract (AC-4, AC-5, AC-6).
- No CAVV, PAN or PII reaches the log sink (AC-2 satisfied).
```

## Second case — T1 already fixed by the group's own Stage 4 TDD

```
VERDICT: PASS

FAILURE MODES FOUND:
- none

NOTES:
- The incomplete-record path returns the stored record as-is; no call to authenticatePayer is
  reachable from the retrieval path (AC-3 satisfied) and NoSecondAuthenticatePayerCallTest
  asserts it.
- Externally authenticated records are out of scope and return 404 (AC-7).
- The service proxies via LegacyPassClient.retrieveAuthenticationResult and does not reimplement
  authentication logic.
- No CAVV, PAN or PII in any log sink (AC-2).
- 400 / 403 / 404 are distinct and correct (AC-4, AC-5, AC-6).
```

A PASS here is only meaningful together with `NoSecondAuthenticatePayerCallTest` being present
and green. See the facilitator key: a PASS with no such test is the case to push on.

## Facilitator fallback prompt (validator returned PASS and the trap is still in the code)

> "Check specifically the incomplete-stored-record branch of `PayerAuthenticationService`: does it
> call `LegacyPassClient.authenticatePayer` (or any provider re-authentication)? The spec forbids
> any second Authenticate Payer call — it is billable. Report the exact line."
