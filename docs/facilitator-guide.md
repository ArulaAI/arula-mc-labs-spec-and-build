# Facilitator guide — Spec to Trusted Build

How to run the session: setup, timing, what to watch for at each checkpoint, and how to recover
when a participant gets stuck. Pair with `docs/FACILITATOR_KEY.md` for the answer key (the
complete closed spec, the exact wrinkle scenario, expected gate outcomes) — keep that one to
yourself. This document is operational; it doesn't duplicate the answer key.

## Before the session

- [ ] Java 21 available (`java -version` → 21). Maven 3.9+ (`mvn -version`).
- [ ] `make test` is green on a clean tree — `capture()` and `reverse()` throw
      `UnsupportedOperationException`. That's the correct starting state; if a participant's
      clone shows anything else, something upstream reset incorrectly — run `make reset`.
- [ ] Harness loaded: `/spec`, `/build`, `/hand-off`, `/grade` resolve in Claude Code, and the
      `planner`, `code-to-spec-validator`, `pr-reviewer` subagents are available. If not, run
      `forge sync .` (or the `make sync`/`make sync-local` fallback — see `LAB_ACTION_GUIDE.md`).
- [ ] Decide and announce the PR path for this session: is a GitHub remote configured and will you
      let `/build` open a real PR in Lab 4, or is this a local-fallback session where
      `docs/plans/pr-body.md` is the deliverable? Either is fine — the harness checks and reports
      which one happened; just don't leave it ambiguous going in.
- [ ] `mvn verify` on the clean tree: the coverage gate should **fail** (the feature isn't built
      yet), while lint and the secret/dependency scan should pass clean. If lint or the
      secret/dependency scan fail on a clean tree, something is broken upstream — don't proceed
      until that's understood.

## Running the four labs

| Lab | Median | Stretch |
|---|---|---|
| 1 — Spec | 40 min | +10 if a participant tries to skip straight to `/build` before READY |
| 2 — Plan and Build | 42 min | +15 if the planner breakdown needs a second pass |
| 3 — Validate and Review | 27 min | +15 for a FAIL → fix → re-validate loop back to Lab 2 |
| 4 — Ship | 11 min | +5 if opening a real PR needs remote/auth troubleshooting |

Total median: ~2 hours; with stretch, ~2.5 hours.

### Lab 1 — Spec (40 min)

Participants run `/spec` against the seeded stub. `spec-craft` reports the two missing sections
(Interfaces, Risks) and the non-testable AC-4 on the first pass — if it reports READY
*immediately*, the participant hasn't actually engaged with the gaps yet; check the spec file
still has its `<!-- TODO -->` markers before believing the READY verdict.

**Watch for:** accepting `spec-craft`'s draft language for Interfaces/Risks without reading it —
the review gate here is the participant confirming the invariants themselves, not the tool
stopping complaining. **Recovery:** if a participant moves on without reading the closed spec,
ask them to restate, out loud, what the Risks section now says about concurrent captures.

### Lab 2 — Plan and Build (42 min)

The planner breakdown should cover all three `NON_NEGOTIABLES.md` rules across its issues — if a
participant's plan misses one, that's a legitimate finding to send back before any code exists.

This is where the seeded wrinkle gets a chance to appear — **it is not planted in the starter
code; participants can produce it themselves.** The natural first pass at the remaining-amount
check tends to validate the incoming amount against something request-scoped rather than the
hold's live remaining balance. A participant who writes only a single-capture happy-path test will
not see it fail here — that's expected and is exactly what Lab 3 exists to catch.

**Watch for:** a participant treating one green test as proof the capture logic is right. **Nudge,
don't tell:** ask "what happens if you capture twice against the same hold?" rather than pointing
at the bug directly — let Lab 3's fresh-context checks (or the participant's own answer to that
question) do the catching.

### Lab 3 — Validate and Review (27 min)

The most important 27 minutes in the lab. Two independent, fresh-context checks run against the
Lab 2 diff.

**Expected checkpoint behavior:** if the wrinkle is present, `code-to-spec-validator` should
return `VALIDATION: FAIL` naming the remaining-amount rule and a concrete breaking scenario. If it
returns PASS on a diff that actually has the wrinkle, that's worth pausing the room for — ask the
participant to walk through a sequential two-capture case by hand and see if the validator's
verdict holds up under their own scrutiny. `pr-reviewer` is the second, independent backstop; it
should also catch it via `.claude/rules/payments-guardrails.md` even if the validator somehow
didn't.

**Expected failure/return path:** a FAIL or a BLOCKED sends the participant back to **Lab 2, Stage
3** for the smallest fix — watch for participants trying to patch the test instead of the
implementation. That's the failure this whole lab is built to prevent; stop it in the room.

**Recovery if a participant is stuck on why the check is wrong:** have them write out, on paper or
in a comment, the state of the hold after each of two sequential captures, and compare against
what the buggy check actually evaluates.

### Lab 4 — Ship (11 min)

`/build` always writes `docs/plans/pr-body.md` once Lab 3's gates are green, then checks whether a
real PR can be opened. Confirm participants report which branch actually happened — a written PR
body is not the same claim as an opened pull request, and the lab is graded on getting that
distinction right, not just on the file existing.

## Grading and feedback

Run `make grade` (or `/grade`). It runs the tests and the Forge lab grader against
`.forge/grader.yaml`, scoring observable process signals — spec closed via `/spec`, subagents
dispatched in fresh contexts, quality gates genuinely green, hand-off checkpoints recorded at all
six stage boundaries, the PR body assembled only after gates passed — not a hidden answer-key
comparison. See `docs/FACILITATOR_KEY.md` for what a fully correct run looks like.

## Reset between cohorts

```bash
make reset
```

Restores `src/`, `specs/`, and `exercises/` to the clean baseline and clears local journey logs
(`.forge/journey/*.jsonl`, `.forge/.current-run-id`) and `docs/workflow-tracker.md`. Confirm with
`make test` (green, with `capture()`/`reverse()` still stubbed) afterward.
