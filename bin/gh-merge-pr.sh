#!/usr/bin/env bash
# gh-merge-pr.sh — merge a GitHub PR from the CLI, safely.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
gh-merge-pr.sh — merge a GitHub PR from the CLI, safely.

Usage:
  gh-merge-pr.sh <pr-number> [options]

Options:
  -m, --method <merge|squash|rebase>   Merge method (default: squash)
  -d, --delete-branch                  Delete the head branch after merge
  -r, --repo <owner/name>              Target repo (default: current)
  -y, --yes                            Skip confirmation (sets ASSUME_YES)
  -h, --help

Behavior:
  - Verifies gh auth and polls the PR's mergeable state (~30s).
  - Refuses to merge a CONFLICTING PR (run git-conflict-helper.sh first).
  - Confirms before merging — this is an outward-facing action.

Examples:
  gh-merge-pr.sh 12 --squash --delete-branch
  gh-merge-pr.sh 7 -m merge -r owner/repo -y
EOF
}

method=squash delete_branch=0 repo="" pr=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--method) method="$2"; shift 2;;
    -d|--delete-branch) delete_branch=1; shift;;
    -r|--repo) repo="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) pr="$1"; shift;;
  esac
done

[[ -n "$pr" ]] || { usage; die "PR number required."; }
[[ "$method" =~ ^(merge|squash|rebase)$ ]] || die "Invalid --method: $method"
gh_authed
require_cmd jq

repo_args=(); [[ -n "$repo" ]] && repo_args=(--repo "$repo")

# Poll mergeability — GitHub computes it asynchronously.
state="UNKNOWN"
for _ in $(seq 1 10); do
  state="$(gh pr view "$pr" "${repo_args[@]}" --json mergeable -q .mergeable 2>/dev/null || echo UNKNOWN)"
  [[ "$state" == "MERGEABLE" || "$state" == "CONFLICTING" ]] && break
  sleep 3
done

[[ "$state" == "CONFLICTING" ]] && die "PR #$pr has conflicts. Resolve first (try git-conflict-helper.sh)."
[[ "$state" == "MERGEABLE"  ]] || warn "PR #$pr mergeable state is '$state' — proceeding cautiously."

title="$(gh pr view "$pr" "${repo_args[@]}" --json title -q .title 2>/dev/null || echo '(unknown)')"
info "About to ${method}-merge PR #$pr: $title"
confirm "Merge now?" || die "Aborted."

merge_args=(--"$method"); [[ "$delete_branch" == "1" ]] && merge_args+=(--delete-branch)
gh pr merge "$pr" "${repo_args[@]}" "${merge_args[@]}"
ok "Merged PR #$pr."
