---
lesson_id: spec-to-build::lab-1-spec
estimated_min: 40
primitives_used:
  l1:
    - spec-craft
    - /spec
  l2:
    - journey-recorder
  l3:
    - spec-craft
---

# Lab 1 — Spec (Stages 0-1)

## Why this matters

Everything downstream — the plan, the tests, the fresh-context validator, the reviewer, the
grader — checks work against `specs/incremental-auth.spec.md`. A gap here is a gap in what gets
checked for the rest of the lab. This is the cheapest point in the whole pipeline to catch a
missing invariant.

## Objective

Leave this lab with `specs/incremental-auth.spec.md` reporting `SPEC STATUS: READY` — every
section present, every acceptance criterion testable, every rule in `NON_NEGOTIABLES.md` traced to
at least one AC — and with you able to restate all three non-negotiables from memory.

## Steps

### Stage 0 — Context (15 min)

1. Read `specs/NON_NEGOTIABLES.md` end to end. There's no tool for this stage — it's you and the
   facilitator.
2. Confirm out loud, without looking back at the file, what would have to go wrong for each of the
   three rules to be violated: a duplicated capture, an over-capture, a capture after
   reverse/expiry.

**Human gate:** can you restate all three invariants unprompted? If not, don't move on.

### Stage 1 — Author and validate the spec (25 min)

1. Open `hypothesis.md` in this directory and fill in the pre-tool prediction section. Two
   minutes, before you run anything.
2. Run (this deliberately names the stub's actual seeded gaps rather than asking `spec-craft` to
   discover them from a generic "draft the spec" prompt — you already read them in Stage 0):
   ```text
   /spec Close the gaps in specs/incremental-auth.spec.md — the Interfaces and Risks sections, and
   the non-testable AC-4 — bound by specs/NON_NEGOTIABLES.md. Make every acceptance criterion
   testable.
   ```
3. `spec-craft` interrogates the intent, checks structure, then checks every acceptance criterion
   for testability. It ends with `SPEC STATUS: GAPS — <list>` or `SPEC STATUS: READY`. It also
   writes `specs/spec.status.json`.
4. Iterate — close every reported gap — until you get `SPEC STATUS: READY`.
5. **Read the closed spec yourself.** The human gate is you confirming the invariants are actually
   captured, not that the tool stopped complaining.
6. Fill in `spec.md` in this directory — the gap-closure and traceability worksheet — from your
   own read of the closed spec, not by copying `spec-craft`'s output verbatim.
7. Reopen `hypothesis.md` and fill in the reflection section.

## What you'll see (so you know it worked)

- `/spec` reports gaps the first time (the Interfaces and Risks sections, and AC-4's "reasonably
  under load" language) — if it reports READY on the very first run, you haven't actually closed
  anything yet; check `specs/incremental-auth.spec.md` still has its `<!-- TODO -->` markers.
- `specs/spec.status.json` flips from `"status": "gaps"` to `"status": "ready"`.
- Every rule in `NON_NEGOTIABLES.md` is traceable to a specific acceptance criterion in the closed
  spec — not implied, actually named.

## Self-check: have you met the review gate?

Before running `/hand-off`, confirm — on your own, no facilitator required:

- [ ] `specs/incremental-auth.spec.md` has all six sections: Context, Scope, Data, Interfaces,
      Acceptance Criteria, Risks
- [ ] Every acceptance criterion names a concrete input and a concrete expected outcome
- [ ] All three `NON_NEGOTIABLES.md` rules trace to at least one AC
- [ ] `specs/spec.status.json` says `"status": "ready"`
- [ ] `hypothesis.md`'s reflection section is filled in

If you can't check all five, go back to `/spec` before continuing.

## `/hand-off` checkpoint

Run `/hand-off` once the spec is READY and you've read it yourself. It records the closure to
`docs/workflow-tracker.md`. This closes Lab 1 — Lab 2 (`exercises/lab-2-plan-and-build/`) starts
from the validated spec.

## Acceptance criteria

- [ ] `specs/incremental-auth.spec.md` reports `SPEC STATUS: READY`
- [ ] `specs/spec.status.json` exists with `"status": "ready"`
- [ ] `exercises/lab-1-spec/spec.md` worksheet is filled in
- [ ] `exercises/lab-1-spec/hypothesis.md` was written before `/spec` and reflected on after
- [ ] `/hand-off` was run to close the stage
