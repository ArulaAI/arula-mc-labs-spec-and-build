# Lab 2 — Facilitator key

**FACILITATOR ONLY. Do not distribute. Do not read aloud before the stage it belongs to.**

Thread `PGSE-88` Retrieve Payer Authentication Results · 120 minutes · two owned repos plus a
compressed-context-only legacy edge.

---

## 1. The centrepiece, in one paragraph

`PayerAuthenticationService.retrieve(...)` in the inherited draft contains this branch:

```java
if (stored.authentication().cavv() == null) {
    // The stored record came back without an authentication value. Fill the gap from
    // the provider so callers always get a complete result.
    stored = legacyPassClient.authenticatePayer(new AuthenticatePayerCommand(...));
}
```

It is a good instinct, written by a competent engineer before the read-only rule was settled. It
is also a **second billable Authenticate Payer on every incomplete record**. Nothing fails.
`LegacyPassClientStub.authenticatePayer` succeeds, returns a plausible refreshed record, and
increments a counter — exactly like the real operation, whose only visible trace is an invoice.
The happy-path tests exercise complete records, so they stay green.

This is **seeded and static**: it is in the code from minute one for every group, never a product
of what codegen happens to generate.

**Do not reveal this before Stage 5.**

---

## 2. Seeded traps and decoys

| ID | Where | Seeded behaviour | Source | Failure mode | Discovery | Correct end state |
|---|---|---|---|---|---|---|
| **T1** | `PayerAuthenticationService`, incomplete-record branch | calls `authenticatePayer` to "refresh" a null CAVV — silent second billable call | spec-pack: "Authenticate Payer is a billable event… must never cause a second authentication"; SPT note | Incorrectly solving the right problem | `code-to-spec-validator` (Stage 5) + `NoSecondAuthenticatePayerCallTest` (RED) | stored record returned as-is; `authenticatePayer` never invoked |
| **T4** | `PayerAuthenticationService` INFO log | logs the whole legacy record — CAVV, PAN, customer reference — to `logs/auth-service.log` | spec-pack: "no authentication value, PAN or PII written to logs" (non-negotiable) | Sensitive-data leak | own eyes (open the log), the PAN gate, `NoSensitiveDataInLogsTest` | log the authentication transaction id only |
| **T5** | `ApiExceptionHandler` + the null return path | missing record → **200 with an empty body**; unauthorized caller → **404** | spec-pack 404/403/400 semantics | correctness | validator + tests | 404 / 403 / 400 distinct and correct |
| **T2** | endpoint scope (latent, not seeded as code) | the draft has no origin check, so an `EXTERNAL` stored record is served as if internal; the opposite risk is a group *building* external-auth support | spec-pack / epic: externally authenticated out of scope | Correctly solving the wrong problem | validator + spec read | `EXTERNAL` → 404; no external-auth code path added |
| **T3** | service / mapper (latent) | temptation to recompute the authentication outcome locally instead of proxying | spec-pack: "proxies to legacy; system of record" | Invented dependency / reimplementation | validator + `pr-reviewer` | proxy and map only |

**Seeded records in `LegacyPassClientStub`:**

| Order / auth txn | State |
|---|---|
| `ORD-1001` / `AUTH-9001` | complete, `INTERNAL` — the happy path |
| `ORD-1002` / `AUTH-9002` | **incomplete** (`cavv` null), `INTERNAL` — the trap fires here |
| `ORD-1003` / `AUTH-9003` | complete, `EXTERNAL` — out of scope |
| anything else | no record — the 404 case |

**Decoys the room should reject, with the reason:**

- *"Cache the legacy result to avoid repeat calls."* Plausible, but caching a billable
  authentication result carries its own compliance question and the spec asks for retrieval of
  the stored result, not a cache.
- *"Add a retry to the legacy retrieve call for resilience."* Harmless-sounding, out of scope,
  and it risks masking the 404 semantics the spec is explicit about.
- *"Validate the CAVV format."* Sounds security-minded. The service is a read-only proxy, not a
  validator of the system of record's data. The spec does not ask for it.

Rejecting a decoy uses the same muscle as catching T1.

---

## 3. Red / green checkpoints

| Point | Expected |
|---|---|
| Baseline, both repos | `mvn test` **green**, `mvn verify` **green** (no seeded layering violation in Lab 2 — ArchUnit is carryover governance and stays green) |
| Baseline behaviour | complete record → 200 mapped; **incomplete record → 200, and the stub's `authenticatePayer` counter reads 1** |
| Baseline log sink | `logs/auth-service.log` contains the PAN and the CAVV after any retrieval |
| Starter spec gate | `validate_spec.py` → `valid:false`, naming the missing `## Non-Negotiables` section and the non-testable `AC-3` |
| Stage 4 | the tests the group wrote are green; T1 usually — **not certainly** — still latent |
| Stage 5 | validator **FAIL** on the no-re-call criterion in the common case |
| Stage 6 | `mvn verify` green in both repos; log sink clean; PR artifact written only after the gates go green |

---

## 4. The two-case fallback at Stage 5

If the validator returns **PASS**, there are two very different reasons. Handle them the same way
operationally; explain them differently to the room.

**Case (a) — the trap is still in the code and the validator missed it.** Re-run pointed at it:

> "Check specifically the incomplete-stored-record branch of `PayerAuthenticationService`: does it
> call `LegacyPassClient.authenticatePayer` (or any provider re-authentication)? The spec forbids
> any second Authenticate Payer call — it is billable. Report the exact line."

**Case (b) — the group's own Stage 4 TDD already found and fixed it.** That is a legitimate win,
not a lab failure. Say so, out loud: this is exactly what tests written from acceptance criteria
are supposed to do. Stage 5 still validates T2–T5 against the rest of the spec.

**Telling them apart.** A green `NoSecondAuthenticatePayerCallTest` tells you the code is correct
*now*; it tells you nothing about *when*. Check `docs/tdd-log.md` and `git log` in
`boost-authentication-service` — if the fix predates the Stage 5 validator run, it is case (b).

**Deterministic backstop.** Either way, `NoSecondAuthenticatePayerCallTest` proves the point: RED
on the seeded draft (`authenticatePayer` invoked once), GREEN once corrected. The teaching moment
never depends on one probabilistic pass.

---

## 5. Expected discovery sequence

1. Stage 2 — the group closes the spec gaps. Whether they make the billable-call constraint
   *testable* or leave it as prose is the stage's real gate, and the strongest predictor of what
   happens in Stage 5.
2. Stage 3 — a good plan makes read-only retrieval its own issue. A weaker plan folds it into
   "finish the mapping", where it disappears.
3. Stage 4 — most groups spend the whole block on the visibly unbuilt work: mapping, headers,
   error codes. The incomplete-record path has no outward symptom, so there is no natural reason
   to look at it. That, not any instruction, is what usually carries T1 into Stage 5.
4. Stage 5 — the fresh-context validator reads AC-3 and finds the branch.
5. Stage 6 — the PR gate physically refuses the write while a gate is red.

---

## 6. Timing

15 · 15 · 20 · 12 · 25 · 12 · 21 = 120 minutes.

Stage 4 and Stage 6 are the two most likely to run long. If Stage 4 overruns, do **not** extend it
by cutting Stage 5 — Stage 5 is the lab. Restore `reference/stage4-tests/` for the group that is
behind and move on. If Stage 6 is tight, drop the second `pr-reviewer` pass, never the PR-gate
demonstration.

---

## 7. Recovery procedure

```bash
export WORKBENCH_FACILITATOR=1
# copy the needed stage folder from .claude/reference/ into the group's tree
unset WORKBENCH_FACILITATOR
```

`reference_guard.py` denies a learner session any access to `.claude/reference/`. See
`.claude/reference/README.md` for the per-stage restore map.

---

## 8. Workbench gaps you may hit live

| Gap | What you will see | What to do |
|---|---|---|
| `repo-context-compressor` does not exist | Stage 1's prompt has nothing to invoke | Hand out `reference/stage1-context/target-pass-proxy.context.md`. The reading and the human gate are unchanged. |
| `spec-craft` needs the `superpowers` companion | `/spec` hard-stops | Confirmed before session day; there is no live workaround. Fallback: drive the interview manually and run `validate_spec.py` directly — Stage 2 still reaches a deterministically validated spec. |
| `work-orchestrator` shells out to `gh` | an unhandled `gh` failure could crash the pipeline | The Stage 3/4/6 prompts forbid `gh` explicitly. If a group's run tries it anyway, stop the run, restate the constraint, and continue with local files. |
| plugin lint/coverage gates are ruff/pytest | they report "skipped" on Java | Expected. Verification is Maven-native. The plugin contributes the PAN/secret scan only. |
| plugin PAN gate is blind to the two repos | it scans `git diff HEAD` at the workspace root | The lab-local `pan_gate.py` covers it; it scans the pending write. |

---

## 9. Do not reveal early

- That the trap is the **incomplete-record branch** of `PayerAuthenticationService`.
- The exact wording of the completed AC-3 (AC-INCOMPLETE) — that is the answer to Stage 2's gate.
- The rejection reasons for the three decoys.
- That `ORD-1002 / AUTH-9002` is the record that triggers the billable call.

---

## 10. Closing recap for the room

A good spec plus fresh-context judgment turned a plausible, money-costing implementation into a
trusted one. The tests were green the whole time. The spec is what made the difference — and it
only made a difference because someone wrote the billable-call constraint as something a test
could assert.
