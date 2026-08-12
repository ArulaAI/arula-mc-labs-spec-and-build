#!/usr/bin/env bash
# PreToolUse guard, matched on Write only (see .claude/settings.json). Blocks a write to
# docs/plans/pr-body.md unless `mvn verify` (coverage threshold, lint, secret/dependency scan)
# passes clean. No-op for every other Write target.
set -uo pipefail

TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

case "$TOOL_INPUT" in
  *docs/plans/pr-body.md*)
    if ! mvn -q verify > /tmp/quality-gates-guard.log 2>&1; then
      echo "quality_gates: mvn verify failed — docs/plans/pr-body.md may not be written until gates are clean. See /tmp/quality-gates-guard.log" >&2
      exit 2
    fi
    ;;
esac

exit 0
