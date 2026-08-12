---
lesson_id: spec-to-build::lab-2-plan-and-build
estimated_min: 42
primitives_used:
  l1:
    - planner
    - /build
  l2:
    - journey-recorder
  l3:
    - work-orchestrator
---

# Lab 2 — Plan and Build (Stages 2-3)

## Why this matters

This is where a plausible-but-wrong implementation actually gets written. `/build` plans the spec
into issues and then drives TDD/codegen per issue — this lab covers both, as **two distinct
checkpoints with their own gate, their own failure path, and their own `/hand-off`**. Whether the
pipeline catches a mistake made here is what Lab 3 (`exercises/lab-3-validate-and-review/`) is
for — but the mistake, if there is one, gets written here.

## Objective

Leave this lab with `capture()` and `reverse()` implemented and every `NON_NEGOTIABLES.md` rule
covered by a passing test.

## Before you start

Open `hypothesis.md` in this directory and fill in the pre-tool prediction section — two minutes,
before you run `/build` at all.

---

## Stage 2 — Plan: spec to issues (12 min)

**Objective.** Turn the validated spec (`SPEC STATUS: READY` from Lab 1) into a small, ordered,
independently-testable issue breakdown.

**Command.**
```text
/build plan-only using specs/incremental-auth.spec.md. Break it into a small ordered set of
issues, each with its own acceptance criteria. Write issues.json and docs/plans/plan.md.
```

**What Claude is doing.** Dispatches the `planner` subagent with only the spec and
`NON_NEGOTIABLES.md` — it doesn't write code and doesn't validate anything, it just orders the
work.

**Expected artifacts.** `issues.json` (structured, per-issue acceptance criteria),
`docs/plans/plan.md` (human-readable version).

**Inspect.** Does every rule in `NON_NEGOTIABLES.md` show up in at least one issue's acceptance
criteria? If idempotency, the remaining-amount ceiling, or the status gate is missing from every
issue, nothing downstream will check for it.

**Success / failure.** `PLAN: <N> issues, all NON_NEGOTIABLES.md rules covered` vs. a named gap —
if a gap is named, ask for a revised breakdown before continuing; don't patch `issues.json` by
hand.

**Human gate.** Approve the breakdown, or send it back, before any code gets written.

**`/hand-off` checkpoint.** Run `/hand-off` once you've approved the plan. This closes Stage 2
independently of Stage 3 — don't wait until code exists to record it.

---

## Stage 3 — TDD and code generation (30 min)

**Objective.** Implement `capture()`, `reverse()`, and the `HoldStore` invariants — tests first,
per issue.

**Command.**
```text
/build run using issues.json. For each issue: write the failing tests first from its acceptance
criteria, then implement HoldService.capture and reverse and the HoldStore invariants until the
tests pass. Stop at the first issue whose tests will not go green and report why.
```

**What Claude is doing.** Per issue: writes a failing test derived from that issue's acceptance
criteria, then writes the smallest implementation that makes it pass.

**Expected artifacts.** New tests under `src/test/java`, implementation changes in
`HoldService`/`HoldStore`, and a `RED <issue-id>` / `GREEN <issue-id>` pair per issue in
`docs/plans/tdd-log.md` — the machine-checkable record that tests came first.

**Inspect — closely, this is the stage where it bites.** The remaining-amount check
specifically: does it compare the incoming capture amount against `hold.remainingAuthorized()`
computed fresh at the moment of *this* capture, or against something request-scoped (the original
authorized amount, or the request amount in isolation)? A single-capture happy-path test cannot
tell you which — write (or confirm you have) a test that captures twice in sequence against the
same hold.

**Success / failure and return path.** Tests fail, then pass, per issue. If a test won't go
green, `/build` stops at that issue and reports why — fix the implementation, don't weaken the
test. If the remaining-amount check has the wrinkle, a single-capture test will still pass; only a
sequential-partial-capture test (capture 60 of 100, then attempt 50) will fail against it.

**Human gate.** Before moving on, look at the remaining-amount check yourself. Don't rely on green
tests alone if you only wrote a single-capture test.

**`/hand-off` checkpoint.** Run `/hand-off` once every issue in `issues.json` is implemented and
its own tests are green. This closes Lab 2 — independent, fresh-context judgment on this diff
happens in Lab 3 (`exercises/lab-3-validate-and-review/`).

---

## After Stage 3: reflect

Reopen `hypothesis.md` and fill in the reflection section — specifically, whether the
remaining-amount check you wrote actually checks the hold's live remaining balance, or something
request-scoped. You may not know for certain yet; say what you believe and why. Lab 3 is where
that belief gets checked by someone (something) that wasn't in the room.

## Self-check: have you met the review gate?

Before moving to Lab 3, confirm — on your own, no facilitator required:

- [ ] `issues.json` covers every `NON_NEGOTIABLES.md` rule
- [ ] Every issue has a test that fails before the implementation and passes after
- [ ] At least one test captures the same hold twice in sequence (not just a single-capture
      happy path)
- [ ] `/hand-off` was run at the end of Stage 2 and at the end of Stage 3 — two separate entries
      in `docs/workflow-tracker.md`, not one

If you can't check all four, go back to the relevant stage before continuing.

## Acceptance criteria

- [ ] `docs/plans/plan.md` and `issues.json` exist and cover every non-negotiable
- [ ] `capture()` and `reverse()` no longer throw `UnsupportedOperationException`
- [ ] A sequential-partial-capture test exists and passes
- [ ] `exercises/lab-2-plan-and-build/spec.md` worksheet is filled in
- [ ] `exercises/lab-2-plan-and-build/hypothesis.md` was written before `/build` and reflected on
      after
- [ ] `docs/workflow-tracker.md` has two new entries, one per stage above
