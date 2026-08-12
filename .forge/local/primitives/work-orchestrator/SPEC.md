# L3: work-orchestrator — lab-local primitive contract

## Purpose

Drive a validated spec to a reviewed, gated pull request, with a human gate at every stage and
a fresh context for every judgment step.

## Layer

L3 lab-local (lives under `.forge/local/primitives/`; wired into the Claude Code harness via
`make sync-local`, which copies the adapter's `SKILL.md` to `.claude/commands/build.md`).

## CLI reconciliation note

There is no native declarative "workflow" pipeline feature in the installed Claude Code CLI
(confirmed against `claude plugin init --with`, which scaffolds skills/agents/hooks/mcp/lsp/
output-style/channel but no workflow component). This primitive is therefore authored as a
sequenced skill: the instructions in `adapters/claude_code/SKILL.md` tell the main session which
subagent to dispatch at each stage. Claude Code's native subagent dispatch (`.claude/agents/*.md`)
already runs each subagent in a clean, isolated context — confirmed by inspecting the reference
lab's `adversarial-verifier.md` agent — so no custom process-spawning script is needed to satisfy
the fresh-context requirement.

## Pipeline

1. **Plan** — dispatch the `planner` subagent with the validated spec. It returns an ordered issue
   breakdown; write `issues.json` and `docs/plans/plan.md`.
2. **Per issue, in order:**
   a. Write the failing test(s) for the issue's acceptance criteria first.
   b. Implement until those tests pass.
   c. **Code-to-spec validation (fresh context)** — dispatch the `code-to-spec-validator` subagent
      with only the spec, the issue, and the diff. PASS/FAIL against `specs/NON_NEGOTIABLES.md`.
      On FAIL, return to step (b) for the smallest fix, then re-validate.
   d. **PR review (fresh context)** — dispatch the `pr-reviewer` subagent with only the diff. It
      reads `.claude/rules/coding-standards.md` and `.claude/rules/payments-guardrails.md` itself
      and reviews as a skeptical reviewer, not the author.
   e. **Quality gate** — run `mvn verify`. A failure stops the issue and reports why.
3. **PR creation** — only after validation passes, review has no blocker, and gates are green, plus
   human approval, summarize the change (spec link, validator verdict, reviewer notes, gate result)
   as the PR body and write it to `docs/plans/pr-body.md`. This always happens — it's the body of
   record. Then, if a GitHub remote is configured and approved, open a real PR from that body and
   report its URL/number; otherwise `docs/plans/pr-body.md` stands on its own as the deliverable.
   Do not hardcode either branch — check, and report which one actually happened.

## Delivery mapping

Stage 1 and steps 2(a)-2(b) above are `exercises/lab-2-plan-and-build/` in the participant-facing
guide; steps 2(c)-2(e) are `exercises/lab-3-validate-and-review/`. Together these are presented as
four separate checkpoints (plan; TDD/codegen; validation; review+gates) each closed with its own
`/hand-off`, even though this primitive runs 2c-2e together per issue. Stage 3 is
`exercises/lab-4-ship/`.

## Fresh-context rule

Stages 2c and 2d must run as genuinely separate subagent dispatches (`code-to-spec-validator`,
`pr-reviewer`) — never inline reasoning by the same context that wrote the code. This is the
anti-sycophancy rule: the reviewer must be structurally unable to defend work it didn't write.

## Acceptance

`/build` on the closed spec: if the capture implementation has the remaining-amount wrinkle
described in `docs/FACILITATOR_KEY.md`, `code-to-spec-validator` returns FAIL against AC-2 and the
pipeline halts before PR creation. Once fixed, all stages pass and a PR body is produced.
