---
name: journey-recorder
description: Always-on hook adapter that records Copilot lifecycle events (SessionStart, PreToolUse, PostToolUse, SessionEnd) to an append-only JSONL file at .forge/journey/<run-id>.jsonl. Uses the Claude Code hook format natively supported by VS Code Copilot >=1.109.3. Sensitive text is hashed (SHA-256, 16-char) and redacted before storage. Registered via forge sync — does not need to be invoked manually.
---

# journey-recorder — Copilot adapter

Registers the `journey_recorder` hooks in a lab's `.github/hooks/journey-recorder.json` so that every Copilot session activity is captured without any manual step.

## What it does

`forge sync` deep-merges `hooks-snippet.json` into the lab's `.github/hooks/journey-recorder.json`. Once merged, VS Code Copilot (≥ 1.109.3) fires `record-hook.sh` on the 4 registered lifecycle events, which builds a structured JSON event and pipes it to the shared `primitives/journey_recorder/shared/recorder.sh`. The recorder appends the event (with hash + preview for any `*_text` fields) to `.forge/journey/<run-id>.jsonl`.

## Hook format

Since January 2026, VS Code Copilot reads the same hook format as Claude Code:

```json
{ "hooks": { "EventName": [{ "type": "command", "command": "..." }] } }
```

Both harness adapters now use this unified format. VS Code Copilot also reads `.claude/settings.json` directly, so a single hook configuration can serve both harnesses in practice.

## Event mapping

U3 registers hooks for 4 lifecycle events:

| Hook event       | Journey event type |
|---|---|
| `SessionStart`   | `session_start`    |
| `PreToolUse`     | `pre_tool_use`     |
| `PostToolUse`    | `post_tool_use`    |
| `SessionEnd`     | `session_end`      |

`UserPromptSubmit` has no direct Copilot analogue. The first `PreToolUse` in a session carries the initial user prompt context through `$COPILOT_USER_INPUT` when available.

## Caveats

- **Matchers are ignored** — VS Code Copilot fires hooks on ALL tool invocations regardless of matcher values. The `"matcher": ".*"` in the snippet is for Claude Code compatibility only.
- **JetBrains not supported** — Copilot in JetBrains IDEs has no hook system. Labs targeting JetBrains must rely on MCP tools or manual invocation.

## Merge semantics

`forge sync` performs a **deep-merge** — it appends to existing hooks arrays rather than replacing them. Labs that already have hooks for other purposes are not affected. See `README.md` in the journey_recorder directory for details.

## Files shipped by forge sync

| Source (primitive library) | Destination (lab) |
|---|---|
| `adapters/copilot/hooks-snippet.json` | merged into `.github/hooks/journey-recorder.json` |
| `adapters/copilot/record-hook.sh` | `.forge/primitives/journey_recorder/adapters/copilot/record-hook.sh` |
| `shared/recorder.sh` (via `primitives/journey_recorder/shared/recorder.sh`) | `.forge/primitives/journey_recorder/shared/recorder.sh` |

## Invariants

- Logic lives in `primitives/journey_recorder/shared/recorder.sh` in the Forge primitive library.
- DO NOT modify `record-hook.sh` or `hooks-snippet.json` directly in a lab — changes are overwritten on the next `forge sync`. Upstream changes flow through the library.
- The raw `*_text` payload is kept only in the local JSONL. Only `*_text_hash` and `*_text_preview` (80-char, secrets redacted) are forwarded to the telemetry pipeline.
