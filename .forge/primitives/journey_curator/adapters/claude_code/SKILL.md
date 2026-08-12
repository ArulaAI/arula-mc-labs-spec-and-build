---
name: journey-curator
description: Synthesise a journey.md student artifact from session journey events. Reads .forge/journey/<run-id>.jsonl (and optional grade.json), calls Sonnet 4.6 via llm-proxy with an 8-section structured prompt, and writes a human-readable journey.md. Also triggered automatically by the SessionEnd hook. This adapter is implemented as a Claude Code sub-agent definition.
---

# /journey-curator

Claude Code adapter for the Forge primitive library U4 primitive.

This is a **sub-agent** adapter. The entry-point is `journey-curator.md` (a CC sub-agent manifest),
not a bare SKILL invocation. Install by copying `journey-curator.md` to `.claude/agents/` in the lab.

## When invoked

1. Determine the run ID — user-supplied, else read `.forge/.current-run-id`, else error.
2. Delegate to the `journey-curator` sub-agent (`.claude/agents/journey-curator.md`).
3. The sub-agent reads the journey JSONL, calls the curator, and prints a brief summary.

## Direct invocation (fallback)

```bash
bash <skill_dir>/invoke.sh --run-id <run-id> [--lab-root <path>]
```

## Output expectations

- Always confirm the path of the written `journey.md`.
- Print a 3-5 sentence human summary of what the artifact covers.
- If JSONL is missing, surface the error and remind the user to run a session with U3 first.

## Invariants

- Logic lives in `primitives/journey_curator/shared/curator.py` in the Forge primitive library.
- DO NOT modify `invoke.sh` or duplicate curator logic — primitive library upgrades flow through `forge sync`.
- LLM calls go through `services/llm-proxy` (model_logical="default" → Sonnet 4.6). Never call Bedrock directly.
