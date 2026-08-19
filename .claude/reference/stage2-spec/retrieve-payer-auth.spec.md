# Retrieve Payer Authentication Results (PGSE-88)

**Status:** READY — validated by `spec_check.py` (`spec.status.json` → `"valid": true`).
**Owner:** AFR Modernization · **Repo:** `boost-authentication-service` (producer),
`boost-order-processing` (consumer)

## Context

The modernized gateway (Boost) does not yet perform strong cardholder authentication, so
authenticated transactions still run through the legacy Target/PASS platform. Target/PASS remains
the system of record for payer authentication.

Order Processing needs payer authentication results for transactions the gateway authenticated
internally. This feature exposes a modern REST endpoint that proxies retrieval to the legacy
platform and maps the response onto the modern contract, so merchants keep the existing
authentication behaviour while their flows move to Boost.

The legacy edge (`target-pass-proxy`) is not in this workspace. What it does, what it returns and
what it must never be asked to do is described in
`.claude/context/target-pass-proxy.context.md`.

## Scope

In scope:

- A modern REST endpoint returning payer authentication data plus order details for a given
  merchant / order / authentication transaction.
- EMV 3DS, passkey and RuPay authentication types, including challenge/response, protocol
  version, authentication value and PSD2 SCA exemption data.
- Proxy behaviour to the legacy platform for transactions authenticated there.
- Consumer wiring in `boost-order-processing` against the published contract.

Out of scope — do not implement:

- **Externally authenticated transactions.** Only transactions the gateway authenticated
  internally are served. An externally authenticated stored record is not returned as if it were
  internally authenticated — it is refused, per AC-7.

  *Refused with 404, not a distinct status: this API does not confirm the existence of records
  outside its scope. From the caller's perspective there is no in-scope result, which is the same
  observable state as no record at all. 404 is also already declared in the shared OpenAPI
  contract, so refusing this way needs no contract change.*

  Refusing to serve an `EXTERNAL` record is **not** "implementing externally-authenticated
  handling" — it is the absence of it. What stays out of scope is building support for
  externally-authenticated transactions: no external provider, no alternate authentication path,
  no separate retrieval flow.
- **Re-running or re-triggering authentication.** Authenticate Payer is a billable event. This
  API is read-only retrieval and must never cause a second authentication.
- Caching the retrieved result, retrying the legacy retrieval, or validating the format of the
  authentication value. None of these is requested, and the first two change the observable
  behaviour of a money-adjacent path.

## Interfaces

`GET /merchants/{merchant_wsapi_id}/orders/{order_wsapi_id}/authentications/{authentication_transaction_wsapi_id}`

Path parameters: `merchant_wsapi_id`, `order_wsapi_id`, `authentication_transaction_wsapi_id`.

Tracing / correlation headers to propagate: `X-Client-Correlation-Id`, `X-Mc-Correlation-Id`,
`X-Mc-Correlation-Request-ID`, `X-Mc-Tns-Logging-Id`, `X-Mc-Toggle-Version`.

Caller identity: `X-Mc-Client-Id`. Deny by default — an unknown or absent client id is refused.

Responses: `200` `PayerAuthenticationWithOrderDetails` · `400` malformed request ·
`403` unauthorized caller · `404` no matching record.

Legacy edge operations consumed: `retrieveAuthenticationResult` (read-only) only.
`authenticatePayer` is **not** part of this interface.

Contract: `src/main/resources/openapi/payer-authentication-v1.yaml` (shared with the consumer).

## Data

`PayerAuthenticationWithOrderDetails`:

- `payerAuthentication` — method, status, scheme, protocol version, challenge indicator,
  authentication value (CAVV, nullable), PSD2 SCA exemption.
- `legacyOrderData` — browser, IP address, reference order.
- `merchant` — merchant id, name, category code.
- `order` — currency, amount, customer reference, billing/shipping country, funding
  (method, card number, brand).
- Errors are structured objects: source, reason code, description, recoverability, details.

The legacy field-by-field mapping is in `.claude/context/target-pass-proxy.context.md`. The
mapping is 1:1; nothing is computed, defaulted or enriched on the modern side. A stored record
with no authentication value maps to a null `authenticationValue`.

Sensitive: `authenticationValue` (CAVV) and `order.funding.cardNumber` (PAN) are cardholder data;
customer reference, countries and IP address are PII.

## Acceptance Criteria

AC-1: Given an internally authenticated transaction with a valid merchant / order /
authentication transaction id, when the endpoint is called, then it returns 200 with a
`PayerAuthenticationWithOrderDetails` whose authentication, legacy order data, merchant and order
blocks are all mapped from the stored legacy record.

AC-2: Given a successful retrieval, when the response is processed, then no authentication value,
PAN or PII is written to any log sink, error message or metric.

AC-3: Given a stored authentication result missing an optional field — specifically a stored
record whose authentication value is null — when retrieval is called, then the service returns
the stored result as-is, mapping the gap through as null, and the legacy Authenticate Payer
operation is never invoked. *(Referred to elsewhere as **AC-INCOMPLETE**; Authenticate Payer is
billable, so "never invoked" is the assertion, not a preference.)*

AC-4: Given no matching authentication record, when the endpoint is called, then it returns 404
with a structured error — not 200 with an empty body.

AC-5: Given an unauthorized or unidentified caller, when the endpoint is called, then it returns
403 and no authentication or order data.

AC-6: Given a malformed identifier in the request path, when the endpoint is called, then it
returns 400 with a structured error.

AC-7: Given a stored authentication record whose `authenticationOrigin` is `EXTERNAL`, when the
endpoint is called, then the service returns 404 with no authentication or order data — the
record is never served as if it were internally authenticated.

AC-8: Given inbound tracing headers, when the endpoint is called, then those headers are
propagated across the hop to the legacy edge and echoed to the caller, and their values are never
written to a log.

AC-9: Given the consumer in `boost-order-processing`, when it looks up an order's payer
authentication result, then it propagates the tracing headers it received and treats a 404 from
the producer as "no stored result" rather than a failure.

## Non-Negotiables

1. **Retrieval is read-only.** The call must never influence a live transaction outcome and never
   mutates legacy state.
2. **Authenticate Payer is billable and must never be called a second time.** No path reachable
   from a retrieval request may invoke `LegacyPassClient.authenticatePayer` — not to refresh a
   stale record, not to fill a null authentication value, not "just in case". This is the
   criterion AC-3 makes testable.
3. **Never log sensitive data.** No CAVV, PAN or PII in application logs, error responses or
   exception messages. Do not log the legacy record or the mapped response object.
4. **Correlation IDs end to end.** Every inbound tracing header is propagated across the hop;
   values are propagated, never logged.
5. **Deny by default at the trust boundary.** Every interface is a trust boundary, including
   internal callers. Validate inputs in this service.
6. **Proxy, do not reimplement.** The legacy platform is the system of record. This service
   retrieves and maps; it does not recompute an authentication outcome or build a local source of
   truth.
7. **Contract-first.** `payer-authentication-v1.yaml` is shared with the consumer; the response
   shape does not change unilaterally.

## Risks

- The retrieval response carries CAVV, card data and full billing / shipping / customer PII — a
  single "helpful" debug log leaks cardholder data.
- A gap-filling call to the provider is invisible in tests and in behaviour, and is charged on
  every incomplete record. The only evidence is the provider's invoice.
- The legacy platform is the system of record; drift between the mapped modern response and the
  stored legacy record would be invisible to the caller.
- The stored live-authentication response has a short TTL (~10 minutes) on the legacy side; the
  modern path is observational only and must not attempt to refresh it.
