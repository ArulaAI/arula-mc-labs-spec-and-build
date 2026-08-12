# Lab Action Guide — Spec to Trusted Build

## The scenario

A card network is adding **incremental authorization with partial capture and strict
idempotency** to its authorization core. A retried request must never create a second hold or
capture, a partial capture must never exceed the remaining held amount, and an expired or
reversed hold must never capture. `HoldService.capture()` and `HoldService.reverse()` are
currently unbuilt — that's what you're building.

The arc: **SPEC → BUILD → TRUST → SHIP.** A validated spec, an implementation driven from it, two
independent fresh-context checks on whether the implementation actually honors it, then a change
record assembled only once all of that is clean.

## Setup (10 minutes)

1. **Java 21 + Maven 3.9+** — `java -version` and `mvn -version`.
2. **Build green** — from the repo root:
   ```bash
   make test
   ```
   You should see `BUILD SUCCESS`. `capture()` and `reverse()` are unbuilt stubs — that's the
   correct starting state, not a bug.
3. **Harness loaded.** In Claude Code, `/spec`, `/build`, `/hand-off`, and `/grade` should be
   available, along with the `planner`, `code-to-spec-validator`, and `pr-reviewer` subagents.

## Commands and how to run them

You drive the whole lab with four commands, run in order across the four exercises below.

| Command | Exercise | What it does |
| --- | --- | --- |
| `/spec` | Lab 1 (SPEC) | Closes the gaps in `specs/incremental-auth.spec.md` until every acceptance criterion is testable and every non-negotiable is traced. |
| `/build` | Lab 2, 3, 4 (BUILD, TRUST, SHIP) | Plans the spec into issues, drives TDD/codegen, dispatches fresh-context validation and review, runs quality gates, and (Lab 4) assembles the PR body. |
| `/hand-off` | All | Closes out the checkpoint you just finished — appends an entry to `docs/workflow-tracker.md`. Run it at **every** checkpoint below, not just at the end of an exercise. |
| `/grade` | Lab 4 (SHIP) | Scores the run against `.forge/grader.yaml` and writes a grade card. |

**If a command isn't recognized.** Run `make sync-local` and confirm `.claude/commands/` is loaded
in your session.

## How the labs work

You are **driving**. The AI proposes; you decide. Every checkpoint has an explicit human gate —
the failure mode the gate exists to catch is *accepting output unread*. Each exercise below has
its own `hypothesis.md` (predict, then check against reality), `instructions.md` (the full
step-by-step), and `spec.md` (that exercise's evidence worksheet — not the technical spec, which
stays at `specs/incremental-auth.spec.md` throughout).

- **[Lab 1 — Spec](exercises/lab-1-spec/instructions.md)** — SPEC (Stages 0-1, 40 min). Read
  `NON_NEGOTIABLES.md`, then run `/spec` until `specs/incremental-auth.spec.md` reports READY.
  Human gate: you read the closed spec and confirm the invariants are actually captured.

- **[Lab 2 — Plan and Build](exercises/lab-2-plan-and-build/instructions.md)** — BUILD (Stages
  2-3, 42 min). `/build` plans the spec into issues, then drives TDD/codegen per issue. This is
  where a plausible-but-wrong capture-amount check actually gets written — kept as **two separate
  checkpoints** (Plan; TDD/codegen), each with its own gate, failure path, and `/hand-off`.

- **[Lab 3 — Validate and Review](exercises/lab-3-validate-and-review/instructions.md)** — TRUST
  (Stages 4-5, 27 min). Two independent, fresh-context checks on the diff from Lab 2:
  `code-to-spec-validator` (never saw why you wrote it that way) and `pr-reviewer` (a second,
  independent check, unaware of the validator's verdict), then the hard automated quality gates.
  Kept as **two separate checkpoints** (validation; review+gates) — this is the most important
  concept in the lab, so it isn't allowed to blur into one step.

- **[Lab 4 — Ship](exercises/lab-4-ship/instructions.md)** — SHIP (Stage 6, 11 min). `/build`
  always assembles `docs/plans/pr-body.md` once Lab 3's gates are green — that's the body of
  record regardless of what happens next. If a GitHub remote is configured and approved, `/build`
  opens a real PR from that body; otherwise `docs/plans/pr-body.md` stands on its own as the
  deliverable. Either way, it says explicitly which one happened — never assume no GitHub access.
  Then `/grade` scores the whole run.

## Grade yourself

```bash
make grade
```
or run `/grade` directly. Either scores the current run against `.forge/grader.yaml` and writes
`.forge/journey/<run-id>/grade.json`.

## Ground rules

- No implementation without a validated spec (`SPEC STATUS: READY`) first.
- No PR body without clean fresh-context validation, clean fresh-context review, and a clean
  `mvn verify` first.
- `code-to-spec-validator` and `pr-reviewer` must run as separate subagent dispatches, not as
  inline reasoning in the same context that wrote the code.
- `/hand-off` at every checkpoint — the audit trail in `docs/workflow-tracker.md` is what shows
  the pipeline was actually followed, not just that the final files exist.
- Never assert "no GitHub access" or "no PR was opened" without checking — report what actually
  happened.

## Artifact checklist

`specs/incremental-auth.spec.md`, `specs/spec.status.json`, `specs/NON_NEGOTIABLES.md`,
`exercises/lab-1-spec/{hypothesis,spec}.md`, `issues.json`, `docs/plans/plan.md`,
`exercises/lab-2-plan-and-build/{hypothesis,spec}.md`, the generated tests and code,
`exercises/lab-3-validate-and-review/{hypothesis,spec}.md`, `docs/plans/pr-body.md`,
`exercises/lab-4-ship/{hypothesis,spec}.md`, `docs/workflow-tracker.md`, the journey log under
`.forge/journey/`, the grade card (`.forge/journey/<run-id>/grade.json`),
`docs/FACILITATOR_KEY.md` (facilitator only).
