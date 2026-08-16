# Non-negotiables — Retrieve Payer Authentication Results (PGSE-88)

These bind every change in this repo. They outrank convenience, tidiness and "it would be more
helpful if…". When a non-negotiable and a specific instruction disagree, the non-negotiable wins.

## 1. Never log sensitive data

The retrieval response carries the authentication value (CAVV), card data and full
billing / shipping / customer PII. None of it goes to a log line, an error message, an exception
message, a metric label or any other sink. No "temporary debug logging" of a request or response
object. Application logs stay separate from security/audit logs.

## 2. Retrieval is read-only

This API retrieves a stored result. It must never influence a live transaction outcome and must
never mutate state on the legacy platform.

## 3. Authenticate Payer is billable and must not be called a second time

The legacy edge exposes a live Authenticate Payer operation. Every invocation is charged and
affects the live outcome. The retrieval path must never invoke it — not to refresh a record, not
to fill a missing field, not "just in case". If a stored record is incomplete, the incomplete
stored record is the answer.

## 4. Correlation IDs end to end

Every inbound tracing header is propagated across the hop to the legacy edge. Values are
propagated, never logged.

## 5. Deny by default at the trust boundary

Every interface is a trust boundary, including calls from other internal services. An unknown or
absent caller is refused. Validate inputs in this service; do not rely on an upstream caller
having done it.

## 6. Proxy, do not reimplement

The legacy platform is the system of record. This service retrieves and maps. It does not
reimplement authentication logic, does not recompute authentication outcomes, and does not
invent a local source of truth.

## 7. Stay inside the spec

Implement the spec's in-scope items and respect its out-of-scope list. Where the spec is silent,
stop and name the gap — do not pick a default silently.
