# /journey-curator — GitHub Copilot adapter

Copilot-side counterpart to the Claude Code sub-agent adapter. Both share `shared/curator.py`.

## What lands in a lab repo

When `forge sync` runs in a lab, contents of `github-bundle/` merge into the lab's `.github/`:

- `.github/agents/journey-curator.agent.md` — the Copilot custom-agent manifest
- `.github/prompts/journey-curator.prompt.md` — slash-command prompt for direct invocation

The lab's `.github/copilot-instructions.md` (thin) cross-references both.

## Notes for adapter authors

- The agent invokes `python .forge/primitives/journey_curator/shared/curator.py` — this path is
  resolved after `forge sync` places the primitive library under `.forge/primitives/`.
- `model_logical="default"` maps to Sonnet 4.6 via the lab's configured `LLM_PROXY_URL`. Do not
  hardcode model IDs here.
- `EXAMPLES.md` in the parent `journey_curator/` directory covers the three canonical use-cases.
