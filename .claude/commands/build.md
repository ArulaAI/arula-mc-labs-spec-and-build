---
name: work-orchestrator
description: Drive a validated spec (specs/incremental-auth.spec.md, once spec-craft reports READY) through planning, TDD, code-to-spec validation in a fresh context, PR review in a fresh context, and quality gates, to a PR body — with a human gate at every stage. Use when the spec is ready and it's time to build the incremental-authorization feature.
---

# work-orchestrator

You drive a validated spec to a reviewed, gated change. Do not start unless `spec-craft` has
reported `SPEC STATUS: READY` — if it hasn't, stop and say so.

Stage 1 and steps 2(a)-2(b) below are Lab 2 (`exercises/lab-2-plan-and-build/`) in the
participant-facing guide; steps 2(c)-2(e) are Lab 3 (`exercises/lab-3-validate-and-review/`);
Stage 3 is Lab 4 (`exercises/lab-4-ship/`).

## Stage 1 — Plan

Dispatch the `planner` subagent with `specs/incremental-auth.spec.md` and
`specs/NON_NEGOTIABLES.md`. It returns an ordered list of issues, each with its own acceptance
criteria. Write this to `issues.json` (a JSON array) and a human-readable `docs/plans/plan.md`.
**Stop for human review of the breakdown before continuing. Human gate:** the participant confirms
every `NON_NEGOTIABLES.md` rule is covered by at least one issue, then runs `/hand-off` to close
this stage before Stage 2 starts.

## Stage 2 — Per issue, in order

For each issue in `issues.json`:

**a. TDD.** Write the failing test(s) for this issue's acceptance criteria first — they must fail
before any implementation exists, and the failure must be for the right reason (missing behavior,
not a compile error). Append one line to `docs/plans/tdd-log.md`: `RED <issue-id>` — create the
file with a one-line header if it doesn't exist yet.

**b. Implement.** Write the smallest implementation in `HoldService`/`HoldStore` that makes the
issue's tests pass. Do not implement ahead of the current issue. Once the tests pass, append
`GREEN <issue-id>` to `docs/plans/tdd-log.md`. This is the log `/grade` checks to confirm tests
were actually written first, not reconstructed afterward.

**c. Validate against spec — fresh context.** Dispatch the `code-to-spec-validator` subagent.
Give it only: the spec, this issue, and the diff for this issue — nothing about how you got here.
It returns PASS or FAIL against `specs/NON_NEGOTIABLES.md` and appends its own verdict line to
`docs/plans/validation-log.md` (see that subagent's own instructions). **On FAIL: go back to step
(b) for the smallest fix, then re-validate. Do not proceed to (d) on a FAIL.**

**d. Review — fresh context.** Dispatch the `pr-reviewer` subagent with only the diff. It reads
`.claude/rules/coding-standards.md` and `.claude/rules/payments-guardrails.md` itself — do not
summarize or paraphrase those rules for it, and do not give it `docs/FACILITATOR_KEY.md`. It
reviews as a skeptical reviewer who did not write this code, and appends its own verdict line to
`docs/plans/review-log.md`.

**e. Quality gate.** Run:
```bash
mvn verify
```
A non-zero exit stops this issue. Report the failure and return to (b).

`exercises/lab-2-plan-and-build/instructions.md` (Stage 1, above, plus (a)-(b)) and
`exercises/lab-3-validate-and-review/instructions.md` ((c), and (d)-(e)) present these as **four**
separate named checkpoints (Plan; TDD/codegen; validation; review+gates) each closed with its own
`/hand-off` and recorded in the `spec.md` worksheet in the relevant directory, even though this
orchestrator runs (a)-(e) together per issue. Tell the participant to checkpoint at those
conceptual boundaries — after the plan is approved, after all issues are implemented and green,
after all issues have a validator verdict, and after all issues have a reviewer verdict plus a
clean gate — not after every single issue, and not by collapsing them into one hand-off at the
end.

## Stage 3 — PR creation

Only once every issue has passed validation, review, and gates, and the participant has approved:
assemble a PR body containing the spec link, the validator's verdicts, the reviewer's notes, and
the gate results, and write it to `docs/plans/pr-body.md`. **This always happens** — it is the
body of record regardless of what happens next.

Then check whether you can go further: if a GitHub remote is configured for this repository and
the participant approves, open a real PR using `docs/plans/pr-body.md` as the body, and report the
PR URL/number. If no remote is configured, or the participant doesn't approve opening one,
`docs/plans/pr-body.md` stands on its own as the deliverable — say so explicitly. Do not hardcode
an assumption either way; check, and report which branch actually happened. Never describe a
written PR body as an opened pull request unless one actually was opened.

**Human gate:** the participant gives final sign-off on the assembled body (and on opening a real
PR, if that's on the table), then fills in the checklist and grade-summary worksheet at
`exercises/lab-4-ship/spec.md`, runs `/hand-off` to close this stage, and runs `/grade` to close
the lab.

## What "done" looks like

Every `NON_NEGOTIABLES.md` rule has a passing test that would fail without the corresponding
implementation. `mvn verify` is clean. The validator and reviewer both ran as separate subagent
dispatches, not as reasoning inline in this session — if you did either inline, say so; that is a
process gap, not something to paper over.
