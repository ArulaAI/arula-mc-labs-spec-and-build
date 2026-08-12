# Spec to Trusted Build

A hands-on Forge lab built on a small **Spring Boot payment-authorization service**. A card
network is adding incremental authorization with partial capture and strict idempotency — a
plausible-but-wrong implementation is genuinely dangerous here. You take the feature from a
deliberately incomplete spec to a gated, reviewed change by **driving** an AI harness, not
accepting its output.

> Everything runs locally against a Claude Code harness. `capture()` and `reverse()` ship unbuilt
> — that's the correct starting state, not a bug.

## Start here

1. Read [`LAB_ACTION_GUIDE.md`](LAB_ACTION_GUIDE.md) — setup and the four labs.
2. Open [`exercises/lab-1-spec/instructions.md`](exercises/lab-1-spec/instructions.md).
3. `make test` should be green before you start.

## The arc: SPEC → BUILD → TRUST → SHIP

| Lab | Exercise | You produce |
|---|---|---|
| 1 · Spec | `exercises/lab-1-spec` | A validated `specs/incremental-auth.spec.md`, gaps closed via `/spec` |
| 2 · Plan and Build | `exercises/lab-2-plan-and-build` | `issues.json`, an ordered plan, and a tests-first implementation |
| 3 · Validate and Review | `exercises/lab-3-validate-and-review` | Independent, fresh-context validator + reviewer verdicts, then clean quality gates |
| 4 · Ship | `exercises/lab-4-ship` | `docs/plans/pr-body.md` (or a real PR, if a remote is configured) and a grade card |

## What makes this different

No code is generated against a spec that hasn't been validated, and no judgment step is run by the
context that did the work being judged. `code-to-spec-validator` and `pr-reviewer` each run in a
fresh subagent context — they see only the diff, never why it was written that way. The lab is
built around one specific trap: the natural first pass at the remaining-amount check passes a
naive single-capture test and is still wrong. Whether that gets caught is the point.

Quality gates are real, not advisory: `mvn verify` enforces a coverage threshold, a lint check, and
a secret/cardholder-data and unknown-dependency scan, and a `PreToolUse` hook blocks
`docs/plans/pr-body.md` from being written at all until gates are clean.

## Grade yourself

```bash
make grade
```

Runs the tests and the Forge lab grader against `.forge/grader.yaml`. Grading checks *process*,
not just output — spec closed via `/spec`, tests written before implementation
(`docs/plans/tdd-log.md`), the validator and reviewer logging their own verdicts
(`docs/plans/validation-log.md`, `review-log.md`), quality gates genuinely green, and `/hand-off`
recorded at every stage boundary in `docs/workflow-tracker.md`.

## Stack

| Technology | Version | Purpose |
|---|---|---|
| Java | 21 | Language |
| Spring Boot | 3.3.x | Application framework |
| Maven | 3.9+ | Build |
| JUnit 5 | — | Testing |
| JaCoCo | 0.8.12 | Coverage threshold |
| Checkstyle | 3.5.0 | Lint gate |

## Primitives shipped

| Primitive | Layer | Where |
|---|---|---|
| `spec-craft` | L3, lab-local | `.forge/local/primitives/spec-craft/`, wired to `/spec` |
| `work-orchestrator` | L3, lab-local | `.forge/local/primitives/work-orchestrator/`, wired to `/build` |
| `planner`, `code-to-spec-validator`, `pr-reviewer` subagents | L1 | `.claude/agents/` |
| `coding-standards`, `payments-guardrails` review rules | L1 | `.claude/rules/` |
| `quality-gates-guard` hook | L1, lab-local | `.claude/hooks/`, wired in `.claude/settings.json` |
| `journey_recorder`, `lab_grader` (+ 2 more, unused in this lab's flow) | L2, synced | `.forge/primitives/` |

See [`docs/primitive-tour.md`](docs/primitive-tour.md) for the full tour, and
[`docs/overview.md`](docs/overview.md) for why the remaining-amount wrinkle is the centerpiece.

## Prerequisites

- JDK 21
- Maven 3.9+
- Claude Code — this lab is Claude Code only; there is no Copilot/`.github` mirror

## Harness

This is a single-harness lab (Claude Code). `make sync` refreshes the synced primitives under
`.forge/primitives/`; `make sync-local` wires `spec-craft`/`work-orchestrator` into
`.claude/commands/`. See `Makefile` for the full target list.
