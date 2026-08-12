#!/usr/bin/env bash
# recorder.sh — shared journey-recorder script invoked by harness hook adapters.
#
# Usage:
#   recorder.sh --event-type <type> --run-id <id> \
#               [--lab-slug <slug>] [--harness <claude-code|copilot>] \
#               [--<field> <value> ...]
#
# Behavior:
#   - Generates event_id (UUID-based) if not supplied.
#   - Captures timestamp (UTC ISO-8601).
#   - For any --<field>_text argument, computes:
#       <field>_text_hash    = SHA-256 first 16 hex chars of raw value
#       <field>_text_preview = first 80 chars with secrets redacted (via redact.py)
#   - Appends a JSONL line to .forge/journey/<run-id>.jsonl inside LAB_ROOT.
#
# LAB_ROOT defaults to the git repo root (git rev-parse --show-toplevel) or CWD.
#
# Compatible with bash 3.2+ (macOS default).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Resolve LAB_ROOT: honour --lab-root if supplied, else git root or CWD.
# ---------------------------------------------------------------------------
LAB_ROOT=""
_REMAINING_ARGS=()
_i=0
_ARGS=("$@")
while [[ $_i -lt ${#_ARGS[@]} ]]; do
    if [[ "${_ARGS[$_i]}" == "--lab-root" ]]; then
        LAB_ROOT="${_ARGS[$((_i + 1))]}"
        _i=$((_i + 2))
    else
        _REMAINING_ARGS+=("${_ARGS[$_i]}")
        _i=$((_i + 1))
    fi
done

if [[ -z "$LAB_ROOT" ]]; then
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        LAB_ROOT="$(git rev-parse --show-toplevel)"
    else
        LAB_ROOT="$(pwd)"
    fi
fi

# ---------------------------------------------------------------------------
# Delegate ALL parsing + JSON construction + JSONL write to Python.
# Pass all CLI args verbatim; Python handles the --key value pairs.
# ---------------------------------------------------------------------------
python3 - "$LAB_ROOT" "${_REMAINING_ARGS[@]}" <<'PYEOF'
import sys
import json
import hashlib
import datetime
import pathlib
import re

# First positional arg is LAB_ROOT; rest are the original CLI args.
lab_root_str = sys.argv[1]
cli_args = sys.argv[2:]

# Try to import the installed redact helper; fall back to inline minimal version.
script_dir = pathlib.Path(__file__).resolve().parent if "__file__" in dir() else pathlib.Path(lab_root_str)
try:
    sys.path.insert(0, str(pathlib.Path(lab_root_str)))
    from primitives.journey_recorder.shared.redact import redact_preview  # type: ignore[import]
except ImportError:
    _SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS-KEY"),
        (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC-KEY"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GITHUB-PAT"),
        (re.compile(r'(?i)(password\s*[:=]\s*)(["\']?[a-zA-Z0-9!@#$%^&*()\-_+=]{4,}["\']?)'), "PASSWORD"),
        (re.compile(r'(?i)(api[_-]?key\s*[:=]\s*)(["\']?[a-zA-Z0-9\-_]{8,}["\']?)'), "API-KEY"),
    ]

    def redact_preview(text: str, max_chars: int = 80) -> str:  # type: ignore[misc]
        result = text
        for pattern, kind in _SECRET_PATTERNS:
            if pattern.groups:
                result = pattern.sub(lambda m, k=kind: m.group(1) + f"[REDACTED-{k}]", result)
            else:
                result = pattern.sub(f"[REDACTED-{kind}]", result)
        return result[:max_chars]

import uuid

# Parse --key value pairs from CLI args.
fields: dict[str, object] = {}
i = 0
while i < len(cli_args):
    arg = cli_args[i]
    if arg.startswith("--"):
        key = arg[2:].replace("-", "_")  # --event-type → event_type
        if i + 1 < len(cli_args):
            fields[key] = cli_args[i + 1]
            i += 2
        else:
            # Flag without value — treat as boolean true
            fields[key] = True
            i += 1
    else:
        i += 1

# Parse JSON-valued fields (e.g. token_usage).
for key in list(fields.keys()):
    if key == "token_usage" and isinstance(fields[key], str):
        try:
            fields[key] = json.loads(fields[key])
        except (json.JSONDecodeError, TypeError):
            pass  # leave as string if not valid JSON

# Validate required fields.
if "type" not in fields and "event_type" not in fields:
    print("recorder.sh: --event-type is required", file=sys.stderr)
    sys.exit(1)

if "run_id" not in fields:
    print("recorder.sh: --run-id is required", file=sys.stderr)
    sys.exit(1)

# Normalise event_type → type
if "event_type" in fields and "type" not in fields:
    fields["type"] = fields.pop("event_type")

# Build base event dict.
event: dict[str, object] = dict(fields)

# Ensure mandatory housekeeping fields.
if not event.get("event_id"):
    event["event_id"] = "evt_" + uuid.uuid4().hex[:20]
event.setdefault("timestamp", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

# Compute *_text_hash and *_text_preview for any _text field.
for key in list(event.keys()):
    if key.endswith("_text") and event[key]:
        raw = str(event[key])
        event[key + "_hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]
        event[key + "_preview"] = redact_preview(raw)

# Write JSONL.
lab_root = pathlib.Path(lab_root_str)
run_id = str(event.get("run_id", "run_unknown"))
journey_dir = lab_root / ".forge" / "journey"
journey_dir.mkdir(parents=True, exist_ok=True)
out_file = journey_dir / f"{run_id}.jsonl"
with open(out_file, "a") as f:
    f.write(json.dumps(event) + "\n")
PYEOF
