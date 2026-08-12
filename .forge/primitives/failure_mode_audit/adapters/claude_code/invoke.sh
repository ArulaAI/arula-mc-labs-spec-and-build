#!/usr/bin/env bash
# U1 /failure-mode-audit — Claude Code adapter invoke script.
# Usage: invoke.sh <path> [--modes fm1,fm5] [--max-severity high] [--format markdown|json]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMITIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ -f "${PRIMITIVE_ROOT}/shared/auditor.py" ]; then
  AUDITOR="${PRIMITIVE_ROOT}/shared/auditor.py"
else
  echo "ERROR: cannot locate auditor.py at ${PRIMITIVE_ROOT}/shared/" >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python3}"
exec "${PYTHON_BIN}" "${AUDITOR}" "$@"
