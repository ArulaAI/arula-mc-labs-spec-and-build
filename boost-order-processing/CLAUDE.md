# CLAUDE.md — boost-order-processing

Guidance for an AI coding agent working in this PGS Java/Spring Boot service.

**Where this fits.** Repo tier. Org-wide Mastercard standards and MPGS team conventions come from
higher tiers; this file adds only what is specific to this repo.

## What this codebase is

Order processing. In this feature it is the **consumer** of the Retrieve Payer Authentication
Results API (PGSE-88): for an order the gateway authenticated internally, it asks
`boost-authentication-service` for the stored authentication result.

Deliberately minimal in this lab — the work here is the cross-repo wiring, not new business
logic.

## Our stack

- Java 17 (target), Maven, Spring Boot 3.5.x, JUnit 5 + Mockito, Log4j2 via SLF4J.
- No Docker, no Kafka, no live inter-service HTTP during the lab, no CI.

## The repo boundary

- The producer is `boost-authentication-service`, a separate repo in this workspace.
- `src/main/resources/openapi/payer-authentication-v1.yaml` is **the same contract file the
  producer publishes**. It is the agreement between the two repos. `ContractConsumerTest` fails
  if the two copies drift apart or if the contract drifts from the DTOs we bind to.
- Do not reach into the producer's source to work out what it returns. Read the contract.

## Non-negotiables (do not violate these)

1. **Never log sensitive data.** The retrieval response carries CAVV, PAN and PII. Do not log the
   response object, and do not echo it into an error.
2. **Correlation IDs end to end.** Every inbound tracing header is propagated across the hop to
   the authentication service. Values are propagated, never logged.
3. **No hardcoded secrets, URLs or endpoints.** The producer's base URL comes from configuration.
4. Treat the producer's `404` as "no stored result", not as a transport failure.

## How to work

- Surgical changes; the minimum code that satisfies the acceptance criterion.
- Write the failing test first from the acceptance criterion, then make it pass.
- Do not implement the producer's behaviour here. This repo consumes; it does not proxy or
  reimplement authentication.
