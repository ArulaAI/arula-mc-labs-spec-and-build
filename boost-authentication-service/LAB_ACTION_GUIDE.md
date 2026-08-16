# Lab 2 — The Call You Must Not Make Twice

**Thread:** `PGSE-88` Retrieve Payer Authentication Results (AFR domain) · **Level:** 200 ·
**Duration:** 120 minutes · **Topology:** two owned repos plus a legacy edge you cannot see

---

## The scenario

Refunds shipped. Order Processing now needs payer authentication results for transactions the
gateway authenticated **internally**. Boost does not have that capability yet — legacy
**Target/PASS** is still the system of record, and it is **not in your workspace**.

A squad member scaffolded a first-pass draft of the modern endpoint in
`boost-authentication-service` before the spec was locked. Complete-record retrieval works and
the tests are green. You are finishing it, spec-first, across two repos.

> **Authenticate Payer is a billable event. This API retrieves. It never re-authenticates.**

**Your role:** the engineer finishing the inherited draft.

**What you are building:** a read-only proxy that returns
`PayerAuthenticationWithOrderDetails`, honours the tracing headers and 404/403/400, logs nothing
sensitive, and never triggers a second Authenticate Payer — plus the consumer wiring in
`boost-order-processing`.

---

## Workspace setup

You open Claude Code **once, at the workspace root** — the directory that contains both repos:

```
lab2-payer-auth/                  <- open Claude Code HERE
  .claude/                        shared lab config for the whole workspace
    context/                      the compressed context you produce in Stage 1 lands here
  boost-authentication-service/   owned repo — the producer, where the work lives
  boost-order-processing/         owned repo — the consumer
  journey/                        created at runtime by the plugin's journey hooks
```

`target-pass-proxy`, the legacy edge, is **not here**. It is represented only by a compressed
context artifact. That is the point of Stage 1.

Do not open a single repo as the project root — the shared `.claude/`, the hooks and the grader
all resolve from the workspace root.

### Prerequisites

- JDK 17 (Zulu 21 is fine; the compile target is 17) and Maven 3.9+
- Python 3.11+ with PyYAML (`pip install pyyaml`)
- Claude Code with the `workbench` plugin **and its `superpowers` companion** installed
- No Docker, no Kafka, no CI, no network at runtime. The legacy edge is a local stand-in.

### Preflight (before the session starts)

1. `java -version` → 17.x or 21.x · `mvn -version` → 3.9+
2. Pre-warm the Maven cache once per machine:
   `cd boost-authentication-service && mvn -q -o dependency:go-offline` (and the same in
   `boost-order-processing`).
3. Open the **workspace root** in Claude Code. Confirm these resolve: `/spec`, `/build`, `/lab`,
   `/hand-off`, `/grade`, and the `planner`, `pr-reviewer` and `code-to-spec-validator` subagents.
4. **Harness liveness:** run `/lab`, then confirm a journey event actually landed in `journey/` —
   not just that the command exited cleanly.
5. `cd boost-authentication-service && mvn test` → GREEN. Same in `boost-order-processing`.

Two go/no-go checks the facilitator confirms **before session day**, because there is no live
workaround: the `superpowers` companion plugin is installed (`spec-craft` hard-stops without it),
and `repo-context-compressor` is available — or the facilitator is ready to hand out the
reference compressed context at Stage 1.

---

## What is already true when you start

- `mvn test` is **green** in both repos.
- Retrieval of a **complete** stored record works and returns 200.
- Genuinely unbuilt: the rest of the response mapping, the tracing headers, and the error codes.
- The spec is **incomplete** and `/build` will refuse to run against it.

---

## Stage 0 — Ground: specs, the pipeline, and the context blind spot (15 min)

**Objective.** Shared vocabulary and a confirmed-working harness. No code.

**Action.** Facilitator-led. Three things, building on Lab 1 rather than repeating it:

1. What makes a spec **buildable** rather than a conversation: named sections, and acceptance
   criteria that a test can be written from.
2. Why `/build` refuses an unvalidated spec — the gate is structural, not cultural.
3. **The context-window blind spot.** An agent starts guessing the moment work crosses into a
   repo it cannot see. `target-pass-proxy` is that repo.

**Commands.** `/lab` · confirm a journey event landed in `journey/`.

**Human gate.** Everyone's harness is live.

**Failure / recovery.** No journey event → the plugin is not installed, or a subfolder was opened
instead of the workspace root. Fix before Stage 1; nothing downstream is gradeable without it.

**Close the stage.** `/hand-off`

**Invariant.** Harness live; the room can say why Stage 1 exists.

---

## Stage 1 — Compress the legacy edge (15 min)

**Objective.** A usable Tier-1 compressed context for `target-pass-proxy`.

**Start state.** `.claude/context/` is empty. Nothing in your workspace tells you what the legacy
edge does.

**Surface.** `repo-context-compressor` (see the note below).

**Prompt.**

> "Generate a compressed context for the `target-pass-proxy` legacy edge for use by
> `boost-authentication-service`. Include: identity/purpose, the retrieve and authenticatePayer
> operations, request/response contracts, the legacy→modern field map, the stored-response/TTL
> behavior, and an explicit DOES / DOES-NOT section stating that the retrieval path must never
> call authenticatePayer (billable). Write `.claude/context/target-pass-proxy.context.md`."

**If the compressor skill is not installed**, the facilitator hands you the artifact instead.
Reading it is the part of this stage that matters.

**Artifact.** `.claude/context/target-pass-proxy.context.md`

**Observable.** The artifact names two operations, not one — and says explicitly that one of them
must never be called from the retrieval path.

**Human gate.** Read the DOES / DOES NOT section aloud. Confirm the no-re-call fact is there. You
will need it in Stage 2, and an agent will need it in Stage 4.

**Failure / recovery.** `reference/stage1-context/` — the facilitator restores it.

**Close the stage.** `/hand-off`

**Invariant.** The compressed context exists and contains every required section, including the
explicit "DOES NOT call authenticatePayer" statement.

---

## Stage 2 — Author and validate the spec (20 min)

**Objective.** `specs/retrieve-payer-auth.spec.md` reaches READY.

**Start state.** The starter spec is inherited from the Solution Intent and is **incomplete**.
Run the validator yourself first and look at what it says:

```bash
cd boost-authentication-service
python3 "$CLAUDE_PLUGIN_ROOT/skills/spec-craft/scripts/validate_spec.py" specs/retrieve-payer-auth.spec.md
```

It reports NOT READY, names the missing section and the untestable acceptance criterion, and
writes `specs/retrieve-payer-auth.spec.status.json` with `"valid": false`.

**Surface.** `/spec` (the `spec-craft` skill).

**Prompt.**

> "/spec Complete `specs/retrieve-payer-auth.spec.md` for Retrieve Payer Authentication Results
> (`PGSE-88`), bound by `specs/NON_NEGOTIABLES.md` and
> `.claude/context/target-pass-proxy.context.md`. Add the missing Out-of-scope section
> (externally-authenticated transactions are out of scope), the 404/403/400 error semantics as
> distinct acceptance criteria, and replace the vague incomplete-record criterion with a testable
> one: the service returns the stored result as-is and never invokes the legacy Authenticate
> Payer operation. Make every acceptance criterion testable."

**Artifacts.** the completed spec · `retrieve-payer-auth.spec.status.json` with `"valid": true`

**Observable.** `spec.status.json` moves `valid:false` → `valid:true`; the missing section and
the untestable criterion are both gone.

**Human gate — the one that matters in this stage.** Read the finished spec yourself. Confirm the
billable-call constraint landed as a **testable criterion** — something a test can assert — and
not as prose in a paragraph. "The service should not re-authenticate unnecessarily" is prose. A
criterion that says the legacy Authenticate Payer operation is **never invoked** is a test.

**Failure / recovery.** `/build` will refuse until the spec is READY. Recovery:
`reference/stage2-spec/`.

**Close the stage.** `/hand-off`

**Invariant.** Spec READY; the incomplete-record criterion, the out-of-scope declaration and the
404/403/400 semantics are all present and testable.

---

## Stage 3 — Plan: spec to issues (12 min)

**Objective.** A small ordered issue set that names repo boundaries.

**Surface.** `/build` (the `work-orchestrator` skill). It is **one command** — it plans first and
stops at the plan gate. There is no separate plan-only command.

**Prompt.**

> "/build using `specs/retrieve-payer-auth.spec.md`. First break it into a small ordered set of
> issues, each with its own acceptance criteria, and for each issue name which repo it touches
> (`boost-authentication-service` producer work vs. `boost-order-processing` consumer wiring).
> Write `issues.json` and `docs/plans/plan.md` **as local files only — do NOT run
> `gh issue create` or create any GitHub issue.** Stop at the plan gate for review."

**Artifacts.** `issues.json` · `docs/plans/plan.md` — both local files.

**Human gate.** Are the boundaries right? Which issues are producer work and which are consumer
work? Is the read-only retrieval behaviour **its own issue**, or is it buried inside "finish the
mapping"?

**Failure / recovery.** `reference/stage3-plan/`.

**Close the stage.** `/hand-off`

**Invariant.** Issues are ordered; each names its repo; no GitHub issue was created.

---

## Stage 4 — TDD and correct the draft (25 min · the largest block)

**Objective.** Failing tests first, then working code, across both repos.

**Surface.** the paused `/build` run. In this lab you write the tests **directly from the
acceptance criteria** — `sdet-architect` arrives in Lab 3.

**Prompt.**

> "Continue `/build` per issue from `issues.json`. For each issue: write the failing tests first
> from its own acceptance criteria, then make them pass. Complete `LegacyResponseMapper` and the
> consumer wiring, honour the tracing headers and 404/403/400. Do not implement
> externally-authenticated handling. Do not run any `gh` command."

**Artifacts.** implementation in both repos · `docs/tdd-log.md` (one row per issue: the test you
wrote first, the RED you observed, the change that turned it green)

**Live traps.** The agent will offer to cache the legacy result, or to add a retry to the legacy
retrieve call, or to validate the format of the authentication value. All three are grounded,
plausible and **out of scope** — the spec asks for retrieval of the stored result, nothing more.
Reject them with a reason.

**Human gate.** Each issue's tests are green before you move to the next one.

**Failure / recovery.** `reference/stage4-tests/`.

**Close the stage.** `/hand-off`

**Invariant.** Both repos compile; the tests you wrote are green; `docs/tdd-log.md` shows
tests-first.

---

## Stage 5 — Validate against spec, fresh context (12 min)

**Objective.** The validator catches what the tests missed.

**Surface.** `code-to-spec-validator` — a subagent with **fresh context**. It receives only the
spec, the issue, the diff, and the compressed context. It never sees your session, your
reasoning, or your own review.

**Prompt.**

> "Validate the diff for each issue against `specs/retrieve-payer-auth.spec.md` and
> `.claude/context/target-pass-proxy.context.md`. Confirm: retrieval is read-only; the legacy
> Authenticate Payer operation is never invoked (including on the incomplete-record branch);
> externally-authenticated transactions are out of scope; 404/403/400 are correct; no CAVV/PAN/PII
> is logged. Return PASS or FAIL with the specific criterion and line for any failure. You did not
> write this code."

**Artifact.** `docs/validation-log.md` — the verdict per issue, the criterion, and what you did.

**Observable.** A FAIL naming a specific acceptance criterion and a specific line.

**On FAIL.** Go back to Stage 4 and make the **smallest** fix that satisfies the criterion. Add
the test that proves it — a test asserting the criterion, written before the fix. Then
re-validate.

**Human gate.** Every FAIL is either fixed or explicitly accepted with a recorded reason.

**Failure / recovery.** `reference/stage5-validation/`.

**Close the stage.** `/hand-off`

**Invariant.** The validator ran with fresh context; every finding is resolved or recorded;
`docs/validation-log.md` exists.

---

## Stage 6 — Review, gates, ship and close (21 min)

**Objective.** A gated PR artifact and a closed trail.

**Actions, in order.**

1. **Fresh-context review.** Run `pr-reviewer` over the full change:

   > "Review the full diff for `PGSE-88` against `rules/coding-standards.md` and
   > `specs/NON_NEGOTIABLES.md`. You are not the author. Return APPROVE / REQUEST CHANGES /
   > BLOCKER with `file:line` findings."

2. **Try the PR gate early — on purpose.** Before the gates are green, ask the session to write
   `docs/PR_DESCRIPTION.md`. The write is **denied** by a `PreToolUse` guard, which tells you
   which gate is red. Watch the control fire. This is the lesson: the gate is structural.

3. **Close the gates.** `mvn verify` in **both** repos — tests, the ArchUnit layering rule,
   JaCoCo, the consumer contract test — and confirm the log sink carries no CAVV, PAN or PII.

4. **Write the PR description** to `boost-authentication-service/docs/PR_DESCRIPTION.md`: the
   spec link, validator notes, reviewer notes and gate results.

   > "Write the PR description to `docs/PR_DESCRIPTION.md`. Do not run `gh pr create` or push."

5. **Close the trail.** Run this stage's `/hand-off` **before** `/grade`, so all seven boundary
   events are in the journey. Then `/grade`.

**Artifacts.** `docs/PR_DESCRIPTION.md` (a local file — there is no GitHub PR in this lab) ·
`docs/workflow-tracker.md` with seven entries · the grade card.

**Human gate.** The PR artifact exists only because the gates are green.

**Failure / recovery.** `reference/stage6-solution/`.

**Invariant.** `mvn verify` green in both repos; `docs/PR_DESCRIPTION.md` written only after the
gates went green; nothing sensitive in any log; no externally-authenticated handling; no GitHub
issue or PR created.

---

## Where each artifact goes

Paths are what the grader and the gates look at. Everything below is relative to the workspace
root.

| Stage | Artifact |
|---|---|
| 1 | `.claude/context/target-pass-proxy.context.md` |
| 2 | `boost-authentication-service/specs/retrieve-payer-auth.spec.md` + `…spec.status.json` |
| 3 | `boost-authentication-service/issues.json` · `boost-authentication-service/docs/plans/plan.md` |
| 4 | tests in each repo's `src/test/java/…` · `boost-authentication-service/docs/tdd-log.md` |
| 5 | `boost-authentication-service/docs/validation-log.md` |
| 6 | `boost-authentication-service/docs/PR_DESCRIPTION.md` · `boost-authentication-service/docs/workflow-tracker.md` |
| every stage | a `hand-off` event in `journey/*.jsonl` |

## Grading

Two layers, both reproducible.

**Layer A — journey completeness** (`/grade`, the plugin `lab-grader` against
`.claude/rubrics/lab-2.yaml`): did you move through the stages, and did the audit trail stay free
of sensitive data? It proves progress, not correctness.

**Layer B — repo state and behaviour**:

```bash
python3 .claude/scripts/grade_repo.py        # from the workspace root
```

Twenty deterministic checks on content and behaviour, not file existence — the compressed context
is complete, the spec's gaps are closed, the billable-call constraint is testable *and* green, no
path from a retrieval reaches the provider, nothing sensitive is in the log sink, the contract
holds across the repo boundary, and the seven stage boundaries are in the journey. It also runs
an anti-gaming probe: a known-wrong implementation is dropped into a temporary copy, and your
test must **fail** against it. A deleted or weakened test cannot pass this.

---

## What you leave with

- A READY spec whose no-second-billable-call constraint is a **testable** criterion.
- A read-only retrieval endpoint that proxies to the legacy edge, maps to
  `PayerAuthenticationWithOrderDetails`, honours the tracing headers and 404/403/400, logs nothing
  sensitive, and never re-authenticates — plus the consumer wiring and contract test.
- The evidence: compressed context, spec + status, `issues.json`, `plan.md`, `tdd-log.md`,
  `validation-log.md`, `PR_DESCRIPTION.md`, seven hand-offs, the journey, and a grade card.

## The four things this lab is actually about

1. **No code against an unvalidated spec.** The gate is structural — you literally cannot proceed.
2. **Tests prove the code does what it does. Only the spec proves it does what it should.**
3. **Failure modes are not only security bugs.** A correct-looking implementation can cost money
   on every call.
4. **A judgment step run by the author's own context is theatre.** Fresh context is the control.
