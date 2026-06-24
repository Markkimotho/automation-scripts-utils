#!/usr/bin/env bash
# git-safe-checkout.sh — switch branches without silently losing uncommitted work.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-safe-checkout.sh — checkout a branch after handling uncommitted work.

Usage:
  git-safe-checkout.sh <branch> [options]

Options:
  -b, --create     Create the branch (git checkout -b)
  --check          Report dirty state only. Exit 0 = clean, 2 = dirty.
  -y, --yes        Assume "stash" for the dirty prompt (non-interactive)
  -h, --help

Why:
  The #1 cause of confusing conflicts is switching branches with uncommitted
  changes. This refuses to do that blindly: it shows what's dirty and asks you
  to commit, stash, discard, or abort first.
EOF
}

branch="" create=0 check=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--create) create=1; shift;;
    --check) check=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) branch="$1"; shift;;
  esac
done

is_git_repo || die "Not inside a git repository."
[[ "$check" == "1" || -n "$branch" ]] || { usage; die "Branch name required."; }

dirty=0
if has_uncommitted || has_untracked; then dirty=1; fi

if [[ "$check" == "1" ]]; then
  if [[ "$dirty" == "1" ]]; then
    warn "Working tree is dirty:"; git status --short
    exit 2
  fi
  ok "Working tree is clean."
  exit 0
fi

if [[ "$dirty" == "1" ]]; then
  warn "You have uncommitted changes:"
  git status --short
  say ""
  if [[ "${ASSUME_YES:-0}" == "1" ]]; then
    action="s"
  else
    read -r -p "Handle them: [c]ommit / [s]tash / [d]iscard / [a]bort: " action
  fi
  case "$action" in
    c) read -r -p "Commit message: " msg; git add -A; git commit -m "${msg:-WIP}";;
    s) git stash push -u -m "git-safe-checkout before $branch"; ok "Stashed. Restore later with: git stash pop";;
    d) confirm "Discard ALL uncommitted changes? This cannot be undone." || die "Aborted."
       git reset --hard && git clean -fd;;
    *) die "Aborted — nothing changed.";;
  esac
fi

if [[ "$create" == "1" ]]; then
  git checkout -b "$branch"
else
  git checkout "$branch"
fi
ok "On branch: $(current_branch)"
