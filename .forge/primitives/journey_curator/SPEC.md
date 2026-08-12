# U4: journey-curator — Forge primitive contract

## Purpose

LLM-backed sub-agent that synthesises a student's lab journey into a concise,
structured markdown artifact (`journey.md`). The curator reads the append-only
JSONL produced by U3 (`journey-recorder`) and the optional `grade.json` written
by U2 (`lab-grader`), then calls the LLM to produce a structured student report
covering 8 defined sections. Students keep this artifact; coaches read it.

## Layer

L2 Universal (every modernised Forge lab SHOULD ship this primitive — see
Project 2 §4.2). Depends on: U3 (JSONL source), optionally U2 (`grade.json`).

## Trigger

`/journey-curator` is invoked in two ways:

1. **Automatic** — U3's `SessionEnd` hook adapter calls the curator after each
   session ends. Set `FORGE_CURATOR_AUTO=1` to enable (default: disabled so
   developers can choose timing).
2. **Manual** — Claude Code slash command `/journey-curator` or Copilot prompt
   `journey-curator.prompt.md`. The student (or coach) can re-run the curator
   at any time against any `<run-id>`.

## Inputs

| Input | Location | Required |
|---|---|---|
| Journey events JSONL | `.forge/journey/<run-id>.jsonl` | Yes |
| Grader result JSON | `.forge/journey/<run-id>/grade.json` | No (optional) |
| `lab_root` | Path to the lab directory (default: CWD) | Yes |
| `run_id` | Session run identifier | Yes |
| `llm_backend` | `LLMBackend` instance (BedrockBackend or MockBackend) | Yes |

## Outputs

| Output | Location | Description |
|---|---|---|
| `journey.md` | `.forge/journey/<run-id>/journey.md` | Student artifact — 8-section structured markdown |
| `journey_curator_run` event | `.forge/journey/<run-id>.jsonl` | Appended after curation completes |

## LLM call details

- **Model logical name:** `"default"` (resolves to Sonnet 4.6 via llm-proxy)
- **Max tokens:** 2048
- **Temperature:** 0.0 (deterministic)
- **Prompt:** Structured system prompt (8 sections) + user message (JSONL content
  + optional grade summary, truncated to 6000 chars)

## Structured prompt — 8 sections (Spec A §8.4)

The LLM MUST produce valid Markdown covering these sections in order:

1. **Session Timeline** — chronological summary of events (tool calls, prompts,
   key moments)
2. **Primitives Used** — by layer:
   - L1 native (Claude Code / Copilot built-ins used)
   - L2 Forge (which universals fired: recorder, grader, curator, etc.)
   - L3 per-lab (custom primitives authored during the session)
3. **Workflows Attempted** — map observed sequences to W1-W15 from the Forge
   Prowess curriculum catalog
4. **Failure Modes Encountered** — any FM1-FM5 findings recorded as
   `failure_mode_finding` events; include severity and count
5. **Golden Prompts** — prompts that produced the highest-quality or most
   efficient results (inferred from tool success + low backtracking)
6. **Stuck Points** — where the session stalled, backtracked, or repeated
   unsuccessful patterns
7. **Harness Comparison** — statistics comparing Claude Code vs Copilot tool
   calls if both harnesses appear in the session JSONL; otherwise note which
   single harness was used and any harness-specific observations
8. **What to Try Next** — 3-5 concrete, actionable next steps tailored to the
   student's demonstrated gaps

## Privacy note

The curator operates on tier-1 data by default (hashed + previewed `*_text`
fields). Raw `*_text` values are present in the local JSONL (tier-2) but are
NOT uploaded unless the user opts in via `FORGE_TIER2_CONSENT=1`.

The curator reads the **local** JSONL, so it sees raw text. The `journey.md`
artifact written by the curator is tier-1: it summarises content but MUST NOT
reproduce verbatim secret values.

## Adapter pointer

Harness adapters live in `adapters/claude_code/` and `adapters/copilot/`.
See `EXAMPLES.md` for invocation patterns.
