# TDD log — Retrieve Payer Authentication Results (PGSE-88)

One entry per issue from `issues.json`. The failing test comes first; the implementation follows.
Reference copy — a learner's log will differ in wording and timestamps, not in shape.

| # | Issue | Test written first | Observed RED | Implementation | Observed GREEN |
|---|---|---|---|---|---|
| 1 | Complete the legacy mapping | `RetrievalMappingTest.completeStoredRecordMapsOntoTheFullAggregate` | `No value at JSON path "$.legacyOrderData.browser"` | `LegacyResponseMapper` maps all four blocks | 200 with every block populated |
| 2 | Error semantics | `ErrorSemanticsAndScopeTest` (404 / 403 / 400) | missing record returned 200 with an empty body; unauthorized caller returned 404; malformed id returned 200 | `MalformedRequestException`, `AuthenticationRecordNotFoundException`, corrected `ApiExceptionHandler` | 404 / 403 / 400 distinct |
| 3 | Externally authenticated out of scope | `ErrorSemanticsAndScopeTest.externallyAuthenticatedTransactionIsNotServed` | `expected:<404> but was:<200>` — the EXTERNAL record was served as if internal | service serves only `INTERNAL` records | 404 |
| 4 | Tracing headers | `RetrievalMappingTest.tracingHeadersArePropagatedBackToTheCaller` | `Response header 'X-Mc-Correlation-Id' expected:<corr-abc-123> but was:<null>` | controller collects the five headers; service carries the correlation id into the legacy query; headers echoed | headers propagated and echoed |
| 5 | No sensitive data in logs | `NoSensitiveDataInLogsTest` | `PAN found in logs/auth-service.log` | the retrieval path logs the authentication transaction id only | log sink clean |
| 6 | Read-only retrieval | `NoSecondAuthenticatePayerCallTest`, `NoBillableCallThroughLegacyStubTest` | `Wanted but not invoked… actually, there were 1 interactions` — `authenticatePayer` was called once for the incomplete record, and the stub's billable-call counter read 1 | the refresh branch is removed; the stored record is returned as-is | `authenticatePayer` never invoked; counter 0 |
| 7 | Consumer wiring | `OrderAuthenticationLookupTest` | tracing headers were not passed to the client | `OrderAuthenticationLookup` passes them through; the client maps 404 to "no result" | both consumer tests green |

## Note on issue 6

The test for issue 6 asserts a **negative**: that a billable operation is never invoked. Nothing
about the draft's behaviour is visibly wrong — it returns 200, the happy-path tests stay green,
and the mock/stub for `authenticatePayer` succeeds. Written after the fix, this test would have
passed on the first run and proved nothing. Written first, it is RED for exactly one reason.
