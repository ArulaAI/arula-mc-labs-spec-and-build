# Lab 2 Build Instructions: Spec to Trusted Build (Claude Code, payments)

**Audience:** Claude Code, building the lab, with a facilitator supervising.
**What this doc produces:** a Java 21 + Spring Boot repo where the cohort takes a real payments feature from a validated spec to a gated pull request using the workbench orchestrator, plus the seeded spec stub, acceptance criteria, facilitator key, lab config and the participant action guide.
**Prerequisites:** Claude Code with the `workbench` plugin installed; Java 21; Maven 3.9+.

> Workbench pieces this lab **introduces**: `spec-craft` (`/spec`) and the `work-orchestrator` (`/build`) with the `planner`, `code-to-spec-validator` and `pr-reviewer` subagents. It reuses the governance rules, `quality_gates`, `journey_record`/`/hand-off` and `lab-grader` from Lab 1.

---

## 1. Learning outcome
Cohort learns what makes a good spec in a spec-first payments world, and how to hand that spec to an orchestrated pipeline that runs planner, TDD, code generation, code-to-spec validation in a fresh context, PR review in a fresh context, quality gates, and PR creation, with a human gate at each step.

## 2. The payments scenario
A card network is adding **incremental authorization with partial capture and strict idempotency** to its authorization core, shaped by an ISO 20022 style message contract. This is the kind of change where a plausible but wrong implementation is dangerous: a retried request must never create a second hold, a partial capture must never exceed the held amount, and an expired or reversed hold must never capture. The invariants matter more than the happy path.

## 3. Build the lab repo
Create `lab-preauth`:
```
lab-preauth/
  pom.xml                          # Java 21, Spring Boot 3.3.x, web, validation, test; JaCoCo
  src/main/java/com/mc/preauth/
    PreauthApplication.java
    domain/                        # records: Hold, CaptureRequest, AuthMessage (ISO 20022-shaped fields)
    service/HoldService.java       # secure, minimal base: create hold; capture and reverse are STUBBED to fail
    repo/HoldStore.java            # concurrency-safe store scaffold (the cohort completes the invariants)
  src/main/resources/application.yml   # virtual threads on
  src/test/java/com/mc/preauth/BaselineTest.java   # green baseline
  specs/incremental-auth.spec.md   # STUB: title, context, a few gaps to fill via /spec
  specs/NON_NEGOTIABLES.md         # the invariants (idempotency, capture <= held, no capture after reverse/expire)
  docs/plans/.gitkeep
  docs/workflow-tracker.md
  docs/FACILITATOR_KEY.md
  LAB_ACTION_GUIDE.md
  .claude/
    settings.json                  # quality_gates + journey_record on
    lab.json                       # id: spec-to-build, rubric: spec-to-build.rubric.yaml
```

### 3.1 Baseline and seams
- Java 21 records for the ISO 20022 shaped `AuthMessage`, `Hold`, `CaptureRequest`; sealed result types; virtual threads on.
- The base compiles and `BaselineTest` is green. `capture()` and `reverse()` are stubbed to throw `UnsupportedOperationException` so the feature is genuinely unbuilt.
- `specs/NON_NEGOTIABLES.md` states the invariants precisely and testably. `specs/incremental-auth.spec.md` is an intentionally incomplete stub with two missing sections and one non-testable acceptance criterion, so `/spec` validation reports gaps.

### 3.2 The wrinkle (documented in the key)
The natural first implementation captures against the request amount rather than the remaining held amount, which passes a naive happy-path test but violates a non-negotiable. The `code-to-spec-validator` (fresh context) must catch this against the acceptance criteria, and the `pr-reviewer` (fresh context) must not wave it through. This is the "incorrectly solving the right problem" failure mode.

### 3.3 Facilitator key and lab config
- `docs/FACILITATOR_KEY.md`: the complete, correct spec; the invariant set; the wrinkle and where it bites; the expected planner issue breakdown; the gate outcomes.
- `spec-to-build.rubric.yaml` for `lab-grader`: spec passed validation with gaps closed, planner produced ordered issues, TDD wrote failing tests first, code-to-spec validation ran in a fresh context and caught the capture invariant, PR review ran in a fresh context, all quality gates green, PR created only after gates and human approval.

## 4. Acceptance: built correctly when
1. Fresh clone green; `capture()`/`reverse()` are unbuilt.
2. `/spec` on the stub reports the seeded gaps and passes once they are closed.
3. `/build` drives planner, TDD, codegen, fresh-context validation and review, gates, and PR creation, and it **blocks the PR** when the capture-against-request wrinkle is present.
4. `lab-grader` scores a completed run reproducibly.

## 5. Participant Action Guide (write to `LAB_ACTION_GUIDE.md`)

### Workspace setup
Install and open as in Lab 1. Confirm `/spec`, `/build`, the three subagents, `/hand-off` and `/grade` are available, and the governance rules load.

### The flow at a glance

| # | Stage | Min | Workbench surface | Key artifacts |
|---|-------|-----|-------------------|---------------|
| 0 | Context: specs and the pipeline | 15 | facilitator; `NON_NEGOTIABLES.md` | shared understanding |
| 1 | Author and validate the spec | 25 | `spec-craft` (`/spec`) | `specs/incremental-auth.spec.md` validated |
| 2 | Plan: spec to issues | 12 | `planner` (via `/build`) | `docs/plans/plan.md`, `issues.json` |
| 3 | TDD and code generation | 30 | `work-orchestrator` (`/build`) | failing tests then passing code, per issue |
| 4 | Code-to-spec validation (fresh) | 12 | `code-to-spec-validator` | validation verdict, wrinkle caught |
| 5 | PR review and quality gates | 15 | `pr-reviewer`, `quality_gates` | review verdict, gates green |
| 6 | PR creation and close | 11 | `work-orchestrator`, `/hand-off`, `/grade` | PR opened, journey, grade |

### Stage 1: Author and validate the spec (25 min)
1. `/spec`:
   ```text
   /spec Draft specs/incremental-auth.spec.md for incremental authorization with
   partial capture and strict idempotency, shaped by the ISO 20022 fields in the
   domain records and bound by specs/NON_NEGOTIABLES.md. Fill the missing sections
   and make every acceptance criterion testable.
   ```
2. Let `spec-craft` validate. Close the reported gaps until it reports ready. Human gate: read the spec and confirm the invariants are captured. **End of stage:** `/hand-off`.

### Stage 2: Plan, spec to issues (12 min)
1. Start the orchestrator planning pass:
   ```text
   /build plan-only using specs/incremental-auth.spec.md. Break it into a small
   ordered set of issues, each with its own acceptance criteria. Write issues.json
   and docs/plans/plan.md.
   ```
2. Review the issue breakdown. **End of stage:** `/hand-off`.

### Stage 3: TDD and code generation (30 min)
1. Run the build loop per issue:
   ```text
   /build run using issues.json. For each issue: write the failing tests first from
   its acceptance criteria, then implement HoldService.capture and reverse and the
   HoldStore invariants until the tests pass. Stop at the first issue whose tests
   will not go green and report why.
   ```
2. Watch the capture logic. If it captures against the request amount rather than the remaining held amount, the tests derived from the non-negotiables should fail. **End of stage:** `/hand-off`.

### Stage 4: Code-to-spec validation, fresh context (12 min)
1. **Subagent `code-to-spec-validator`** runs with only the spec, the issue and the diff:
   ```text
   Validate the diff for each issue against specs/incremental-auth.spec.md and
   specs/NON_NEGOTIABLES.md. Confirm: retries are idempotent, capture never exceeds
   the remaining held amount, and no capture occurs after reverse or expiry.
   Return PASS or FAIL with the specific criterion for any failure.
   ```
2. If it fails on the capture invariant, return to Stage 3 for the smallest fix. **End of stage:** `/hand-off`.

### Stage 5: PR review and quality gates (15 min)
1. **Subagent `pr-reviewer`** (fresh context, no sycophancy) reviews the diff against `coding-standards` and `payments-guardrails`.
2. Run the gates:
   ```bash
   mvn verify
   ```
   The `quality_gates` hook runs lint, a secret and cardholder-data scan, the coverage threshold, and an unknown-dependency check. A failure stops the PR. **End of stage:** `/hand-off`.

### Stage 6: PR creation and close (11 min)
1. On passing validation, review and gates, plus your approval, let the orchestrator open the PR with the spec link, the validator and reviewer notes, and the gate results attached.
2. Run `/grade`. Recap: a good spec plus fresh-context judgment is what turned a plausible implementation into a trusted one.

### Artifact checklist
`specs/incremental-auth.spec.md`, `specs/NON_NEGOTIABLES.md`, `issues.json`, `docs/plans/plan.md`, the generated tests and code, the PR, `docs/workflow-tracker.md`, the journey file, the grade card, `docs/FACILITATOR_KEY.md`.
