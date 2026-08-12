# L3: spec-craft — lab-local primitive contract

## Purpose

Turn an incomplete or draft spec into a validated one the team trusts before any code is
generated against it. This lab's spec ships intentionally incomplete
(`specs/incremental-auth.spec.md`) — spec-craft's job is to interrogate the gap, not paper over it.

## Layer

L3 lab-local (lives under `.forge/local/primitives/`; wired into the Claude Code harness via
`make sync-local`, which copies the adapter's `SKILL.md` to `.claude/commands/spec.md`).

## Provenance note

The brainstorm-then-plan interrogation step below is a lab-local, self-authored implementation —
not a call-out to a third-party plugin. (An earlier plan considered depending on a companion
`superpowers` plugin for this step; that plugin isn't resolvable in this environment, so this
primitive re-expresses the same discipline directly. See build-session notes — swappable later if
a confirmed source shows up, without changing this primitive's contract.)

## Inputs

- The current state of `specs/incremental-auth.spec.md`.
- `specs/NON_NEGOTIABLES.md`, which every acceptance criterion must trace back to.

## Steps

1. **Interrogate before drafting.** Before editing the spec, work through: what is actually being
   asked, what's ambiguous, what invariant from `NON_NEGOTIABLES.md` isn't yet reflected as a
   testable acceptance criterion, what edge case (retry, concurrent capture, expiry) is missing.
2. **Check structure.** The spec must have: Context, Scope, Data, Interfaces, Acceptance Criteria,
   Risks. Report which are missing.
3. **Check testability.** Every acceptance criterion must be objectively checkable (a concrete
   input/output or a concrete test scenario) — not a vague quality statement like "handles load
   reasonably." Report any that aren't, and either propose a concrete replacement or flag for
   removal.
4. **Emit a ready/gaps summary**, write `specs/spec.status.json`, and stop for the human gate. Do
   not proceed to `/build` on a spec still reporting gaps.

## Outputs

A gap report (missing sections, non-testable ACs) when not ready; a "ready to work" confirmation
once the structural and testability checks pass; `specs/spec.status.json` either way. The human
gate closes with the participant filling in the evidence worksheet at
`exercises/lab-1-spec/spec.md` (distinct from `specs/incremental-auth.spec.md`, the technical
spec this primitive validates) and running `/hand-off`.

## Acceptance

Run against the shipped `specs/incremental-auth.spec.md` stub: reports the missing Interfaces and
Risks sections and flags AC-4 as non-testable. Passes once those are closed per
`docs/FACILITATOR_KEY.md` section 1.
