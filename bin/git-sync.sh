#!/usr/bin/env bash
# git-sync.sh — fetch, fast-forward the base, prune, and rebase the current branch onto it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-sync.sh — catch up with the remote: fetch, ff base, prune, rebase current branch.

Usage:
  git-sync.sh [options]

Options:
  -b, --base <branch>   Base branch (default: main, else master)
  --no-rebase           Don't rebase the current branch onto the base
  -y, --yes             Skip confirmation
  -h, --help

Refuses to run with a dirty working tree — commit or stash first
(see git-safe-checkout.sh).
EOF
}

base="" rebase=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--base) base="$2"; shift 2;;
    --no-rebase) rebase=0; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) usage; die "Unexpected argument: $1";;
  esac
done

is_git_repo || die "Not inside a git repository."
require_cmd git

if has_uncommitted || has_untracked; then
  warn "Working tree is dirty:"; git status --short
  die "Commit or stash first (git-safe-checkout.sh handles this)."
fi

if [[ -z "$base" ]]; then
  if git show-ref --verify --quiet refs/heads/main; then base="main"
  elif git show-ref --verify --quiet refs/heads/master; then base="master"
  else die "No main/master branch — pass --base."; fi
fi
cur="$(current_branch)"

info "Sync: fetch origin, ff '$base', prune${rebase:+, rebase '$cur' onto '$base'}."
confirm "Proceed?" || die "Aborted."

git fetch --prune origin

if [[ "$cur" == "$base" ]]; then
  git merge --ff-only "origin/$base"
  ok "Fast-forwarded '$base'."
else
  # Update base without checking it out.
  git fetch origin "$base:$base" 2>/dev/null || {
    git checkout "$base"; git merge --ff-only "origin/$base"; git checkout "$cur";
  }
  ok "Updated '$base' to origin."
  if [[ "$rebase" == "1" ]]; then
    git rebase "$base" && ok "Rebased '$cur' onto '$base'." || {
      warn "Rebase hit conflicts — run git-conflict-helper.sh"; exit 1;
    }
  fi
fi
