# U3: journey-recorder — Forge primitive contract

## Purpose

Always-on hook adapter that captures every lab activity event to an append-only JSONL file.
Every tool call, user prompt, and session lifecycle event is recorded without interrupting the AI
session. The resulting `.forge/journey/<run-id>.jsonl` is the raw audit trail consumed by U2
(`/lab-grader`) and U4 (`/journey-curator`).

## Layer

L2 Universal (every modernized Forge lab MUST ship this primitive — see Project 2 §4.2).
Unlike U1 and U2, U3 has no Python CLI entry point; it is a hook-only primitive implemented
entirely in shell (`primitives/_recorder.sh`) with thin harness-specific wrappers.

## Trigger events

U3 responds to five Claude Code / Copilot lifecycle events:

| Hook event | Journey event type emitted | Description |
|---|---|---|
| `SessionStart` | `session_start` | AI session opened; captures harness, user, lab metadata |
| `UserPromptSubmit` | `user_prompt_submit` | User sends a prompt; `prompt_text` field subject to hash+preview policy |
| `PreToolUse` | `pre_tool_use` | Before any tool fires; captures `tool_name`, `tool_input_text` |
| `PostToolUse` | `post_tool_use` | After a tool completes; captures `tool_name`, `tool_result_text` |
| `SessionEnd` | `session_end` | AI session closed; triggers optional U4 invocation |

Additional event types emitted by other primitives and written through U3's recorder:

| Event type | Emitted by | Description |
|---|---|---|
| `file_changed` | Hook (PostToolUse on Write/Edit tools) | File path + diff summary written to lab |
| `confidence_score` | F1 `/confidence-score` (optional) | Per-prompt confidence signal |
| `failure_mode_finding` | U1 `/failure-mode-audit` | FM1-FM5 finding detected |
| `lab_grader_run` | U2 `/lab-grader` | Grading session result |
| `journey_curator_run` | U4 `/journey-curator` | Curation run completed |

## Output

All events are appended to:

```
<lab-root>/.forge/journey/<run-id>.jsonl
```

- One JSON object per line (newline-delimited JSON, not a JSON array).
- File is created on first event; directory is created if absent.
- `<run-id>` is read from `<lab-root>/.forge/.current-run-id` (written by `SessionStart` hook).
  Falls back to `run_unknown` if the file is absent.
- The file is **append-only**; no existing lines are ever modified or deleted.

## Default event schema (Spec A §8.2)

Every event MUST contain these base fields:

| Field | Type | Description |
|---|---|---|
| `event_id` | string (ULID or `evt_<hex20>`) | Unique event identifier |
| `run_id` | string | Session run identifier (from `.forge/.current-run-id`) |
| `timestamp` | ISO 8601 UTC string | Time the event was recorded |
| `type` | string | Event type (see trigger table above) |
| `harness` | `"claude-code"` or `"copilot"` | Which AI harness emitted the event |
| `user_id` | string or null | Lab user identifier (from env `FORGE_USER_ID` if set) |
| `cohort_id` | string or null | Cohort identifier (from env `FORGE_COHORT_ID` if set) |
| `lab_slug` | string or null | Lab identifier (from env `FORGE_LAB_SLUG` if set) |
| `session_seq` | integer | Monotonically increasing counter within the run |

Event-specific fields are appended alongside these base fields. Examples:

```jsonc
// session_start
{ "event_id": "evt_a1b2c3d4e5f6a7b8c9d0", "run_id": "run_x9y8z7...", "timestamp": "2026-04-18T10:00:00Z",
  "type": "session_start", "harness": "claude-code", "user_id": null, "cohort_id": null,
  "lab_slug": "forge-python-tdd", "session_seq": 1 }

// user_prompt_submit (text fields hashed + previewed per §hash-redact-policy)
{ "event_id": "evt_...", "run_id": "run_...", "timestamp": "2026-04-18T10:01:15Z",
  "type": "user_prompt_submit", "harness": "claude-code", "session_seq": 2,
  "prompt_text": "Write a pytest test for...",
  "prompt_text_hash": "a3f9c2b1e8d47f05",
  "prompt_text_preview": "Write a pytest test for..." }

// pre_tool_use
{ "type": "pre_tool_use", "tool_name": "Write", "tool_input_text": "{\"path\": \"src/...\"}",
  "tool_input_text_hash": "...", "tool_input_text_preview": "...", "session_seq": 3, ... }

// post_tool_use
{ "type": "post_tool_use", "tool_name": "Write", "tool_result_text": "File written successfully.",
  "tool_result_text_hash": "...", "tool_result_text_preview": "...", "session_seq": 4, ... }

// session_end
{ "type": "session_end", "session_seq": 5, ... }
```

## Hash + preview policy (Spec A §8.3)

Any field whose key ends in `_text` is subject to the two-tier redaction contract enforced by
`primitives/_recorder.sh`:

1. **`*_hash`** — SHA-256 digest of the raw value, truncated to 16 hex characters. Always written.
2. **`*_preview`** — First 80 characters of the raw value, with secrets redacted via
   `redact_preview()`. Patterns redacted: Anthropic API keys (`sk-ant-*`), GitHub PATs (`ghp_*`),
   AWS access key IDs (`AKIA*`), and bare `password=` / `password:` assignments.
3. The raw `*_text` value is retained in the **local** JSONL only (tier-2 data). It is
   **never** sent to the telemetry backend unless the user opts in to tier-2 upload.

## Two-tier telemetry

| Tier | Content | Upload condition |
|---|---|---|
| Tier 1 | All fields except raw `*_text` values (`*_hash` + `*_preview` instead) | Always — on `session_end` event, metadata is forwarded to `services/telemetry` |
| Tier 2 | Full JSONL including raw `*_text` fields | Opt-in only — user prompted by U4 `/journey-curator` at session end; requires explicit `FORGE_TIER2_CONSENT=1` env var |

## Lab-extensible event types

Labs may declare additional event types beyond the defaults. Declare them in:

```
<lab-root>/.forge/journey-schema.yaml
```

Example:

```yaml
# .forge/journey-schema.yaml
lab: forge-python-tdd
extra_event_types:
  - type: test_run_complete
    description: "pytest run finished; captures pass/fail counts"
    fields:
      passed: integer
      failed: integer
      duration_s: float
  - type: refactor_applied
    description: "Student applied a refactor suggestion"
    fields:
      target_file: string
      strategy: string
```

The schema file is informational only; U3's recorder writes any JSON object it receives without
schema validation. Validation (if desired) is the lab author's responsibility via a custom U2
rubric criterion.

## Recorder implementation

The shared recorder logic lives at `primitives/_recorder.sh`. Both harness adapters delegate to
it. The script:

1. Reads event JSON from stdin.
2. Computes `*_hash` and `*_preview` for all `*_text` fields (via embedded Python).
3. Sets `timestamp` if not already present.
4. Appends the enriched JSON to `.forge/journey/<run-id>.jsonl`.
5. Creates the `.forge/journey/` directory if absent.

## Adapters

### Claude Code (`adapters/claude_code/`)

- **`settings-snippet.json`** — JSON fragment merged into a lab's `.claude/settings.json`. Registers
  one hook per lifecycle event (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
  `SessionEnd`). Each hook calls `record-hook.sh <event-type> [tool-name] [payload]`.
- **`record-hook.sh`** — Thin wrapper that builds the event JSON object, determines the current
  `run_id` from `.forge/.current-run-id` (creating the file on `SessionStart`), and pipes to
  `primitives/_recorder.sh`.

Merge command (run during `forge sync`):

```bash
forge sync journey-recorder --harness claude-code
# Merges settings-snippet.json into .claude/settings.json (deep-merge hooks array)
```

### Copilot (`adapters/copilot/`)

- **`hooks-snippet.json`** — JSON fragment merged into a lab's `.github/hooks/journey-recorder.json`.
  Since VS Code Copilot ≥ 1.109.3 (January 2026), Copilot reads the same hook format as
  Claude Code. U3 registers hooks for the same 4 lifecycle events as Claude Code:

  | Hook event | Journey event type |
  |---|---|
  | `SessionStart` | `session_start` |
  | `PreToolUse` | `pre_tool_use` |
  | `PostToolUse` | `post_tool_use` |
  | `SessionEnd` | `session_end` |

  `UserPromptSubmit` has no direct Copilot analogue. The first `PreToolUse` in a session
  carries the initial user prompt context through `$COPILOT_USER_INPUT` when available.

  **Caveats:** VS Code Copilot ignores matcher values (hooks fire on ALL tool invocations).
  JetBrains Copilot does not support hooks at all.

- **`record-hook.sh`** — Same structure as the Claude Code variant but sets `harness: copilot`.

Merge command:

```bash
forge sync journey-recorder --harness copilot
# Merges hooks-snippet.json into .github/hooks/journey-recorder.json
```
