#!/usr/bin/env bash
# record-hook.sh — thin wrapper called by Claude Code lifecycle hooks.
# Builds a journey event JSON and pipes it to the shared _recorder.sh.
#
# Usage:
#   record-hook.sh <event_type> [<tool_name>] [<payload>]
#
# Claude Code environment variables consumed:
#   CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT, CLAUDE_TOOL_RESULT, CLAUDE_USER_PROMPT
#
# Non-fatal: if recorder fails, hook exits 0 to avoid blocking Claude Code.
set -euo pipefail

EVENT_TYPE="${1:-unknown}"
TOOL_NAME="${2:-}"
PAYLOAD="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Resolve or create the stable run-id for this session.
RUN_ID_FILE="$LAB_ROOT/.forge/.current-run-id"
mkdir -p "$LAB_ROOT/.forge"
if [ ! -f "$RUN_ID_FILE" ]; then
    python3 -c 'import uuid; print("run_" + uuid.uuid4().hex[:20])' > "$RUN_ID_FILE"
fi
RUN_ID="$(cat "$RUN_ID_FILE")"

EVENT_ID="evt_$(python3 -c 'import uuid; print(uuid.uuid4().hex[:20])')"

# Build event JSON via Python to handle escaping safely.
python3 - <<PYEOF | bash "$SCRIPT_DIR/../../shared/recorder.sh" "" "$LAB_ROOT" "$RUN_ID" || true
import json, sys

event = {
    "event_id": "$EVENT_ID",
    "run_id": "$RUN_ID",
    "type": "$EVENT_TYPE",
    "harness": "claude-code",
    "cohort_id": None,
}

tool_name = """$TOOL_NAME"""
if tool_name:
    event["tool_name"] = tool_name

payload = """$PAYLOAD"""
if payload:
    if "$EVENT_TYPE" == "user_prompt_submit":
        event["prompt_text"] = payload
    elif "$EVENT_TYPE" in ("pre_tool_use", "post_tool_use"):
        event["args_text"] = payload

print(json.dumps(event))
PYEOF
