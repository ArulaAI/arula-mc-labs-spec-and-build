"""U1 /failure-mode-audit — static detector engine.

LLM-judged modes (FM3 nuanced + FM4) defer their full path to Plan 2;
this Plan 1 milestone implements regex-based detectors only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

Severity = Literal["low", "medium", "high", "critical"]
SEVERITY_ORDER: dict[Severity, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class Finding:
    """A single failure mode finding."""

    mode: str
    severity: Severity
    file: str
    line: int
    message: str
    snippet: str


_RULES_PATH = Path(__file__).parent / "failure_mode_rules.yaml"

# Project-internal package roots that are always OK as imports.
_RELATIVE_OK_TOPLEVELS: frozenset[str] = frozenset(
    ["forge_validate", "primitives", "tests", "_pytest", "pytest"]
)


def _load_rules() -> dict[str, Any]:
    result: dict[str, Any] = yaml.safe_load(_RULES_PATH.read_text())
    return result


def _files_under(path: Path, glob_patterns: list[str]) -> list[Path]:
    if path.is_file():
        return [path] if any(path.match(g) for g in glob_patterns) else []
    return [p for g in glob_patterns for p in path.rglob(g) if p.is_file()]


def _python_imports(content_line: str) -> set[str]:
    """Extract top-level package names from a single Python import line."""
    packages: set[str] = set()
    # Strip inline comments (e.g. `# noqa: F401`) before parsing
    line = content_line.split("#", 1)[0].strip()
    if line.startswith("import "):
        mod = line.removeprefix("import ").split(" as ")[0].strip().split(",")[0].strip()
        packages.add(mod.split(".")[0])
    elif line.startswith("from ") and " import " in line:
        mod = line.split()[1]
        packages.add(mod.split(".")[0])
    return packages


def _python_declared_deps(project_root: Path) -> set[str]:
    """Read declared deps from pyproject.toml + requirements.txt + stdlib."""
    deps: set[str] = set(sys.stdlib_module_names)
    deps.update(_RELATIVE_OK_TOPLEVELS)

    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        content = pyproject.read_text()
        match = re.search(r"dependencies\s*=\s*\[([^\]]*)\]", content, re.S)
        if match:
            for raw in re.findall(r'"([^"]+)"', match.group(1)):
                name = re.split(r"[<>=!~ ]", raw)[0].lower().replace("-", "_")
                deps.add(name)

    reqs = project_root / "requirements.txt"
    if reqs.is_file():
        for raw in reqs.read_text().splitlines():
            stripped = raw.strip()
            if stripped and not stripped.startswith("#"):
                name = re.split(r"[<>=!~ ]", stripped)[0].lower().replace("-", "_")
                deps.add(name)

    return deps


def _audit_fm1(path: Path, project_root: Path) -> list[Finding]:
    """FM1: imports not in any declared manifest."""
    findings: list[Finding] = []
    declared = _python_declared_deps(project_root)
    for py_file in _files_under(path, ["*.py"]):
        try:
            content = py_file.read_text()
        except (UnicodeDecodeError, PermissionError):
            continue
        for line_num, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for pkg in _python_imports(stripped):
                pkg_normalized = pkg.lower()
                if pkg_normalized not in declared and pkg_normalized not in _RELATIVE_OK_TOPLEVELS:
                    findings.append(
                        Finding(
                            mode="fm1",
                            severity="medium",
                            file=str(py_file),
                            line=line_num,
                            message=(
                                f"Import `{pkg}` not in any declared manifest "
                                "(possible hallucinated dependency)"
                            ),
                            snippet=stripped,
                        )
                    )
    return findings


def _audit_regex_rules(path: Path, mode: str, mode_rules: dict[str, Any]) -> list[Finding]:
    """Apply regex-pattern detectors for a mode."""
    findings: list[Finding] = []
    for detector in mode_rules.get("detectors", []):
        patterns = detector.get("patterns", [])
        if not patterns:
            continue
        file_patterns = detector.get("file_patterns", ["*"])
        for file in _files_under(path, file_patterns):
            try:
                content = file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            for pat in patterns:
                regex = re.compile(pat["regex"])
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        findings.append(
                            Finding(
                                mode=mode,
                                severity=pat["severity"],
                                file=str(file),
                                line=line_num,
                                message=pat["msg"],
                                snippet=line.strip(),
                            )
                        )
    return findings


def audit_path(
    path: Path,
    *,
    modes: list[str] | None = None,
    max_severity: Severity | None = None,
    project_root: Path | None = None,
) -> list[Finding]:
    """Audit `path` for selected failure modes; return findings list."""
    if modes is None:
        modes = ["fm1", "fm2", "fm3", "fm4", "fm5"]
    if project_root is None:
        project_root = path if path.is_dir() else path.parent

    rules = _load_rules()
    findings: list[Finding] = []

    if "fm1" in modes:
        findings.extend(_audit_fm1(path, project_root))
    if "fm5" in modes:
        findings.extend(_audit_regex_rules(path, "fm5", rules["fm5_security_propagation"]))
    if "fm3" in modes:
        findings.extend(_audit_regex_rules(path, "fm3", rules["fm3_training_bias"]))
    if "fm4" in modes:
        findings.extend(_audit_regex_rules(path, "fm4", rules["fm4_overconfident"]))

    if max_severity is not None:
        threshold = SEVERITY_ORDER[max_severity]
        findings = [f for f in findings if SEVERITY_ORDER[f.severity] >= threshold]

    return findings


def main() -> None:
    """Direct CLI: `python -m primitives.failure_mode_audit.shared.auditor PATH`."""
    parser = argparse.ArgumentParser(description="U1 /failure-mode-audit primitive")
    parser.add_argument("path", type=Path)
    parser.add_argument("--modes", default="fm1,fm3,fm4,fm5")
    parser.add_argument(
        "--max-severity", default=None, choices=["low", "medium", "high", "critical"]
    )
    parser.add_argument("--format", default="markdown", choices=["json", "markdown"])
    args = parser.parse_args()

    findings = audit_path(
        args.path,
        modes=args.modes.split(","),
        max_severity=args.max_severity,
    )

    if args.format == "json":
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    elif not findings:
        print("\u2713 No findings.")
    else:
        print(f"# Failure-mode audit: {args.path}\n")
        by_mode: dict[str, list[Finding]] = {}
        for f in findings:
            by_mode.setdefault(f.mode, []).append(f)
        for mode, mode_findings in sorted(by_mode.items()):
            print(f"## {mode.upper()} ({len(mode_findings)} findings)\n")
            for f in mode_findings:
                print(f"- **{f.severity}** `{f.file}:{f.line}` \u2014 {f.message}")
                print(f"  ```\n  {f.snippet}\n  ```")

    if args.max_severity and findings:
        sys.exit(1)


if __name__ == "__main__":
    main()
