---
name: spec-craft
description: Turn a draft or incomplete spec into a validated one — checks structure against the Context/Scope/Data/Interfaces/Acceptance-Criteria/Risks shape, checks every acceptance criterion is testable, and interrogates the intent before drafting rather than after. Use when authoring or closing gaps in specs/incremental-auth.spec.md, or any time a spec needs validating before /build runs against it.
---

# spec-craft

You turn a draft spec into one the team can trust enough to build from. Payments work is
spec-first: no code is generated against a spec that hasn't passed this.

## Step 1 — Interrogate before you draft or edit

Before writing anything, work through these questions out loud in your response:
- What is actually being asked? Restate it in one sentence.
- What's ambiguous or underspecified in the current draft?
- For each rule in `specs/NON_NEGOTIABLES.md`, is there an acceptance criterion that would fail
  if that rule were violated? If not, that's a gap.
- What edge case would a careless implementation miss — a retry, two concurrent requests, an
  expired hold, a partial capture that's individually valid but invalid in sequence?

Do not skip this step even if the draft looks complete. This is what keeps a spec from being a
restatement of the first idea instead of a pressure-tested one.

## Step 2 — Check structure

The spec must contain all six sections: **Context, Scope, Data, Interfaces, Acceptance Criteria,
Risks**. Read `specs/incremental-auth.spec.md` and report exactly which sections are present and
which are missing or empty. Do not infer a missing section's content from context — report it as
missing and either draft it (with the participant's input) or leave it flagged.

## Step 3 — Check every acceptance criterion is testable

An acceptance criterion is testable if it names a concrete input and a concrete expected
outcome — something a test could assert. Reject vague quality language ("reasonably," "handles
load," "works correctly") as non-testable. For each AC in the spec:
- If testable: leave it.
- If not testable: say why, and propose a concrete replacement (a specific scenario with a
  specific expected result) or recommend removing it as out of scope.

## Step 4 — Emit the verdict

End every run with one of:

- `SPEC STATUS: GAPS — <list of missing sections and/or non-testable ACs, one per line>`
- `SPEC STATUS: READY — every section present, every AC testable, every NON_NEGOTIABLES.md rule
  traced to at least one AC.`

Also write `specs/spec.status.json`:
```json
{ "status": "gaps" | "ready", "gaps": ["<one string per open gap>"] }
```
(`gaps` is `[]` when `status` is `"ready"`.) This is the file `/grade` checks — the chat verdict
alone isn't graded evidence.

Do not proceed to implementation work in this skill. `/build` is a separate step, gated on
`SPEC STATUS: READY`. **Human gate:** the participant reads the closed spec and confirms the
invariants are genuinely captured — not just that this step stopped complaining. Once they've
confirmed, they fill in the gap-closure and traceability worksheet at
`exercises/lab-1-spec/spec.md` (this is a separate document from the technical spec you just
validated — do not write to it yourself) and run `/hand-off` to close Lab 1 before starting
`/build`.
