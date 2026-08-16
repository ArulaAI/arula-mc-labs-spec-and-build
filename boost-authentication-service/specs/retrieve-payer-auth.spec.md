# Retrieve Payer Authentication Results (PGSE-88)

**Status:** DRAFT — carried over from the Solution Intent, not yet validated.
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

## Interfaces

`GET /merchants/{merchant_wsapi_id}/orders/{order_wsapi_id}/authentications/{authentication_transaction_wsapi_id}`

Path parameters: `merchant_wsapi_id`, `order_wsapi_id`, `authentication_transaction_wsapi_id`.

Tracing / correlation headers to propagate: `X-Client-Correlation-Id`, `X-Mc-Correlation-Id`,
`X-Mc-Correlation-Request-ID`, `X-Mc-Tns-Logging-Id`, `X-Mc-Toggle-Version`.

Contract: `src/main/resources/openapi/payer-authentication-v1.yaml` (shared with the consumer).

## Data

`PayerAuthenticationWithOrderDetails`:

- `payerAuthentication` — method, status, scheme, protocol version, challenge indicator,
  authentication value (CAVV), PSD2 SCA exemption.
- `legacyOrderData` — browser, IP address, reference order.
- `merchant` — merchant id, name, category code.
- `order` — currency, amount, customer reference, billing/shipping country, funding.
- Errors are structured objects: source, reason code, description, recoverability, details.

The legacy field-by-field mapping is in `.claude/context/target-pass-proxy.context.md`.

## Acceptance Criteria

AC-1: Given an internally authenticated transaction with a valid merchant / order /
authentication transaction id, when the endpoint is called, then it returns 200 with
`PayerAuthenticationWithOrderDetails`.

AC-2: Given a successful retrieval, when the response is processed, then no authentication
value, PAN or PII is written to any log.

AC-3: the service should handle incomplete stored records gracefully.

## Risks

- The retrieval response carries CAVV, card data and full billing / shipping / customer PII.
- The legacy platform is the system of record; drift between the mapped modern response and the
  stored legacy record would be invisible to the caller.
