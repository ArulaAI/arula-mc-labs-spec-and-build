---
name: journey-recorder
description: Always-on hook adapter that records every Claude Code lifecycle event (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, SessionEnd) to an append-only JSONL file at .forge/journey/<run-id>.jsonl. Sensitive text is hashed (SHA-256, 16-char) and redacted before storage. Registered via forge sync — does not need to be invoked manually.
---

# journey-recorder — Claude Code adapter

Registers the `journey_recorder` hook in a lab's `.claude/settings.json` so that every session activity is captured without any manual step.

## What it does

`forge sync` deep-merges `settings-snippet.json` into the lab's `.claude/settings.json`. Once merged, Claude Code fires `record-hook.sh` on each of the 5 supported lifecycle events, which builds a structured JSON event and pipes it to the shared `primitives/journey_recorder/shared/recorder.sh`. The recorder appends the event (with hash + preview for any `*_text` fields) to `.forge/journey/<run-id>.jsonl`.

## Merge semantics

`forge sync` performs a **deep-merge** — it appends to existing hook arrays rather than replacing them. Labs that already have PreToolUse hooks for other purposes are not affected. See `README.md` in this directory for details.

## Files shipped by forge sync

| Source (primitive library) | Destination (lab) |
|---|---|
| `adapters/claude_code/settings-snippet.json` | merged into `.claude/settings.json` |
| `adapters/claude_code/record-hook.sh` | `.forge/primitives/journey_recorder/adapters/claude_code/record-hook.sh` |
| `shared/recorder.sh` (via `primitives/journey_recorder/shared/recorder.sh`) | `.forge/primitives/journey_recorder/shared/recorder.sh` |

## Invariants

- Logic lives in `primitives/journey_recorder/shared/recorder.sh` in the Forge primitive library.
- DO NOT modify `record-hook.sh` or `settings-snippet.json` directly in a lab — changes are overwritten on the next `forge sync`. Upstream changes flow through the library.
- The raw `*_text` payload is kept only in the local JSONL. Only `*_text_hash` and `*_text_preview` (80-char, secrets redacted) are forwarded to the telemetry pipeline.
