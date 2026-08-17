#!/usr/bin/env python3
"""
Lab 2 — Layer B grader: repo state and behaviour.

Layer A (`/grade`, the plugin `lab-grader`) scores the journey: it proves the learner moved
through the stages and leaked nothing. It cannot prove the work is correct. This script does the
behaviour half — content and state, never mere existence — and is deterministic: two runs on an
unchanged workspace produce identical output.

Usage:
    python3 .claude/scripts/grade_repo.py            # from the workspace root
    python3 .claude/scripts/grade_repo.py --json     # machine-readable

Requires: JDK 17+, Maven, Python 3.11+.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

AUTH = "boost-authentication-service"
ORDERS = "boost-order-processing"

CONTEXT_ARTIFACT = ".claude/context/target-pass-proxy.context.md"
CONTEXT_SECTIONS = [
    "Identity & purpose",
    "Endpoints / interfaces",
    "Request/response contracts",
    "Field mappings",
    "Domain behavior",
    "DOES / DOES NOT",
    "Allowed / forbidden changes",
    "Source paths",
    "Freshness / version metadata",
]
CONTEXT_REQUIRED_FACT = re.compile(
    r"DOES NOT call\s+`?authenticatePayer`?", re.IGNORECASE)

SPEC = f"{AUTH}/specs/retrieve-payer-auth.spec.md"
SPEC_STATUS = f"{AUTH}/specs/retrieve-payer-auth.spec.status.json"
ISSUES = f"{AUTH}/issues.json"
TDD_LOG = f"{AUTH}/docs/tdd-log.md"
PR_ARTIFACT = f"{AUTH}/docs/PR_DESCRIPTION.md"
AUTH_LOG_SINK = f"{AUTH}/logs/auth-service.log"

PAN = re.compile(
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}"
    r"|6(?:011|5[0-9]{2})[0-9]{12})\b")
SENSITIVE_LITERALS = ("AAABBJg0VhI0VniQEjRWAAAAAAA=", "CUST-77301")

# The canonical name for the test that encodes AC-INCOMPLETE. It is a convention, not a
# requirement: the check below finds the test by what it asserts, so a learner who names it
# something else is graded on behaviour, not on a filename.
BILLABLE_TEST = "NoSecondAuthenticatePayerCallTest"
# Matches the Mockito and BDDMockito spellings of "authenticatePayer was never invoked",
# whitespace-normalised: verify(x, never()).authenticatePayer(...) /
# then(x).should(never()).authenticatePayer(...)
NEVER_ASSERTION = re.compile(r"never\s*\(\s*\)[^;]{0,80}?authenticatePayer")


# --------------------------------------------------------------------------- helpers

class Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, check: str, passed: bool, evidence: str) -> None:
        self.checks.append({"check": check, "passed": bool(passed), "evidence": evidence})

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)


def read(root: Path, rel: str) -> str | None:
    path = root / rel
    return path.read_text(errors="replace") if path.exists() else None


def run_maven(repo: Path, *goals: str, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = ["mvn", "-B", "-q", *goals]
    if extra:
        cmd.extend(extra)
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True)


def surefire_results(repo: Path) -> dict[str, dict]:
    """Return {test-class-simple-name: {tests, failures, errors}} from surefire reports."""
    results: dict[str, dict] = {}
    for report in sorted(glob.glob(str(repo / "target" / "surefire-reports" / "TEST-*.xml"))):
        try:
            root = ET.parse(report).getroot()
        except ET.ParseError:
            continue
        name = (root.get("name") or "").split(".")[-1]
        results[name] = {
            "tests": int(root.get("tests") or 0),
            "failures": int(root.get("failures") or 0),
            "errors": int(root.get("errors") or 0),
        }
    return results


def green(results: dict[str, dict], test_class: str) -> bool:
    result = results.get(test_class)
    return bool(result) and result["failures"] == 0 and result["errors"] == 0


def java_sources(repo: Path, *relative: str) -> list[Path]:
    base = repo.joinpath(*relative)
    return sorted(base.rglob("*.java")) if base.exists() else []


# --------------------------------------------------------------------------- checks

def check_compressed_context(root: Path, report: Report) -> None:
    text = read(root, CONTEXT_ARTIFACT)
    if text is None:
        report.add("compressed-context-complete", False, f"{CONTEXT_ARTIFACT} is absent")
        return
    missing = [s for s in CONTEXT_SECTIONS if s.lower() not in text.lower()]
    has_fact = bool(CONTEXT_REQUIRED_FACT.search(text))
    passed = not missing and has_fact
    evidence = "all required sections present; DOES-NOT-call-authenticatePayer fact present"
    if missing:
        evidence = f"missing sections: {', '.join(missing)}"
    elif not has_fact:
        evidence = "no explicit 'DOES NOT call authenticatePayer' statement"
    report.add("compressed-context-complete", passed, evidence)


def check_spec(root: Path, report: Report) -> None:
    text = read(root, SPEC)
    if text is None:
        report.add("spec-ready", False, f"{SPEC} is absent")
        report.add("spec-gaps-closed", False, f"{SPEC} is absent")
        return

    status_text = read(root, SPEC_STATUS)
    status = json.loads(status_text) if status_text else {}
    structurally_valid = bool(status.get("valid"))
    report.add(
        "spec-ready",
        structurally_valid,
        f"spec.status.json valid={status.get('valid')}, "
        f"missing_sections={status.get('missing_sections')}, "
        f"non_testable_acs={status.get('non_testable_acs')}",
    )

    lowered = text.lower()
    ac_incomplete = bool(
        re.search(r"authenticate payer", lowered)
        and re.search(r"never (invoked|called)", lowered))
    out_of_scope = "externally authenticated" in lowered and "out of scope" in lowered
    error_semantics = all(code in text for code in ("404", "403", "400"))
    non_negotiables = "## Non-Negotiables" in text
    gaps = {
        "G1 ## Non-Negotiables section": non_negotiables,
        "G2 AC-INCOMPLETE (billable call never invoked)": ac_incomplete,
        "G3 externally authenticated out of scope": out_of_scope,
        "G4 404/403/400 distinguished": error_semantics,
    }
    unclosed = [name for name, ok in gaps.items() if not ok]
    report.add(
        "spec-gaps-closed",
        not unclosed,
        "G1-G4 closed" if not unclosed else f"still open: {'; '.join(unclosed)}",
    )


def check_issues(root: Path, report: Report) -> None:
    text = read(root, ISSUES) or read(root, "issues.json")
    if text is None:
        report.add("issues-name-repo-boundaries", False,
                   f"{ISSUES} is absent (also checked ./issues.json)")
        return
    try:
        issues = json.loads(text)
    except json.JSONDecodeError as exc:
        report.add("issues-name-repo-boundaries", False, f"{ISSUES} is not valid JSON: {exc}")
        return
    owned = {AUTH, ORDERS}
    untagged = [
        issue.get("number", "?")
        for issue in issues
        if not (str(issue.get("repo", "")) in owned
                or any(name in json.dumps(issue) for name in owned))
    ]
    report.add(
        "issues-name-repo-boundaries",
        bool(issues) and not untagged,
        f"{len(issues)} issues; untagged: {untagged}" if untagged
        else f"{len(issues)} issues, each naming an owned repo",
    )


def check_tdd_log(root: Path, report: Report) -> None:
    text = read(root, TDD_LOG)
    if text is None:
        report.add("tdd-before-implementation", False, f"{TDD_LOG} is absent")
        return
    test_names = {p.stem for p in java_sources(root / AUTH, "src", "test")}
    named = sorted(name for name in test_names if name in text)
    shows_red = bool(re.search(r"\bred\b|failing test|fails? first", text, re.IGNORECASE))
    passed = len(named) >= 3 and shows_red
    report.add(
        "tdd-before-implementation",
        passed,
        f"log names {len(named)} of the repo's test classes ({', '.join(named[:5])}); "
        f"records a failing-first observation: {shows_red}",
    )


def check_billable_test_present(root: Path, report: Report) -> tuple[bool, Path | None]:
    """Find the test that asserts the billable operation is never invoked, whatever it is called."""
    asserting = [
        path for path in java_sources(root / AUTH, "src", "test")
        if NEVER_ASSERTION.search(re.sub(r"\s+", " ", path.read_text(errors="replace")))
    ]
    if not asserting:
        named = [p for p in java_sources(root / AUTH, "src", "test") if p.stem == BILLABLE_TEST]
        report.add(
            "billable-call-constraint-testable", False,
            f"no test asserts never().authenticatePayer "
            f"({BILLABLE_TEST} present but not asserting it)" if named
            else "no test asserts that authenticatePayer is never invoked "
                 f"(convention: {BILLABLE_TEST})",
        )
        return False, None

    # Prefer the canonical name when several tests assert it, so the probe is stable.
    chosen = next((p for p in asserting if p.stem == BILLABLE_TEST), asserting[0])
    note = "" if chosen.stem == BILLABLE_TEST else f" (convention name is {BILLABLE_TEST})"
    report.add(
        "billable-call-constraint-testable", True,
        f"{chosen.stem} asserts never().authenticatePayer{note}; "
        f"{len(asserting)} test class(es) assert it",
    )
    return True, chosen


def check_static_no_reauthentication(root: Path, report: Report) -> None:
    offenders = []
    for path in java_sources(root / AUTH, "src", "main"):
        if "/client/" in path.as_posix():
            continue  # the legacy client contract and its stand-in declare the operation
        if "authenticatePayer" in path.read_text(errors="replace"):
            offenders.append(path.relative_to(root).as_posix())
    report.add(
        "no-reauthentication-reachable",
        not offenders,
        "no non-client source references authenticatePayer" if not offenders
        else f"authenticatePayer referenced in: {', '.join(offenders)}",
    )

    proxies = [p for p in java_sources(root / AUTH, "src", "main")
               if "retrieveAuthenticationResult" in p.read_text(errors="replace")
               and "/client/" not in p.as_posix()]
    report.add(
        "proxies-not-reimplements",
        bool(proxies),
        f"retrieval delegates to LegacyPassClient.retrieveAuthenticationResult in "
        f"{', '.join(p.stem for p in proxies)}" if proxies
        else "no source calls LegacyPassClient.retrieveAuthenticationResult",
    )


def check_no_scope_expansion(root: Path, report: Report) -> None:
    banned = re.compile(r"externalAuth|ExternalAuthentication|externallyAuthenticatedService"
                        r"|authenticateExternally", re.IGNORECASE)
    offenders = [p.relative_to(root).as_posix()
                 for p in java_sources(root / AUTH, "src", "main")
                 if banned.search(p.read_text(errors="replace"))]
    report.add(
        "no-prohibited-scope-expansion",
        not offenders,
        "no externally-authenticated handling added" if not offenders
        else f"external-authentication handling found in: {', '.join(offenders)}",
    )


def check_log_sink(root: Path, report: Report) -> None:
    text = read(root, AUTH_LOG_SINK)
    if text is None:
        report.add("no-sensitive-data-in-logs", False,
                   f"{AUTH_LOG_SINK} is absent — run the test suite so there is evidence to scan")
        return
    findings = []
    if PAN.search(text):
        findings.append("PAN")
    for literal in SENSITIVE_LITERALS:
        if literal in text:
            findings.append("CAVV" if literal.startswith("AAAB") else "customer PII")
    report.add(
        "no-sensitive-data-in-logs",
        not findings,
        f"{AUTH_LOG_SINK} clean" if not findings
        else f"{AUTH_LOG_SINK} contains: {', '.join(sorted(set(findings)))}",
    )


def check_pr_artifact(root: Path, report: Report) -> None:
    settings = read(root, ".claude/settings.json") or ""
    wired = "pr_gate_guard.py" in settings
    guard = root / ".claude/hooks/pr_gate_guard.py"

    denied = False
    detail = "guard not wired in .claude/settings.json"
    if wired and guard.exists():
        with tempfile.TemporaryDirectory() as empty:
            event = json.dumps({
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": f"{empty}/{PR_ARTIFACT}"},
            })
            probe = subprocess.run(
                [sys.executable, str(guard)],
                input=event, capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": empty},
            )
            denied = '"permissionDecision": "deny"' in probe.stdout
            detail = ("guard denies the PR write while gates are red"
                      if denied else f"guard did not deny: {probe.stdout.strip()[:200]}")
    report.add("pr-gate-guard-blocks-on-red", wired and denied, detail)

    exists = (root / PR_ARTIFACT).exists()
    report.add("pr-artifact-written", exists,
               f"{PR_ARTIFACT} present" if exists else f"{PR_ARTIFACT} not written")


def journey_files(root: Path) -> list[Path]:
    """Every journey file in the workspace.

    The plugin's journey hook writes `journey/` relative to the process working directory, so a
    session that ran commands inside an owned repo leaves events in `<repo>/journey/` as well as
    the workspace-root `journey/`. Grading reads all of them (Workbench_Issues_To_Address.md
    item 1 / L2-9).
    """
    found = set(glob.glob(str(root / "journey" / "*.jsonl")))
    found.update(glob.glob(str(root / "*" / "journey" / "*.jsonl")))
    return [Path(p) for p in sorted(found)]


def check_no_gh(root: Path, report: Report) -> None:
    haystack = ""
    for path in journey_files(root):
        haystack += path.read_text(errors="replace")
    for rel in (f"{AUTH}/docs/workflow-tracker.md", PR_ARTIFACT):
        haystack += read(root, rel) or ""
    calls = re.findall(r"gh (?:issue|pr) create", haystack)
    report.add("no-github-artifacts-created", not calls,
               "no `gh issue create` / `gh pr create` in the trail" if not calls
               else f"found {len(calls)} gh invocation(s)")


def check_journey(root: Path, report: Report) -> None:
    events = []
    files = journey_files(root)
    for path in files:
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    hand_offs = [e for e in events if e.get("event") == "hand-off"]
    stages = {e.get("stage") for e in hand_offs if e.get("stage") is not None}
    enough = len(hand_offs) >= 7 or len(stages) >= 7
    report.add(
        "seven-stage-boundaries-recorded",
        enough,
        f"{len(hand_offs)} hand-off events across {len(files)} journey file(s), "
        f"stages {sorted(s for s in stages if s is not None)}",
    )

    blob = json.dumps(events)
    validator_in_journey = "code-to-spec-validator" in blob
    validation_log = read(root, f"{AUTH}/docs/validation-log.md") or ""
    validator_logged = "validator" in validation_log.lower()
    report.add(
        "fresh-context-validator-ran",
        validator_in_journey or validator_logged,
        f"journey mentions code-to-spec-validator: {validator_in_journey}; "
        f"validation-log.md records a validator verdict: {validator_logged}",
    )


def check_builds_and_behaviour(root: Path, report: Report, billable_test: Path | None) -> None:
    auth_repo = root / AUTH
    orders_repo = root / ORDERS

    auth_build = run_maven(auth_repo, "verify")
    report.add("auth-service-mvn-verify-green", auth_build.returncode == 0,
               "mvn verify GREEN" if auth_build.returncode == 0
               else f"mvn verify RED: {auth_build.stdout.strip()[-400:]}")

    orders_build = run_maven(orders_repo, "verify")
    report.add("order-processing-mvn-verify-green", orders_build.returncode == 0,
               "mvn verify GREEN" if orders_build.returncode == 0
               else f"mvn verify RED: {orders_build.stdout.strip()[-400:]}")

    auth_results = surefire_results(auth_repo)
    orders_results = surefire_results(orders_repo)

    test_name = billable_test.stem if billable_test else BILLABLE_TEST
    report.add(
        "billable-call-test-green",
        billable_test is not None and green(auth_results, test_name),
        f"{test_name}: {auth_results.get(test_name, 'not run')}",
    )
    report.add(
        "consumer-contract-holds",
        green(orders_results, "ContractConsumerTest"),
        f"ContractConsumerTest: {orders_results.get('ContractConsumerTest', 'not run')}",
    )


def check_anti_gaming(root: Path, report: Report, billable_test: Path | None) -> None:
    """Apply the wrong implementation to a temp copy; the learner's test must FAIL on it."""
    if billable_test is None:
        report.add("anti-gaming-probe", False,
                   "no test asserts the billable call is never invoked — nothing to probe")
        return
    test_name = billable_test.stem

    reference = root / ".claude/reference"
    patch = reference / "trap-wrong-impl.patch"
    solution = reference / "stage6-solution" / AUTH
    if not patch.exists() or not solution.exists():
        report.add("anti-gaming-probe", False, "reference probe material is missing")
        return

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / AUTH
        shutil.copytree(root / AUTH, work,
                        ignore=shutil.ignore_patterns("target", "logs", ".git"))
        for source in solution.rglob("*.java"):
            destination = work / source.relative_to(solution)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        applied = subprocess.run(
            ["patch", "-p1", "-s", "-i", str(patch)],
            cwd=work, capture_output=True, text=True)
        if applied.returncode != 0:
            report.add("anti-gaming-probe", False,
                       f"could not apply trap-wrong-impl.patch: {applied.stderr.strip()[:200]}")
            return

        probe = run_maven(work, "test", extra=[f"-Dtest={test_name}", "-DfailIfNoTests=false"])
        failed_as_expected = probe.returncode != 0
        report.add(
            "anti-gaming-probe",
            failed_as_expected,
            f"{test_name} fails against the re-introduced billable call — the test bites"
            if failed_as_expected
            else f"{test_name} PASSED against a known-wrong implementation: it does not "
                 f"detect the second billable call",
        )


# --------------------------------------------------------------------------- main

def grade(root: Path) -> Report:
    report = Report()
    check_compressed_context(root, report)
    check_spec(root, report)
    check_issues(root, report)
    check_tdd_log(root, report)
    _, billable_test = check_billable_test_present(root, report)
    check_static_no_reauthentication(root, report)
    check_no_scope_expansion(root, report)
    check_builds_and_behaviour(root, report, billable_test)
    check_log_sink(root, report)
    check_pr_artifact(root, report)
    check_no_gh(root, report)
    check_journey(root, report)
    check_anti_gaming(root, report, billable_test)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 2 Layer B grader (repo state + behaviour)")
    parser.add_argument("--root", default=".", help="workspace root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / AUTH).exists() or not (root / ORDERS).exists():
        print(f"error: {root} does not look like the Lab 2 workspace "
              f"(expected {AUTH}/ and {ORDERS}/)", file=sys.stderr)
        sys.exit(2)

    report = grade(root)
    passed = sum(1 for c in report.checks if c["passed"])
    result = {
        "lab": 2,
        "layer": "B (repo state and behaviour)",
        "checks_passed": passed,
        "checks_total": len(report.checks),
        "passed": report.passed,
        "checks": report.checks,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Lab 2 — Layer B: repo state and behaviour\n")
        for check in report.checks:
            print(f"  [{'PASS' if check['passed'] else 'FAIL'}] {check['check']}")
            print(f"         {check['evidence']}")
        print(f"\n  {passed}/{len(report.checks)} checks passed — "
              f"{'PASS' if report.passed else 'FAIL'}")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
