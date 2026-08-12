#!/usr/bin/env python3
"""quality_gates.py — secret/cardholder-data scan + unknown-dependency check.

Bound to the Maven `verify` phase (see pom.xml, exec-maven-plugin). Deterministic, no model
calls — this is the "python load-bearing" gate layer the workbench build instructions call for
alongside the JaCoCo coverage-threshold check and the Checkstyle lint check, which are wired as
native Maven plugins instead of duplicated here.

Exits 0 with no output on a clean run. Exits 1 and prints every violation (file:line, reason) on
a dirty run, which fails `mvn verify` and stops the pipeline.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIRS = [REPO_ROOT / "src" / "main", REPO_ROOT / "src" / "test"]
SCANNED_SUFFIXES = {".java", ".yml", ".yaml", ".properties"}

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "Anthropic API key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub personal access token"),
    (
        re.compile(r'(?i)password\s*[:=]\s*["\']?[a-zA-Z0-9!@#$%^&*()\-_+=]{4,}["\']?'),
        "hardcoded password",
    ),
    (
        re.compile(r'(?i)api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9\-_]{8,}["\']?'),
        "hardcoded API key",
    ),
]

# Candidate PAN sequences: 13-19 digits, optionally grouped with spaces or dashes.
PAN_CANDIDATE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def scan_secrets_and_pan() -> list[str]:
    violations: list[str] = []
    for src_dir in SRC_DIRS:
        if not src_dir.exists():
            continue
        for path in src_dir.rglob("*"):
            if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
                continue
            rel = path.relative_to(REPO_ROOT)
            for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
                for pattern, label in SECRET_PATTERNS:
                    if pattern.search(line):
                        violations.append(f"{rel}:{lineno}: possible {label}")
                for match in PAN_CANDIDATE.finditer(line):
                    digits = re.sub(r"[ -]", "", match.group())
                    if len(digits) >= 13 and luhn_valid(digits):
                        violations.append(f"{rel}:{lineno}: possible cardholder PAN (Luhn-valid digit sequence)")
    return violations


def load_allowlist() -> set[str]:
    allowlist_path = REPO_ROOT / "scripts" / "approved-dependencies.txt"
    entries: set[str] = set()
    for line in allowlist_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def scan_dependencies() -> list[str]:
    pom_path = REPO_ROOT / "pom.xml"
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    tree = ET.parse(pom_path)
    root = tree.getroot()

    allowlist = load_allowlist()
    violations: list[str] = []

    deps_parent = root.find("m:dependencies", ns)
    if deps_parent is None:
        return violations

    for dep in deps_parent.findall("m:dependency", ns):
        group = dep.findtext("m:groupId", default="", namespaces=ns)
        artifact = dep.findtext("m:artifactId", default="", namespaces=ns)
        key = f"{group}:{artifact}"
        if key not in allowlist:
            violations.append(f"pom.xml: unknown dependency {key!r} — not in scripts/approved-dependencies.txt")
    return violations


def main() -> int:
    violations = scan_secrets_and_pan() + scan_dependencies()
    if violations:
        print("quality_gates: FAIL —", len(violations), "violation(s):")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("quality_gates: OK — no secrets, no cardholder-data patterns, no unknown dependencies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
