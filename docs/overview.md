# Overview — Spec to Trusted Build

A card network is adding **incremental authorization with partial capture and strict
idempotency** to its authorization core, shaped by an ISO 20022 style message contract. This is
the kind of change where a plausible but wrong implementation is dangerous: a retried request must
never create a second hold, a partial capture must never exceed the held amount, and an expired or
reversed hold must never capture. The invariants matter more than the happy path — that sentence is
the whole lab.

Participants take this feature from a deliberately incomplete spec to a gated, reviewed change,
using the `spec-craft` and `work-orchestrator` pieces of the `workbench` plugin. Everything runs
locally against a Java 21 / Spring Boot service seeded with the feature genuinely unbuilt —
`HoldService.capture()` and `HoldService.reverse()` throw `UnsupportedOperationException` on a
fresh clone.

## What you'll learn

Cohort learns what makes a good spec in a spec-first payments world, and how to hand that spec to
an orchestrated pipeline that runs planner, TDD, code generation, code-to-spec validation in a
fresh context, PR review in a fresh context, quality gates, and PR creation — with a human gate at
each step.

## Track + stack

- **Track:** Engineering
- **Stack:** Java 21, Spring Boot 3.3.x, Maven 3.9+, JUnit 5, JaCoCo, Checkstyle
- **Harness:** Claude Code. This lab does not ship a Copilot/`.github` mirror — everything lives
  under `.claude/` and `.forge/`.
- **Estimated duration:** ~2 hours (10 min setup + 120 min across four exercises)
- **Prerequisites:** Lab 1 — Foundations, governance, and the five AI failure modes. This lab
  reuses that lab's governance rules, quality-gate and journey-recorder hooks, and `lab-grader`
  rather than re-teaching them.

## The design idea worth protecting

**No code is generated against a spec that hasn't passed validation, and no judgment step is run
by the same context that did the work being judged.** Those are the two rules — spec first, fresh
context for judgment — that the rest of the pipeline exists to enforce. A subagent that validates
or reviews a diff never sees why it was written that way, only what it does; that's what makes its
verdict worth something.

## Teaching objectives

| # | Objective | How it's taught |
|---|---|---|
| 1 | **Spec-driven development** — the spec, not the prompt, is the durable artifact | `spec-craft` reports specific, testable gaps against a template; `/build` refuses to start until it reports READY |
| 2 | **Fresh-context judgment** — directing and reviewing an AI, not accepting its output | `code-to-spec-validator` and `pr-reviewer` run as separate subagent dispatches, each seeing only the diff and the standard, never the authoring conversation |
| 3 | **TDD discipline** — tests encode the invariant, not just the happy path | Every issue's tests are written from its acceptance criteria before any implementation exists |
| 4 | **Governed quality gates** — hard thresholds, not vibes | `mvn verify` enforces a coverage threshold, a lint check, and a secret/cardholder-data and unknown-dependency scan; a failure genuinely stops the pipeline |
| 5 | **Domain knowledge beats a passing test** — the finding that matters most isn't the one a scanner would catch | The remaining-amount wrinkle, below |

## Why the wrinkle is the centerpiece

The natural first implementation of the remaining-amount check validates the incoming capture
amount against something request-scoped — the original authorized amount, or the request amount
in isolation — instead of the hold's live remaining balance. That version **passes a naive
single-capture test.** It only fails on a second partial capture against the same hold. This is
the "incorrectly solving the right problem" failure mode: the code looks like it does what the
spec asks, and a shallow test agrees with it.

Catching it needs someone (or something) that traces what a *second* capture does, not just the
first. That's exactly what `code-to-spec-validator` is built to do, and `pr-reviewer` is the
second, independent backstop if the first one somehow misses it. Full detail on where this bites
and how it's expected to get caught is in `docs/FACILITATOR_KEY.md`, facilitator-only.

## The arc: SPEC → BUILD → TRUST → SHIP

| Lab | Stages | Arc | What it's for |
|---|---|---|---|
| 1 — Spec | 0-1 | SPEC | Close the seeded gaps in the spec until every non-negotiable is traced to a testable acceptance criterion |
| 2 — Plan and Build | 2-3 | BUILD | Plan the spec into issues, then implement tests-first per issue |
| 3 — Validate and Review | 4-5 | TRUST | Two independent, fresh-context checks on the diff, then the automated quality gates |
| 4 — Ship | 6 | SHIP | Assemble the change record only once everything upstream is clean, then grade |

## What participants produce

| Lab | Deliverable |
|---|---|
| 1 — Spec | A validated `specs/incremental-auth.spec.md`, plus a gap-closure worksheet |
| 2 — Plan and Build | `issues.json`, `docs/plans/plan.md`, and an implementation with tests-first evidence |
| 3 — Validate and Review | A recorded validator verdict and reviewer verdict per issue, and a clean `mvn verify` |
| 4 — Ship | `docs/plans/pr-body.md` (or an opened PR, if a remote is configured) and a grade card |
