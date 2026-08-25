#!/usr/bin/env bash
# Thin wrapper: the real logic lives in validate_spec.py (cross-platform, including native
# Windows, where this .sh cannot run at all). Kept so the existing invocation below still
# works unchanged on macOS/Linux/Git Bash/WSL.
#
# Usage:  .claude/scripts/validate_spec.sh <path/to/spec.md>
# Windows (no bash): python3 .claude/scripts/validate_spec.py <path/to/spec.md>

set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/validate_spec.py" "$@"
