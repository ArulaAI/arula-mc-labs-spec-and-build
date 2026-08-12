"""
redact.py — preview redaction helper for journey_recorder.

Strips secrets from text previews before writing to JSONL.
Matches the FM5 secret patterns from failure_mode_rules.yaml.
"""

from __future__ import annotations

import re
from collections.abc import Callable

# (pattern, kind-label) pairs — mirrors FM5 rules in failure_mode_rules.yaml
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # AWS Access Key ID
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS-KEY"),
    # Anthropic API key (format: sk-ant-<type>-<random>, may contain hyphens)
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC-KEY"),
    # GitHub Personal Access Token
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GITHUB-PAT"),
    # password=<value> or password: <value> (quoted or bare)
    (
        re.compile(r'(?i)(password\s*[:=]\s*)(["\']?[a-zA-Z0-9!@#$%^&*()\-_+=]{4,}["\']?)'),
        "PASSWORD",
    ),
    # api_key=<value> or api-key=<value>
    (
        re.compile(r'(?i)(api[_-]?key\s*[:=]\s*)(["\']?[a-zA-Z0-9\-_]{8,}["\']?)'),
        "API-KEY",
    ),
]


def _make_replacer(kind: str) -> Callable[[re.Match[str]], str]:
    """Return a replacement function that keeps group(1) and redacts the value."""

    def _replace(m: re.Match[str]) -> str:
        return m.group(1) + f"[REDACTED-{kind}]"

    return _replace


def redact_preview(text: str, max_chars: int = 80) -> str:
    """Return text with secrets replaced by [REDACTED-<kind>], truncated to max_chars.

    Each matched secret is replaced inline so the caller never sees raw credential
    values in the preview field written to JSONL.
    """
    result = text
    for pattern, kind in _PATTERNS:
        # For patterns with capture groups (password=, api_key=), keep the key
        # prefix and replace only the value portion.
        if pattern.groups:
            result = pattern.sub(_make_replacer(kind), result)
        else:
            result = pattern.sub(f"[REDACTED-{kind}]", result)
    return result[:max_chars]
