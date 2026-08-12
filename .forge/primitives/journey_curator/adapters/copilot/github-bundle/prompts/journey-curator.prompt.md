---
mode: agent
description: Run the Forge U4 /journey-curator primitive to synthesise a journey.md student artifact from this lab session's events.
---

# /journey-curator

Show me what worked best for me in this lab session.

Invoke the `journey-curator` agent for run ID `{input:run-id|latest}`.

The agent will:

1. Locate the journey JSONL recorded by U3 journey-recorder under `.forge/journey/`.
2. Call `curator.py` (Sonnet 4.6 via llm-proxy) with an 8-section structured prompt covering:
   session timeline, primitives used, workflows attempted, failure modes encountered, golden
   prompts, stuck points, harness comparison, and what to try next.
3. Write `journey.md` to `.forge/journey/<run-id>/journey.md`.
4. Present the artifact path and a 3-sentence summary.

If no run ID is provided (`latest`), the agent resolves the most recent run from
`.forge/.current-run-id`.

If exit code is non-zero, STOP and surface the error output — do not attempt to interpret
partial results.
