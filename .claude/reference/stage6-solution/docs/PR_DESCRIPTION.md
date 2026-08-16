# PGSE-88 — Retrieve Payer Authentication Results

**Repos in this change:** `boost-authentication-service` (producer),
`boost-order-processing` (consumer)
**Spec:** `specs/retrieve-payer-auth.spec.md` (READY — `spec.status.json` `"valid": true`)
**Plan:** `docs/plans/plan.md` · **Issues:** `issues.json` (7, local file — no GitHub issue created)

## What changed

**`boost-authentication-service`**

- `LegacyResponseMapper` maps the stored legacy record onto the full aggregate — authentication,
  legacy order data, merchant and order — 1:1 with the field map in the compressed context
  (AC-1).
- `PayerAuthenticationService` is read-only. The incomplete-stored-record branch that refreshed a
  null authentication value from the provider is gone; the stored record is returned as-is
  (AC-3 / AC-INCOMPLETE).
- Only `INTERNAL` records are served. An externally authenticated record returns 404 and is never
  served as if internally authenticated (AC-7).
- 404 / 403 / 400 are distinct: no matching record, unauthorized or unidentified caller, and
  malformed identifier, each with the structured `ErrorResponse` from the contract
  (AC-4, AC-5, AC-6).
- The five tracing headers are collected, carried into the legacy retrieval query and echoed to
  the caller; their values are never logged (AC-8).
- The retrieval path no longer logs the legacy record. It logs the authentication transaction id
  only (AC-2).

**`boost-order-processing`**

- `OrderAuthenticationLookup` propagates the tracing headers it received; the client maps the
  producer's 404 to "no stored result" rather than a failure (AC-9).
- The shared `payer-authentication-v1.yaml` is unchanged and byte-identical in both repos.

## Validator notes (fresh context, `code-to-spec-validator`)

FAIL on issue 6: the incomplete-record branch called `LegacyPassClient.authenticatePayer`, which
the spec's Non-Negotiable 2 and AC-3 forbid and which the compressed context lists under DOES
NOT. Smallest fix applied (return the stored record as-is); re-validated PASS. Issues 1–5 and 7
passed on first validation. Full trail: `docs/validation-log.md`.

## Reviewer notes (fresh context, `pr-reviewer`)

No BLOCKER outstanding. Findings raised and closed: the error body must not echo payload content;
the negative test for the billable call must assert `never()` rather than a call count read after
the fact.

## Gate results

| Gate | Result |
|---|---|
| `mvn verify` — `boost-authentication-service` (tests, ArchUnit layering, JaCoCo) | GREEN |
| `mvn verify` — `boost-order-processing` (tests incl. `ContractConsumerTest`) | GREEN |
| `NoSecondAuthenticatePayerCallTest` | GREEN — `authenticatePayer` never invoked |
| `NoBillableCallThroughLegacyStubTest` | GREEN — billable-call counter 0 for complete and incomplete records |
| Sensitive-data scan on `logs/auth-service.log` | CLEAN — no PAN, CAVV or customer reference |
| PAN/secret gate on the diff | CLEAN |
| PR gate guard | passed — this file could not be written until the gates above were green |

## Out of scope, deliberately not implemented

Externally authenticated transactions; any re-authentication or provider refresh; caching the
retrieved result; retrying the legacy retrieval; validating the format of the authentication
value. No GitHub issue or PR was created — `issues.json` and this file are local artifacts.
