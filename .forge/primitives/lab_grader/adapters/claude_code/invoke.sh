#!/usr/bin/env bash
# U2 /lab-grader — Claude Code adapter invoke script.
# Usage: invoke.sh <lab_root> [--run-id <id>] [--format markdown|json]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMITIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ -f "${PRIMITIVE_ROOT}/shared/grader.py" ]; then
  GRADER="${PRIMITIVE_ROOT}/shared/grader.py"
else
  echo "ERROR: cannot locate grader.py at ${PRIMITIVE_ROOT}/shared/" >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python3}"
exec "${PYTHON_BIN}" -m primitives.lab_grader.shared.grader "$@"
