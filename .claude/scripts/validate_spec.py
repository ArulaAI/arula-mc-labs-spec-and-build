#!/usr/bin/env python3
"""
Run the Workbench plugin's own spec validator against a spec file.

Python port of validate_spec.sh — identical resolution order, no bash dependency, so it
also runs on native Windows (no Git Bash / WSL required).

This is a locator, not a reimplementation: the structural checks stay load-bearing in the
plugin's `validate_spec.py`, exactly as `spec-craft` runs them.

Resolution order:
  1. $CLAUDE_PLUGIN_ROOT        (set when the plugin runs the script)
  2. $WORKBENCH_HOME            (explicit override, e.g. a checkout of the plugin repo)
  3. the newest copy under the Claude Code plugin cache

Usage: python3 .claude/scripts/validate_spec.py <path/to/spec.md>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REL = Path("skills/spec-craft/scripts/validate_spec.py")


def main() -> int:
    if len(sys.argv) < 2:
        print(f"usage: {Path(sys.argv[0]).name} <path/to/spec.md>", file=sys.stderr)
        return 2
    spec = Path(sys.argv[1])
    if not spec.is_file():
        print(f"no such spec file: {spec}", file=sys.stderr)
        return 2

    for base in (os.environ.get("CLAUDE_PLUGIN_ROOT"), os.environ.get("WORKBENCH_HOME")):
        if base and (Path(base) / REL).is_file():
            os.execvp(sys.executable, [sys.executable, str(Path(base) / REL), str(spec)])

    plugin_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "plugins"
    candidates = sorted(plugin_dir.glob(f"**/{REL.as_posix()}")) if plugin_dir.is_dir() else []

    if not candidates:
        print(
            "Could not find the Workbench spec validator "
            "(skills/spec-craft/scripts/validate_spec.py).\n\n"
            "The `workbench` plugin does not appear to be installed for this user. Either "
            "install it, or point this script at a checkout:\n\n"
            "    WORKBENCH_HOME=/path/to/workbench python3 .claude/scripts/validate_spec.py <spec.md>",
            file=sys.stderr,
        )
        return 3

    os.execvp(sys.executable, [sys.executable, str(candidates[-1]), str(spec)])


if __name__ == "__main__":
    sys.exit(main())
