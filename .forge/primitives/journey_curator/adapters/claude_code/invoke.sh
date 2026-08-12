#!/usr/bin/env bash
# U4 /journey-curator — Claude Code adapter invoke script.
# Usage: invoke.sh --run-id <run-id> [--lab-root <path>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIMITIVE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ -f "${PRIMITIVE_ROOT}/shared/curator.py" ]; then
  CURATOR="${PRIMITIVE_ROOT}/shared/curator.py"
else
  echo "ERROR: cannot locate curator.py at ${PRIMITIVE_ROOT}/shared/" >&2
  exit 2
fi

PYTHON_BIN="${PYTHON:-python3}"
exec "${PYTHON_BIN}" -m primitives.journey_curator.shared.curator "$@"
