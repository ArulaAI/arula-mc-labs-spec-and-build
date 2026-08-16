# CLAUDE.md — boost-authentication-service

Guidance for an AI coding agent working in this PGS Java/Spring Boot service.

**Where this fits.** Repo tier. Org-wide Mastercard standards and MPGS team conventions come from
higher tiers; this file adds only what is specific to this repo. When the guardrails and a
specific instruction file disagree, the guardrails win. Feature-specific rules live in
`specs/NON_NEGOTIABLES.md` and in the spec itself.

## What this codebase is

The modern Retrieve Payer Authentication Results API (PGSE-88). It is a **read-only proxy** in
front of the legacy Target/PASS platform, which is the system of record. Order Processing calls
it for transactions the gateway authenticated internally.

Correctness, security and traceability outrank speed. Every change touches cardholder data or
the paths around it. When in doubt, stop and ask. Do not guess.

## Our stack

- **Language:** Java 17 (target). Zulu 21 JDK compiles to the Java 17 target.
- **Build:** Maven. Gradle is not a PGS standard — no `./gradlew`.
- **Framework:** Spring Boot 3.5.x, Spring Framework 6.2.
- **APIs:** REST/JSON, OpenAPI-first contracts. The contract for this service is
  `src/main/resources/openapi/payer-authentication-v1.yaml` and it is **shared with
  `boost-order-processing`** — a change to the response shape is a change to both repos.
- **Testing:** JUnit 5 + Mockito (unit), ArchUnit 1.2.1 (architecture rules), JaCoCo (coverage).
- **Logging:** Log4j2 via SLF4J.
- **Not here:** no Docker, no Kafka, no live inter-service HTTP, no CI in this lab.

## The repo boundary

- `target-pass-proxy` — the legacy edge — is **not in this workspace**. Everything you may rely
  on about it is in `.claude/context/target-pass-proxy.context.md`. If a fact you need is not in
  there, stop and say so; do not invent legacy behaviour.
- `LegacyPassClientStub` is the legacy edge's stand-in inside this repo. Do not change its
  behaviour — changing it changes the system of record, not this service.
- `boost-order-processing` consumes the OpenAPI contract above. Do not change the agreed response
  shape unilaterally.

## Non-negotiables (do not violate these)

1. **Never log sensitive data.** No CAVV, PAN, PII, keys, credentials or tokens in logs. Do not
   log request or response objects. Sanitise before logging.
2. **Retrieval is read-only, and Authenticate Payer is billable.** The retrieval path must never
   invoke the legacy Authenticate Payer operation — see `specs/NON_NEGOTIABLES.md` §3.
3. **Correlation IDs end to end.** Propagate every inbound tracing header across the hop; never
   log the values.
4. **No hardcoded secrets, URLs or endpoints.** Read them from configuration.
5. **Deny by default** at every interface, including internal callers.

## Architecture and code shape

- **Layering:** `api` (HTTP concerns only) → `service` (business logic) → `client` (the legacy
  edge) / `mapper` / `security`. `api` must not depend on `client`; `LayeringArchTest` enforces
  this and blocks `mvn verify`.
- **Error handling:** global, consistent responses via `@RestControllerAdvice`. Distinguish
  400 / 403 / 404. Never leak internal details or payload contents to the caller.
- **Config is externalised** in `application.yml`; nothing environment-specific in code.

## How to work

1. **Think before coding.** State assumptions. If several interpretations exist, present them
   instead of silently choosing one.
2. **Simplicity first.** The minimum code that satisfies the acceptance criterion. No speculative
   features, no abstractions for single-use code.
3. **Surgical changes.** Touch only what the issue needs. Do not refactor adjacent code.
4. **Goal-driven execution.** Turn the acceptance criterion into a failing test first, then make
   it pass.

## Working with specs

- The spec is the source of truth. Implement its in-scope items; respect its out-of-scope list.
- When the spec is thin or silent, **stop and enumerate the missing decisions** and ask. Do not
  pick a default silently.
- Do not invent dependencies, libraries or endpoints.

## Self-check before you hand back

- Did I log anything sensitive? (Must be no — including the legacy record and the response.)
- Can any path from a retrieval request reach `LegacyPassClient.authenticatePayer`? (Must be no.)
- Did I validate and authorise every inbound request at this service?
- Did I stay inside the spec's scope, and flag anything it left undecided?
- Are 400 / 403 / 404 distinct and correct?
- Does the response still match `payer-authentication-v1.yaml`?
