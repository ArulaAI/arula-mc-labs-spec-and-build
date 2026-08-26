#!/usr/bin/env bash
# Thin wrapper: the real logic lives in bootstrap_workspace.py (cross-platform, including
# native Windows, where this .sh cannot run at all). Kept so the existing invocation below
# still works unchanged on macOS/Linux/Git Bash/WSL.
#
# Usage:  .claude/scripts/bootstrap_workspace.sh
# Windows (no bash): python3 .claude/scripts/bootstrap_workspace.py

set -euo pipefail
PY=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
exec "$PY" "$(dirname "${BASH_SOURCE[0]}")/bootstrap_workspace.py"
