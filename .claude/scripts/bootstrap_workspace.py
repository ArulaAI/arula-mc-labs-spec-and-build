#!/usr/bin/env python3
"""
Materialise the Lab 2 workspace architecture from a distribution bundle.

Python port of bootstrap_workspace.sh — identical behaviour, no bash dependency, so it
also runs on native Windows (no Git Bash / WSL required).

Usage: python3 .claude/scripts/bootstrap_workspace.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOS = ("boost-authentication-service", "boost-order-processing")
BASELINE_MESSAGE = "PGSE-88 starter: inherited first-pass draft of Retrieve Payer Authentication Results"


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def last_commit(repo: Path) -> str:
    result = git("log", "--oneline", "-1", cwd=repo)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "no commits yet"


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    if not (root / ".claude" / "lab.json").exists():
        print(f"not a Lab 2 workspace root (no .claude/lab.json): {root}", file=sys.stderr)
        return 2

    for repo in REPOS:
        repo_path = root / repo
        if not repo_path.is_dir():
            print(f"missing owned repo: {repo}", file=sys.stderr)
            return 2

        if (repo_path / ".git").is_dir():
            print(f"ok       {repo} is already its own git repo ({last_commit(repo_path)})")
        else:
            git("init", "-q", "-b", "main", cwd=repo_path)
            git("add", "-A", cwd=repo_path)
            subprocess.run(
                ["git", "-c", "user.name=Lab Participant", "-c", "user.email=participant@example.invalid",
                 "commit", "-q", "-m", BASELINE_MESSAGE],
                cwd=repo_path, capture_output=True, text=True,
            )
            print(f"created  {repo} is now its own git repo with a committed baseline")

    if (root / ".git").is_dir():
        changed = False
        gitignore = root / ".gitignore"
        ignored_lines = gitignore.read_text().splitlines() if gitignore.exists() else []

        for repo in REPOS:
            tracked = git("ls-files", "--error-unmatch", repo, cwd=root)
            if tracked.returncode == 0:
                git("rm", "-r", "-q", "--cached", repo, cwd=root)
                changed = True
                print(f"untracked {repo} from the workspace repo (it has its own history now)")
            if f"{repo}/" not in ignored_lines:
                with gitignore.open("a") as f:
                    f.write(f"{repo}/\n")
                ignored_lines.append(f"{repo}/")
                changed = True

        if changed:
            git("add", "-A", ".gitignore", cwd=root)
            subprocess.run(
                ["git", "-c", "user.name=Lab Participant", "-c", "user.email=participant@example.invalid",
                 "commit", "-q", "-m", "Materialise the owned repos as independent git repositories"],
                cwd=root, capture_output=True, text=True,
            )

    print()
    print(f"Workspace ready. Open Claude Code at: {root}")
    for repo in REPOS:
        print(f"  {repo:<32} {last_commit(root / repo)}")
    print("  target-pass-proxy                (not in the workspace — compressed context only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
