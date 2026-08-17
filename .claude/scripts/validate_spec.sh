#!/usr/bin/env bash
# Run the Workbench plugin's own spec validator against a spec file.
#
# This is a locator, not a reimplementation: the structural checks stay load-bearing in the
# plugin's `validate_spec.py`, exactly as `spec-craft` runs them. `$CLAUDE_PLUGIN_ROOT` is only
# set while the plugin itself is executing, so a learner running the check by hand needs the
# path resolved for them.
#
# Resolution order:
#   1. $CLAUDE_PLUGIN_ROOT        (set when the plugin runs the script)
#   2. $WORKBENCH_HOME            (explicit override, e.g. a checkout of the plugin repo)
#   3. the newest copy under the Claude Code plugin cache
#
# Usage: .claude/scripts/validate_spec.sh <path/to/spec.md>

set -euo pipefail

spec="${1:-}"
if [ -z "$spec" ]; then
  echo "usage: $(basename "$0") <path/to/spec.md>" >&2
  exit 2
fi
if [ ! -f "$spec" ]; then
  echo "no such spec file: $spec" >&2
  exit 2
fi

rel="skills/spec-craft/scripts/validate_spec.py"
for base in "${CLAUDE_PLUGIN_ROOT:-}" "${WORKBENCH_HOME:-}"; do
  if [ -n "$base" ] && [ -f "$base/$rel" ]; then
    exec python3 "$base/$rel" "$spec"
  fi
done

plugin_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins"
validator="$(find "$plugin_dir" -type f -path "*/$rel" 2>/dev/null | sort | tail -n 1)"

if [ -z "$validator" ]; then
  cat >&2 <<'MSG'
Could not find the Workbench spec validator (skills/spec-craft/scripts/validate_spec.py).

The `workbench` plugin does not appear to be installed for this user. Either install it, or
point this script at a checkout:

    WORKBENCH_HOME=/path/to/workbench .claude/scripts/validate_spec.sh <spec.md>
MSG
  exit 3
fi

exec python3 "$validator" "$spec"
