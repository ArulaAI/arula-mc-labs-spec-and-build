# Primitive tour — `lab-preauth`

The harness isn't scaffolding you ignore. This tour walks the pieces so you can read them during
the lab. Everything below lives in the repo — open the files as you go.

## The shape of it

- `.forge/` — the platform: universal primitives, the grader, the lab manifest.
- `.forge/local/primitives/` — **lab-specific** primitives: `spec-craft` and `work-orchestrator`,
  the two pieces this lab introduces.
- `.claude/` — the Claude Code harness: agents, commands, rules, hooks. This lab is Claude Code
  only — there is no Copilot/`.github` mirror.

## Universal primitives (`.forge/primitives/`)

Synced from the central Forge primitive library. Not lab-specific — the same machinery every Forge
lab uses to record and grade a session.

| Primitive | What it does | Used in this lab's participant workflow? |
|---|---|---|
| **journey_recorder** | Always-on hook adapter. Every tool call, prompt, and session event is appended to `.forge/journey/<run-id>.jsonl` — the raw audit trail the grader reads. Sensitive text is hashed + previewed, not stored raw. | Yes — wired into `.claude/settings.json`, fires automatically |
| **lab_grader** | Reads `.forge/grader.yaml` plus the journey log and produces a score with a per-criterion breakdown. | Yes — via `/grade` / `make grade` |
| **journey_curator** | Turns a raw journey log into a readable narrative `journey.md`. | No — synced but not wired into this lab's participant flow |
| **failure_mode_audit** | A reusable check for common AI-assisted failure modes. | No — synced but not invoked by this lab's grader or commands |

## The differentiators (`.forge/local/primitives/`)

These two are what make this specifically the spec-to-build lab.

- **`spec-craft`** — turns a draft/incomplete spec into one the team can trust enough to build
  from. Interrogates intent before checking structure, then checks every acceptance criterion is
  objectively testable. Wired to `/spec` via `make sync-local`, which copies
  `adapters/claude_code/SKILL.md` to `.claude/commands/spec.md`.
- **`work-orchestrator`** — drives a validated spec to a reviewed, gated change: plan → TDD/codegen
  → fresh-context validation → fresh-context review → quality gates → PR body. Wired to `/build`
  the same way. Read `SPEC.md` in this primitive's directory for the exact pipeline and the
  delivery mapping onto `exercises/`.

## Subagents (`.claude/agents/`)

Each one is a focused reviewer with its own context — dispatched via Claude Code's native subagent
mechanism, which already runs each in a clean, isolated context.

| Agent | Role | Tools |
|---|---|---|
| **planner** | Input: the validated spec + `NON_NEGOTIABLES.md`. Output: an ordered issue list, each with its own acceptance criteria. Does not write code. | Read, Grep, Glob |
| **code-to-spec-validator** | Input: the spec, one issue, and its diff — nothing else. Defaults to FAIL under uncertainty. Traces the diff against every relevant non-negotiable, explicitly checking what a *second* partial capture does. | Read, Grep, Glob, Bash |
| **pr-reviewer** | Input: the diff only. Reads `.claude/rules/coding-standards.md` and `.claude/rules/payments-guardrails.md` itself, then reviews as a skeptical reviewer who did not write the code. No sycophancy. | Read, Grep, Glob, Bash |

## Commands (`.claude/commands/`)

Thin entry points; the substance lives in the primitive's `SKILL.md`/`SPEC.md`.

| Command | Backed by | What it does |
|---|---|---|
| `/spec` | `spec-craft` (L3) | Validate/close gaps in `specs/incremental-auth.spec.md` |
| `/build` | `work-orchestrator` (L3) | Plan, TDD/codegen, fresh-context validation, fresh-context review, gates, PR body |
| `/hand-off` | lab-local, no synced primitive | Close out the checkpoint just finished; appends to `docs/workflow-tracker.md` |
| `/grade` | `lab_grader` (L2) | Score the run against `.forge/grader.yaml` |

## Rules (`.claude/rules/`)

The review bar `pr-reviewer` reads before it looks at a diff:

- **`coding-standards.md`** — general: atomic state transitions via `HoldStore.update`, no
  unhandled exceptions leaking to a caller, no silently swallowed status checks, coverage that
  proves the claim rather than just existing.
- **`payments-guardrails.md`** — payments-domain, grounded in `NON_NEGOTIABLES.md`: the
  remaining-amount rule (the wrinkle this lab is built to exercise), plus a rule-by-rule review
  checklist for idempotency, the remaining-amount ceiling, and the status gate.

## Hooks (wired in `.claude/settings.json`)

| Hook | Behavior |
|---|---|
| `journey_recorder` (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`) | Appends every session event to `.forge/journey/<run-id>.jsonl`. This is what `lab_grader`'s `journey-event-present` criteria and the `subagents-dispatched` check read. |
| `quality-gates-guard` (`.claude/hooks/quality-gates-guard.sh`, `PreToolUse` matched on `Write`) | Lab-local, not synced. No-op for every write except `docs/plans/pr-body.md`; for that one, runs `mvn verify` and blocks the write (exit 2) if it isn't clean. The gate that used to be enforced only by `/build`'s own instructions is now also enforced structurally. |

## Quality gates (`pom.xml`, bound to `mvn verify`) — not a Forge primitive, but load-bearing

Native Maven plugins plus one deterministic script, all part of Lab 3 / TRUST:

- **JaCoCo `check`** — coverage threshold (line + branch), bound to the `verify` phase.
- **Checkstyle** — a minimal, lab-scoped ruleset (`checkstyle.xml`) — fails the build, not just a
  warning.
- **`scripts/quality_gates.py`** — secret and Luhn-validated cardholder-data pattern scan, plus an
  unknown-dependency check against `scripts/approved-dependencies.txt`. Deterministic Python, no
  model call, in keeping with the workbench principle that deterministic work belongs in code, not
  in the model.

A failure in any of these genuinely stops `mvn verify` — confirmed against the unbuilt baseline,
where the coverage gate correctly fails (the feature doesn't exist yet) while lint and the
secret/dependency scan pass clean.
