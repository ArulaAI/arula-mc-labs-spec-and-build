# journey-recorder — Claude Code adapter

## Merge semantics

`forge sync` deep-merges `settings-snippet.json` into the lab's `.claude/settings.json` **by appending to existing hook arrays**, not by replacing the entire `hooks` object. This means:

- If a lab already has a `PreToolUse` hook for `failure-mode-audit`, the journey-recorder hook is appended as a second entry in that array.
- The order of hooks within an array follows Claude Code's execution order (first registered, first fired).
- Other top-level keys in `.claude/settings.json` (e.g. `permissions`, `env`) are never touched.

### Manual merge (if forge sync is not available)

Copy the `hooks` object from `settings-snippet.json` and append each event's array entries into the corresponding array in your lab's `.claude/settings.json`. Example:

```json
{
  "hooks": {
    "PreToolUse": [
      { "...existing hook..." },
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .forge/primitives/journey_recorder/adapters/claude_code/record-hook.sh pre_tool_use \"$CLAUDE_TOOL_NAME\" \"$CLAUDE_TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

## run-id lifecycle

`record-hook.sh` creates `.forge/.current-run-id` on the first event of a session and reads it on all subsequent events. This file is `.gitignore`d (added by `forge init`). Each new session gets a fresh UUID-based run-id prefixed with `run_`.
