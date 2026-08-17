# Compressed context — `target-pass-proxy` (Tier 1)

**Contract version:** 1.0.0 · **Generated:** 2026-08-16 · **Source revision:** `target-pass-proxy@rel-2026.07`
**Compression tier:** 1 (single foreign repo) · **Primary consumer:** `boost-authentication-service`

> This is a distilled map of a repository that is **not in your workspace**. It is the only thing
> you may treat as authoritative about that repository. If a fact you need is not here, stop and
> say so — do not infer it from the modern side, and do not invent it.

## Identity & purpose

`target-pass-proxy` is the legacy **Target/PASS** retrieval edge. It fronts the Payer
Authentication Service (PASS) on the legacy Target platform.

- It is the **system of record** for payer authentication results. The modern gateway (Boost)
  does not yet perform strong cardholder authentication.
- It is **not in this workspace**: too large to clone, and not ours to edit.
- The modern service `boost-authentication-service` **proxies** retrieval to it and maps its
  response onto the modern contract.

## Endpoints / interfaces

| Operation | Kind | Cost | Purpose |
|---|---|---|---|
| `retrieveAuthenticationResult` | read-only | free, repeatable, safe | Return the **stored** authentication result for one merchant + order + authentication-transaction id. No side effects. |
| `authenticatePayer` | live provider call | **BILLABLE — charged per invocation** | Perform a live payer authentication with the service provider. Affects the live transaction outcome. **Not part of retrieval.** |

**Lookup key.** `retrieveAuthenticationResult` matches on all three identifiers together —
merchant + order + authentication transaction. There is no partial lookup: an order id on its own,
or an authentication transaction id on its own, matches nothing. (The wider platform exposes
those narrower lookups elsewhere; this retrieval edge does not.)

**Correlation id.** The caller may pass its own correlation id with the lookup for tracing. It is
not part of the key and it does not change what comes back. The `correlationId` **on the returned
record** is a different value: it is the correlation id under which the legacy platform persisted
that authentication response, and it is returned exactly as stored.

## Request/response contracts

`retrieveAuthenticationResult(merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId, correlationId)`
returns one stored record, or **nothing** when no record matches (there is no "empty result"
object — absence is absence). The first three arguments are the key; `correlationId` is the
caller's tracing id and may be null.

Stored record shape:

```
merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId
authenticationOrigin          INTERNAL | EXTERNAL
authentication {
  authMethod                  EMV_3DS | PASSKEY | RUPAY
  authStatus                  e.g. AUTHENTICATION_SUCCESSFUL
  schemeName
  protocolVersion
  challengeIndicator
  cavv                        NULLABLE  <-- see "Nullable fields"
  psd2ScaExemptionCode
}
order {
  browserData, ipAddress, referenceOrder
  merchantName, merchantCategoryCode
  currency, amountMinor, customerReference
  billingCountry, shippingCountry
  fundingMethod, cardNumber (PAN), cardBrand
}
correlationId
```

### Nullable fields

- `authentication.cavv` (the CAVV / authentication value) **may be null on a stored record.**
  This is a legitimate stored state — for example a frictionless or exemption-carrying
  authentication that never produced an authentication value. A null CAVV is **not** an error, is
  **not** a sign of a corrupt record, and is **not** something to repair.
- Every other field above is populated on any record the legacy edge returns.

### Sensitive fields

`authentication.cavv` and `order.cardNumber` are cardholder data. `order.customerReference`,
`billingCountry`, `shippingCountry` and `ipAddress` are PII. None of them may reach a log sink,
an error message or a metric label.

## Field mappings needed by owned repos

Legacy stored record → modern `PayerAuthenticationWithOrderDetails`:

| Legacy field | Modern field |
|---|---|
| `authentication.authMethod` | `payerAuthentication.method` |
| `authentication.authStatus` | `payerAuthentication.status` |
| `authentication.schemeName` | `payerAuthentication.scheme` |
| `authentication.protocolVersion` | `payerAuthentication.protocolVersion` |
| `authentication.challengeIndicator` | `payerAuthentication.challengeIndicator` |
| `authentication.cavv` | `payerAuthentication.authenticationValue` (null maps through as null) |
| `authentication.psd2ScaExemptionCode` | `payerAuthentication.psd2ScaExemption` |
| `order.browserData` | `legacyOrderData.browser` |
| `order.ipAddress` | `legacyOrderData.ipAddress` |
| `order.referenceOrder` | `legacyOrderData.referenceOrder` |
| `merchantWsapiId` | `merchant.merchantId` |
| `order.merchantName` | `merchant.name` |
| `order.merchantCategoryCode` | `merchant.categoryCode` |
| `orderWsapiId` | `order.orderId` |
| `order.currency` | `order.currency` |
| `order.amountMinor` | `order.amountMinor` |
| `order.customerReference` | `order.customerReference` |
| `order.billingCountry` | `order.billingCountry` |
| `order.shippingCountry` | `order.shippingCountry` |
| `order.fundingMethod` | `order.funding.method` |
| `order.cardNumber` | `order.funding.cardNumber` |
| `order.cardBrand` | `order.funding.cardBrand` |

The mapping is 1:1. No field is computed, derived, defaulted or enriched on the modern side.

## Domain behavior

- A live `authenticatePayer` response is **persisted by the legacy platform**, keyed by
  correlation id, with a **short TTL (~10 minutes)**.
- The modern retrieval path consumes that **stored** response. It is **observational only**: it
  must not alter the live outcome and must not re-call the provider (Scientist-Pattern-Testing
  design constraint).
- `authenticationOrigin` distinguishes transactions the gateway authenticated **internally**
  (`INTERNAL`) from **externally authenticated** ones (`EXTERNAL`).

## DOES / DOES NOT

**DOES**

- Return the stored authentication result, exactly as stored, read-only.
- Return nothing when no record matches the identifiers.
- Hold the authoritative authentication outcome — it is the system of record.

**DOES NOT / FORBIDDEN on the retrieval path**

- **DOES NOT call `authenticatePayer` on the retrieval path — Authenticate Payer is a billable
  event and must never be called a second time.** Not to refresh a stale record, not to fill a
  null CAVV, not "just in case". A retrieval that triggers `authenticatePayer` has spent money
  and has touched a live transaction outcome.
- Does not repair, enrich or back-fill stored records.
- Does not expose externally authenticated transactions as if they were internally
  authenticated.

## Allowed / forbidden changes

- **You do not edit `target-pass-proxy`.** It is not in this workspace and is not yours.
- The modern service must **proxy and map**. It must not reimplement authentication logic, must
  not recompute an authentication outcome, and must not build a local source of truth.
- Inside `boost-authentication-service`, `LegacyPassClientStub` is this edge's stand-in. Treat it
  as the legacy edge: do not change its behaviour to make your code pass.

## Source paths (illustrative)

LAB FIXTURE — representative paths in the real repository, for orientation only:

```
target-pass-proxy/
  src/main/java/com/mastercard/target/pass/retrieval/AuthenticationResultRetrievalService.java
  src/main/java/com/mastercard/target/pass/auth/AuthenticatePayerService.java      # billable
  src/main/java/com/mastercard/target/pass/store/StoredAuthenticationRepository.java
  src/main/resources/schema/pass-authentication-record.xsd
```

## Freshness / version metadata

| Field | Value |
|---|---|
| Contract version | 1.0.0 |
| Generated | 2026-08-16 |
| Source revision | `target-pass-proxy@rel-2026.07` |
| Compression tier | 1 |
| Regenerate when | the legacy retrieval contract changes, a field becomes nullable, or the billable-operation list changes |
