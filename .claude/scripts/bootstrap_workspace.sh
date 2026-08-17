#!/usr/bin/env bash
# Materialise the Lab 2 workspace architecture from a distribution bundle.
#
# The lab is a workspace root plus TWO INDEPENDENT OWNED REPOS (and a legacy edge that is not in
# the workspace at all). The distribution bundle carries all three parts in one download; this
# script turns that download into the real thing:
#
#   lab2-payer-auth/                  git repo — shared .claude/ config, guides
#     boost-authentication-service/   git repo — the producer  (own history, own HEAD)
#     boost-order-processing/         git repo — the consumer  (own history, own HEAD)
#
# Each owned repo gets its own committed baseline, which is what makes `git diff HEAD` meaningful
# per repo from a learner's first edit — the precondition for the PAN/secret gate to fire at all.
#
# Idempotent: safe to re-run, and a no-op on a workspace that is already in this shape.
# It never touches working-tree content, only git metadata.
#
# Usage:  .claude/scripts/bootstrap_workspace.sh

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

if [ ! -f ".claude/lab.json" ]; then
  echo "not a Lab 2 workspace root (no .claude/lab.json): $root" >&2
  exit 2
fi

repos=(boost-authentication-service boost-order-processing)
baseline_message="PGSE-88 starter: inherited first-pass draft of Retrieve Payer Authentication Results"

for repo in "${repos[@]}"; do
  if [ ! -d "$repo" ]; then
    echo "missing owned repo: $repo" >&2
    exit 2
  fi

  if [ -d "$repo/.git" ]; then
    echo "ok       $repo is already its own git repo ($(git -C "$repo" log --oneline -1 2>/dev/null || echo 'no commits yet'))"
  else
    git -C "$repo" init -q -b main
    git -C "$repo" add -A
    git -C "$repo" -c user.name="Lab Participant" -c user.email="participant@example.invalid" \
        commit -q -m "$baseline_message"
    echo "created  $repo is now its own git repo with a committed baseline"
  fi
done

# The workspace repo tracks the shared config and the guides — not the owned repos, which carry
# their own histories. Untrack them if the bundle had them checked in.
if [ -d ".git" ]; then
  changed=0
  for repo in "${repos[@]}"; do
    if git ls-files --error-unmatch "$repo" >/dev/null 2>&1; then
      git rm -r -q --cached "$repo"
      changed=1
      echo "untracked $repo from the workspace repo (it has its own history now)"
    fi
    if ! grep -qx "$repo/" .gitignore 2>/dev/null; then
      printf '%s/\n' "$repo" >> .gitignore
      changed=1
    fi
  done
  # Commit the untracking so the workspace root starts clean: a dirty root makes the plugin's
  # diff-based PAN/secret gate noisy for the whole session.
  if [ "$changed" = "1" ]; then
    git add -A .gitignore
    git -c user.name="Lab Participant" -c user.email="participant@example.invalid" \
        commit -q -m "Materialise the owned repos as independent git repositories"
  fi
fi

echo
echo "Workspace ready. Open Claude Code at: $root"
for repo in "${repos[@]}"; do
  printf '  %-32s %s\n' "$repo" "$(git -C "$repo" log --oneline -1)"
done
echo "  target-pass-proxy                (not in the workspace — compressed context only)"
