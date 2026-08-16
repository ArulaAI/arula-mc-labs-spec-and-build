# Plan — Retrieve Payer Authentication Results (PGSE-88)

Derived from `specs/retrieve-payer-auth.spec.md` (READY). Seven issues, ordered; each issue can
assume the previous ones are complete, and each names the repo it touches.

**No GitHub issues were created.** `issues.json` and this plan are local files — see
`LAB_ACTION_GUIDE.md` Stage 3.

| # | Issue | Repo | ACs |
|---|---|---|---|
| 1 | Map the stored legacy record onto the full response aggregate | `boost-authentication-service` | AC-1 |
| 2 | Return 404, 403 and 400 as distinct outcomes | `boost-authentication-service` | AC-4, AC-5, AC-6 |
| 3 | Keep externally authenticated transactions out of scope | `boost-authentication-service` | AC-7 |
| 4 | Propagate the tracing headers across the hop | `boost-authentication-service` | AC-8 |
| 5 | Stop writing sensitive data to the log sink | `boost-authentication-service` | AC-2 |
| 6 | Make retrieval read-only: never invoke Authenticate Payer | `boost-authentication-service` | AC-3 (AC-INCOMPLETE) |
| 7 | Wire the consumer against the shared contract | `boost-order-processing` | AC-9 |

## Repo boundary

The producer work (issues 1–6) is entirely inside `boost-authentication-service`. The consumer
work (issue 7) is entirely inside `boost-order-processing`. The two repos meet at exactly one
place: `openapi/payer-authentication-v1.yaml`, which is byte-identical in both and is the
agreement between them. `ContractConsumerTest` fails if the copies drift.

`target-pass-proxy` is touched by no issue. It is not in this workspace and is not ours to edit;
`.claude/context/target-pass-proxy.context.md` is the authority on its behaviour, and
`LegacyPassClientStub` is its stand-in inside the producer repo.

## Ordering rationale

1–5 are the visibly unbuilt work: an incomplete mapping, wrong status codes, no scope guard, no
header propagation, a log line that leaks. 6 is different in kind — from the outside the
incomplete-record path already "works": it returns 200, the tests are green, and the only trace
of the problem is on the provider's invoice. It is its own issue precisely so it cannot be
absorbed into "finish the mapping".

7 is the consumer side and depends on the producer's error semantics (issue 2) being settled.

## Notes

- Issue 6 is the criterion AC-3 (AC-INCOMPLETE) makes testable. Its test asserts a negative —
  that `LegacyPassClient.authenticatePayer` is never invoked — so it must be written before the
  fix, or it proves nothing.
- No issue adds caching, retries or authentication-value format validation; all three are
  declared out of scope by the spec.
