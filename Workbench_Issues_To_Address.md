# Workbench Issues to Address

**Purpose:** defects and contract gaps found in `arula-mc-labs-plugin-main/workbench/` while authoring
`Lab1_Build_Instructions_Finish_the_Refund.md`. These are plugin-level problems — they should be fixed
once, in the shared Workbench, not re-solved per lab. This document is a punch list for that future
Workbench build/update pass, not a build-instructions document itself.

**Status:** none of these block Lab 1. Lab 1's build instructions ship a labeled, working mitigation for
every item below and do not depend on any of these being fixed first. Cross-references point to the
exact section of `Lab1_Build_Instructions_Finish_the_Refund.md` carrying each mitigation.

---

## 1. Hook payload delivery — env vars vs. stdin (highest priority; affects every lab)

**What's wrong:** `hooks/journey_record.py` reads `CLAUDE_SESSION_ID`, `CLAUDE_TOOL_NAME`,
`CLAUDE_TOOL_INPUT` from `os.environ`. Confirmed: the actual Claude Code hook contract delivers this
data as event-specific JSON on **stdin** (session ID, hook event name, tool name, tool input), not as
environment variables. Nothing in `journey_record.py` reads stdin.

**Consequence if unfixed:** `CLAUDE_SESSION_ID` is never populated, so the hook's fallback —
`f"session-{int(time.time())}"` — fires on every single invocation. One learner's session scatters
across many `journey/<timestamp>.jsonl` files instead of accumulating in one. This degrades (does not
necessarily break) anything that counts or attributes journey events: liveness checks, hand-off counts,
`event_count_gte` grading criteria, and any per-session audit reconstruction.

**Recommended fix:** rewrite `journey_record.py` to parse the JSON payload from stdin per the documented
hook contract, extracting `session_id`, `hook_event_name`, `tool_name`, `tool_input` from there instead
of `os.environ`. Verify with a real session: one continuous learner interaction should produce exactly
one `journey/<session>.jsonl` with populated `tool`/`session` fields on every event.

**Root cause (confirmed):** this is a plugin bug, not a version mismatch. Anthropic's documented hook
contract delivers event data as JSON on stdin (the current contract); the env-var reads are simply
wrong, and upgrading the CLI does **not** fix them — the script must be corrected regardless of
version. Still run the pre-delivery capability check (Workbench update §6-C) on the actual machines to
confirm the hook records stdin correctly.

**Lab 1 mitigation (in place, works regardless of whether this gets fixed):** grading globs all
`journey/*.jsonl` files rather than assuming a single session filename, and the Stage 0 liveness check
verifies a populated event lands rather than asserting exactly one file exists.
See `Lab1_Build_Instructions_Finish_the_Refund.md` §9 item 5, §14.

---

## 2. `planner` agent contract too narrow for reuse across labs

**What's wrong:** `agents/planner.md`'s documented contract: input is a validated `spec.md`; output is
JSON only (no prose), matching a fixed issue schema (`number/title/body/acs/branch`); tools are `Read,
Bash` — no `Write`. Lab 1 needs to feed it a risk register (not a spec) and get a saved markdown plan
back, which is outside both the input shape and the output/tooling contract.

**Recommendation:** either (a) broaden `planner`'s contract to accept arbitrary structured input beyond
`spec.md` and optionally grant `Write` so it can save its own output, or (b) introduce a second,
lab-oriented planning agent/skill with a looser contract, rather than expecting every lab to repurpose
the spec-to-issues planner. Decide before Lab 2 (which uses `planner` as originally intended, from a
validated spec) and Lab 3/4 (which may need the same repurposing Lab 1 does).

**Lab 1 mitigation (in place):** the Stage 2 prompt asks `planner` for JSON only; the **session**, not
the agent, writes `docs/plans/plan.md` from that JSON. See §9 item 6, §11 Stage 2.

---

## 3. `pr-reviewer` agent contract is diff-shaped; being reused against prose

**What's wrong:** `agents/pr-reviewer.md`'s contract: input is a diff + `coding-standards.md`; output is
`file:line`-anchored findings. Lab 1 Stage 2 uses it to review a plan document (prose, no diff, no line
numbers) — a real stretch of its designed output format.

**Recommendation:** either accept per-lab prompt overrides as the norm (tell the agent explicitly not to
use `file:line` format when there's no diff) and document that pattern once, centrally, so every lab
author doesn't rediscover it independently — or evaluate whether `clean-room-judge` (introduced in Lab 3
for fresh-context scoring of non-diff artifacts against a rubric) should be generalized and made
available earlier, since its contract already fits "judge an artifact that isn't a diff" better than
`pr-reviewer`'s does.

**Lab 1 mitigation (in place):** the Stage 2 `pr-reviewer` prompt explicitly asks for prose findings, not
`file:line` references. See §9 item 6, §11 Stage 2.

---

## 4. No shared `/hand-off` command

**What's wrong:** the plugin has `/journey start|stop|export` but no `/hand-off`. Every lab in the
four-lab series wants an identical stage-boundary checkpoint mechanic.

**Recommendation:** once a second lab needs the same behavior, promote a `/hand-off` command into the
shared plugin (model-authored structured checkpoint appended to `docs/workflow-tracker.md` — see the
design note below) rather than continuing to duplicate a lab-local command per lab.

**Design note carried over from Lab 1 (worth keeping when this is promoted):** `/hand-off` should stay a
model-authored narrative checkpoint, not a deterministic script. The deterministic audit backbone is
already `journey_record.py`'s automatic hook capture (once fixed per item 1), which is independent of
what any command writes. Grading should read hook-captured events for pass/fail, and treat
`workflow-tracker.md` as the human-readable record — not the graded evidence. This separation is
deliberate, not a shortcut: it means a thin or occasionally-skipped hand-off never silently breaks
grading integrity. See `Lab1_Build_Instructions_Finish_the_Refund.md` §10.

**Lab 1 mitigation (in place):** built lab-locally as `.claude/commands/hand-off.md`. Do not fold into
the shared plugin as part of Lab 1's build — that is separate Workbench work.

---

## 5. CLI version — required input, not yet confirmed

The plugin is **validated on Claude Code 2.1.177** and **provisionally supported on 2.1.108+** (2.1.108
is a real release; the "PGS runs 2.1.108" figure is verbal/unverified). This is **not a blocker**: rather
than force an enterprise upgrade, run the pre-delivery capability check on the actual lab machines
(Workbench update §6-C — `/lab`, `/grade`, `/hand-off`, rules load, skills resolve, one hook records
stdin, one end-to-end Lab 1 path) and deliver on the installed version if it passes. Newer is not
universally safer, so treat no single version as a magic threshold. Confirm before delivery.

---

## How to use this document

When Workbench build/update work starts: work items 1–4 in roughly that order (1 affects every lab's
audit trail; 2–3 affect any lab that reuses `planner`/`pr-reviewer` outside a spec-to-issues or
diff-review flow; 4 is a straightforward promotion once duplication actually shows up in a second lab).
Confirm item 5 alongside item 1, since they may share a root cause. None of this blocks building or
delivering Lab 1 as currently specified.

---

# Workbench_Changes_Required_For_Lab2

Gaps found while authoring `Lab2_Build_Instructions_Retrieve_Payer_Authentication.md`. As with Lab 1,
none block building or running Lab 2 — the lab ships labeled, working mitigations — but each should be
fixed once in the shared Workbench rather than re-solved per lab. Section 4 confirms Lab 2 becomes the
"second lab" that justifies promoting the shared `/hand-off` flagged in item 4 above.

| # | Required capability | Current actual behavior | Why Lab 2 needs it | Minimum change | Blocks implementation or only delivery? |
|---|---|---|---|---|---|
| L2-1 | **`repo-context-compressor` skill (Tier 1)** | Does not exist in the plugin (`skills/` has no such skill) | Stage 1 has the learner generate the compressed context for the `target-pass-proxy` legacy edge | Add a skill that crawls a repo and emits the compressed-context artifact per the schema in Lab 2 §6 (identity, endpoints, contracts, field map, DOES/DOES-NOT, freshness metadata) | **Only delivery of Stage 1 as designed.** The lab ships the correct compressed artifact as a protected reference, so the lab is fully buildable and runnable without the skill; only the "learner generates it live" experience is affected |
| L2-2 | **PreToolUse PR-gate guard** (block writing the PR body while any required gate is red) | `PreToolUse` runs `journey_record.py` + `quality_gates.py` (PAN/secret) only; no PR-body gate | Stage 6 demonstrates the control physically blocking a PR while gates are red | A PreToolUse hook keyed to PR-creation tool calls that checks gate status and denies until green | **Only delivery.** Built lab-local as `.claude/hooks/pr_gate_guard.py` (same pattern as Lab 1's `reference_guard.py`); promote to the shared plugin |
| L2-3 | **`work-orchestrator` TDD step vs. `sdet-architect`** | `work-orchestrator` SKILL step 2 invokes `sdet-architect` to write failing tests | `sdet-architect` is a Lab 3 introduction; Lab 2 writes tests directly from ACs | Allow `/build` to run with direct-from-AC TDD (or make the TDD step pluggable) so it does not hard-require `sdet-architect` before Lab 3 | **Neither** — Lab 2 mitigates by writing tests directly in Stage 4; note the contract nuance so a future `/build` change does not assume `sdet-architect` is always present |
| L2-4 | **`code-to-spec-validator` taxonomy coverage** | Validates against `references/failure-modes.md` (5 modes) | Must catch the "second billable Authenticate Payer call" (Lab 2 T1) | None required **if** the spec's AC-INCOMPLETE encodes the constraint (it does — maps to the validator's spec-drift / broken-contract coverage). Optional: add a payments-specific "unintended external side effect / billable operation" note to `failure-modes.md` | **Neither** — works as-is given the spec AC; note only |
| L2-5 | **`spec-craft` companion dependency** | `spec-craft` depends on the `superpowers` companion plugin (per `docs/ARCHITECTURE.md`, companion-install mode) | Stage 2 uses `/spec` | None to the Workbench; an environment prerequisite | **Only delivery** — confirm `superpowers` is installed on lab machines (Lab 2 §20 required input) |
| L2-6 | **Java-aware lint/coverage gates** (carryover from Lab 1) | `quality_gates.py` lint/coverage are `ruff`/`pytest`, inert on Java | Both Lab 2 repos are Java | Same as Lab 1 — verification is Maven-native (ArchUnit + JUnit + JaCoCo); plugin gate contributes PAN/secret scan only | **Neither** — already mitigated; same posture as Lab 1 |

| L2-7 | **`work-orchestrator` shells out to `gh` with no error handling** | `pr.py` runs `gh pr create` and `issue.py` runs `gh issue create` with `check=True` | A local, offline lab (participants clone into one workspace) has no authed `gh`/remote; an unhandled `gh` failure would crash the pipeline across live breakout groups | Add a "local-artifact / no-remote" mode to `work-orchestrator` (write `issues.json` + a PR-body file instead of calling `gh`), or wrap the `gh` calls so a missing remote degrades gracefully | **Would block delivery if the shared pipeline ran the `gh` calls** — Lab 2 avoids it by forbidding `gh` in the prompts and writing local artifacts (`issues.json`, `docs/PR_DESCRIPTION.md`); the guard is a path-based Write guard on the PR file. Promote the local-artifact mode so future labs don't rely on prompt discipline alone |
| L2-8 | **`spec_check.py` required-section list has no "Out of scope"** | Required sections are the 7 generic template headers (Context/Scope/Interfaces/Data/Acceptance Criteria/Non-Negotiables/Risks); out-of-scope lives inside `## Scope` | Lab spec-gate determinism depends on knowing exactly what `spec_check.py` catches (missing required section + non-testable `AC-N`) | None required for Lab 2 (the lab anchors its hard gaps on the omitted `## Non-Negotiables` section + a non-testable AC, which `spec_check.py` does catch). Optional: enrich the AC-testability heuristic and/or the section list for PGS-shaped specs | **Neither** — noted so future labs anchor their seeded spec gaps on the deterministic checks, not on model completeness judgment |

### Additional items found while physically building Lab 2

These were found while implementing `lab2-payer-auth/`, after the build instructions were
written. Same rule as above: none blocks the lab, each ships a labeled lab-local mitigation, each
should be fixed once in the shared Workbench.

| # | Required capability | Current actual behavior | Why Lab 2 needs it | Minimum change | Blocks implementation or only delivery? |
|---|---|---|---|---|---|
| L2-9 | **PAN/secret gate that works in a multi-repo workspace** | `quality_gates.py` -> `git_diff.get_diff()` runs `git diff HEAD --` in Claude Code's working directory. In Lab 2 that directory is the *workspace root*, while the Java code lives in two independent git repos beneath it. The gate therefore either throws (no repo at the root -> caught -> silently "skip") or diffs only workspace-level files, and never sees an edit to either service | The PAN gate is the one gate Lab 1 and Lab 2 both call blocking; silently no-opping for a whole session defeats the acceptance-matrix row "PAN gate fires (not skipped)" | Scan the *pending write* from the PreToolUse payload rather than a git diff, or resolve the enclosing git repo of the edited path and diff there | **Only delivery.** Mitigated lab-local as `.claude/hooks/pan_gate.py`, which scans the pending write content (strictly earlier than a diff-based scan). Promote it |
| L2-10 | **Rubric vocabulary cannot count events by type** | `grader.py` supports `event_exists`, `event_contains`, `event_count_gte` (total events only), `secret_scan_clean` | Lab 1 and Lab 2 both grade "at least 7 hand-off boundary events", which none of the four checks can express | Add `event_count_by_type_gte:<type>:<n>` to `score_criterion` | **Neither.** Layer A asserts hand-off events *exist*; the >=7 count is done deterministically in the lab-local `grade_repo.py` (Layer B) |
| L2-11 | **`spec_check.py` AC-testability heuristic matches substrings** | `check_ac_testability` does `keyword in ac_text.lower()` over `given/when/then/must/shall/returns/produces/equals`. "au**then**tication" contains "then", so **any** acceptance criterion that mentions authentication is scored testable regardless of wording | A lab that seeds a deliberately non-testable AC to make the spec gate fire deterministically cannot use the domain's own vocabulary in that AC | Match on word boundaries (`\b(given|when|then|...)\b`) | **Neither.** Lab 2's seeded `AC-3` is worded to avoid the collision ("incomplete stored records", not "incomplete authentication records"), and the gate fires as designed. Any future lab seeding a non-testable AC needs the same care until this is fixed |
| L2-12 | **Issue schema has no repo field** | `planner`'s output schema and `issue.Issue` are `number/title/body/acs/status/branch`; `load_issues` does `Issue(**i)`, so an extra key raises `TypeError` | Multi-repo labs from Lab 2 onward must record which repo each issue touches, and grading checks it | Add an optional `repo` field to the schema and the dataclass | **Neither.** Lab 2 writes `issues.json` as a local file and never calls `issue.load_issues`, so the extra `repo` key is safe here. It would break the moment a lab used the loader |

Items L2-1 and L2-2 are the two worth building at the Workbench level before Lab 2 is delivered live, so
the learner experience is the designed one rather than the facilitator-provided fallback. **L2-7 is the
one with real crash potential if the shared pipeline is used unmodified** — Lab 2 sidesteps it, but the
local-artifact mode should be built so no lab depends on prompt discipline to avoid a `gh` crash. The
hook-payload issue (item 1 above) and its journey-glob mitigation apply unchanged to Lab 2.

---

## Lab 3

Gaps found while authoring `Lab3_Build_Instructions_Region_AP_0200_Sydney.md`. As before, none block
building or running Lab 3 — the lab ships labeled, working mitigations — but each should be fixed once in
the shared Workbench rather than re-solved per lab. Carryover items (hook payload, Java gates, gh/local
artifact, superpowers) apply unchanged.

| # | Required capability | Current actual behavior | Why Lab 3 needs it | Minimum change | Blocks implementation or only delivery? |
|---|---|---|---|---|---|
| L3-1 | **`repo-manifest-sync` skill (Tier 2)** | Does not exist in the plugin | Stage 1 declares a five-repo manifest and syncs the whole working set's compressed context | Add a skill that reads `repos.manifest.json`, produces/refreshes each repo's compressed context, tracks freshness via a source hash, and exits non-zero on an unresolved repo (schema in Lab 3 §7) | **Only delivery of Stage 1 as designed.** Lab ships a lab-local `repo_manifest_sync.py` + the correct synced contexts as a protected reference — fully buildable/runnable without the skill |
| L3-2 | **Local (no-CI) risk-score gate** | `release-risk-scorer` is a **Lab 4 CI/GitHub stub** — `scripts/risk_scorer.py` is unimplemented, it reads `GITHUB_PR_NUMBER` and posts a GitHub check run; unusable in a local, no-`gh` lab | Stage 5 must run a risk gate locally and demonstrably block a reverted dangerous change | Provide a local risk-gate mode that scores the working-tree diff against `references/risk-weight-table.yaml` and blocks locally (no `gh`, no CI) | **Only delivery.** Built lab-local as `.claude/scripts/risk_gate.py` reusing the existing `risk-weight-table.yaml`. Do **not** wire the Lab 4 `release-risk-scorer` skill here. Promote a local mode |
| L3-3 | **PITest mutation testing not wired into `quality_gates.py`** | `quality_gates.py` lint/coverage are ruff/pytest (inert on Java); no mutation testing anywhere in the plugin | Lab 3's centerpiece proof is mutation SURVIVED→KILLED | None to the Workbench — PITest is **Maven-native** (`org.pitest:pitest-maven`) configured per repo `pom.xml` and run via `mvn ... org.pitest:pitest-maven:mutationCoverage` | **Neither** — Maven-native; noted so a future gate that claims "mutation coverage" is understood to be Maven, not a plugin skill |
| L3-4 | **`clean-room-judge` evidence packaging is manual** | The agent exists (`agents/clean-room-judge.md`) and is correctly context-isolated, but nothing in the plugin assembles/validates the evidence package it should receive | Lab 3 must feed it an isolated file-based evidence package (strategy + contract + degraded + mutation + risk results) with no builder history | Optional: a helper that assembles the evidence package deterministically. Not required — the lab specifies the file set explicitly | **Neither** — noted so future labs assemble judge evidence as files, not conversation |
| L3-5 | **`sdet-architect` `coverage_map.py` is AC-comment/Python-oriented** | Maps ACs→test files by scanning for `AC-<n>` comments in a test dir; no coverage % and Java test-dir globbing is best-effort | Lab 3 uses `/test-strategy` and `/build-tests` on Java/Maven repos | None required — treat its AC-to-test mapping as advisory; real coverage is JaCoCo, real test quality is PITest | **Neither** — noted so its output isn't mistaken for a coverage or quality metric |
| L3-6 | **Dependency/CVE scan gate absent from the plugin** | `quality_gates.py` has no dependency/CVE scan; the plugin ships no SCA gate. Mastercard non-negotiable: no CVSS ≥ 7 | Stage 5 must run a CVE gate and demonstrably block a known-CVE dependency (design authority + traceability map this to Lab 3 Stage 5) | None to the Workbench — CVE scan is **Maven-native** (`org.owasp:dependency-check-maven`, `failBuildOnCVSS=7`, standing in for Black Duck), run per repo. **No-network:** needs a pre-warmed local NVD cache (`autoUpdate=false` on session day) | **Only delivery** — Maven-native and lab-local; noted so a future plugin gate can absorb SCA. Do not block the build |

L3-1 and L3-2 are the two worth building at the Workbench level before Lab 3 is delivered live, so the
learner experience is the designed one rather than the facilitator-provided fallback. Neither blocks the
build. The `risk-weight-table.yaml` reference already exists in the plugin and is reused by Lab 3 (local
gate) and carried into Lab 4 (`release-risk-scorer`), so no new weights file is invented.

---

## Lab 4

Gaps found while authoring `Lab4_Build_Instructions_Make_It_Everyones_Default.md`. Lab 4's subject **is**
the Workbench, so unlike Labs 1–3 it does not just ship a labeled lab-local mitigation for every gap — it
is the lab where several of these get **fixed centrally**, in the plugin itself, because the cohort is the
one fixing them. Carryover items (hook payload, Java-inert gates, superpowers, CLI version) apply unchanged
and are not re-litigated here.

| # | Required capability | Current actual behavior | Why Lab 4 needs it | Minimum change | Resolved in Lab 4 or deferred? |
|---|---|---|---|---|---|
| L4-1 | **`pr.py`/`issue.py` shell out to `gh` with `check=True`, no local mode (carries L2-7 forward)** | Both call `subprocess.run([...], check=True)` against `gh pr create`/`gh issue create`/etc. with no fallback | All three CI skills (`red-team-review`, `test-maintainer`, `release-risk-scorer`) must run headless with no `gh`/credentials assumed | Add a local-artifact mode to `pr.py`/`issue.py`: write `findings.json` / a draft-fix patch+note / `risk-score.json`+`check-result.json` locally when no remote is configured, instead of crashing | **RESOLVED IN LAB 4 (Stage 1)** — this is the one fix Lab 4 treats as load-bearing for the other three stages, not optional |
| L4-2 | **`secret_scan.py` has no hardcoded-URL/hostname detection pattern** | `_SECRET_PATTERNS` only matches password/secret/api_key/token/auth/bearer assignments; `pan-patterns.txt` only has PAN/Track-2 regexes — neither matches a bare hardcoded endpoint like `https://acquirer.internal.local/...` | `red-team-review`'s payoff demo depends on deterministically re-finding Lab 1's F9 (hardcoded acquirer URL) without relying on model judgment | Add a URL/hostname regex to `secret_scan.py`/`pan-patterns.txt` (e.g. matching internal hostnames/schemes not in an allow-list) | **RESOLVED IN LAB 4 (Stage 1)** — added alongside the local-artifact mode; `red-team-review`'s F9 claim is conditional on this landing first |
| L4-3 | **`repo-context-compressor` skill (Tier 1) does not exist** (carries L2-1 forward) | No code anywhere in the plugin; Lab 2 shipped only a static `target-pass-proxy.context.md` reference artifact | Lab 4 promotes Tier 1 into a real, general-purpose skill | Author the skill fresh, using the Lab 2 artifact's structure (identity/endpoints/contracts/field-map/DOES-DOES-NOT/freshness) as the target output schema | **RESOLVED IN LAB 4 (Stage 5)** — authored new, not hardened, since there was no prior code (§10 of the Lab 4 doc) |
| L4-4 | **`repo-manifest-sync` skill (Tier 2) does not exist as a shared skill** (carries L3-1 forward) | Only exists as Lab 3's lab-local `repo_manifest_sync.py`, hardcoded to Lab 3's five-repo manifest | Lab 4 promotes Tier 2 into a shared, general-purpose skill | Generalize Lab 3's working script to accept an arbitrary manifest, add freshness/`source_hash`, `UNRESOLVED`-on-missing error handling, and a pytest test | **RESOLVED IN LAB 4 (Stage 5)** — smaller lift than L4-3 since real working code already exists |
| L4-5 | **`marketplace/.claude-plugin/marketplace.json` does not exist** | `docs/ARCHITECTURE.md` references a marketplace manifest, but no `marketplace/` directory is present anywhere in the plugin repo | Lab 4 must validate, version, publish, and prove sync of the plugin | Create `marketplace/.claude-plugin/marketplace.json` with a local-dev entry (`source: ../workbench`) | **RESOLVED (Workbench 0.2.0)** — created in the shared update because Labs 1–3 need distribution; Lab 4 Stage 5 then **version-bumps, re-publishes, and proves teammate sync** against the existing manifest (real distribution URL is a later, gated swap) |
| L4-6 | **`red-team-review`, `test-maintainer`, `release-risk-scorer` are unimplemented Lab-4 stubs** | Each `SKILL.md` exists with "LAB 4 STUB" in its description; scripts (`red_team.py`, `maintainer.py`, `risk_scorer.py`) are not implemented | This is Lab 4's core deliverable | Author each script per its documented contract (Lab 4 doc §7–§9), importing from `scripts/lib/` — no duplicated logic | **RESOLVED IN LAB 4 (Stages 2–4)** — the stubs' documented contracts already match; nothing to reconcile, only to implement |
| L4-7 | **No shared `/hand-off` command in the plugin** (carries item 4 forward) | Every lab (1–4) reimplements it lab-locally as `.claude/commands/hand-off.md` | Lab 4 is the 4th consumer of the identical pattern — the strongest case yet for promotion | Promote the existing lab-local design (model-authored checkpoint appended to `docs/workflow-tracker.md`, graded off hook-captured journey events, not off the hand-off text itself) into the shared plugin | **OPTIONAL PROMOTE** — promote if Stage 5 has time; otherwise keep lab-local and do not block delivery |
| L4-8 | **No shared PR-gate guard in the plugin** (carries L2-2 forward) | Each lab reimplements `pr_gate_guard.py` lab-locally (Lab 2/3 pattern) | Lab 4's local-artifact PR/check-run outputs would benefit from the same block-while-red guard | Promote the path-based Write-guard pattern into the shared plugin, generalized to the local-artifact filenames Lab 4 introduces (`findings.json`, `risk-score.json`, etc.) | **OPTIONAL PROMOTE** — same posture as L4-7; not required for Lab 4 to work |
| L4-9 | **Hook payload env-vars-vs-stdin bug** (carries item 1 forward), **planner/pr-reviewer contract narrowness** (items 2–3), **Java-inert `quality_gates.py`** (L2-6), **no dependency/CVE gate** (L3-6) | Unchanged from prior labs' findings | Outside Lab 4's teaching path (skill-authoring and CI-agentic patterns, not journey plumbing or Java build gates) | No change from Lab 4 | **DEFERRED** — logged here for the Workbench build pass; Lab 4's own grading globs `journey/*.jsonl` so item 1 does not block it |

**L4-1 and L4-2 are the two Lab 4 treats as prerequisites for its own Stage 2–4 work**, not just nice-to-haves
— `red-team-review`, `test-maintainer`, and `release-risk-scorer` all depend on the local-artifact mode, and
`red-team-review`'s F9 payoff specifically depends on L4-2. **L4-3/L4-4/L4-5/L4-6 are Lab 4's actual
deliverables** — by design, this is the lab that fixes them, not one that routes around them. L4-7/L4-8 are
optional promotions if time allows. L4-9 is carried forward unchanged and intentionally out of scope.
