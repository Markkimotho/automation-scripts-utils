#!/usr/bin/env bash
# gh-pr-open.sh — push the current branch and open a PR in one step.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
gh-pr-open.sh — push the current branch and open a pull request.

Usage:
  gh-pr-open.sh [options]

Options:
  -t, --title <text>     PR title (default: gh --fill from commits)
  -b, --base <branch>    Base branch (default: repo default)
  -d, --draft            Open as a draft
  -w, --web              Open the PR in a browser after creating
  -y, --yes              Skip confirmation
  -h, --help

Refuses to open a PR from the base branch itself.
EOF
}

title="" base="" draft=0 web=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--title) title="$2"; shift 2;;
    -b|--base) base="$2"; shift 2;;
    -d|--draft) draft=1; shift;;
    -w|--web) web=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) usage; die "Unexpected argument: $1";;
  esac
done

is_git_repo || die "Not inside a git repository."
gh_authed

branch="$(current_branch)"
[[ -n "$branch" && "$branch" != "HEAD" ]] || die "Detached HEAD — checkout a branch first."

# Determine the default base if not given.
if [[ -z "$base" ]]; then
  base="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)"
fi
[[ "$branch" != "$base" ]] || die "You're on the base branch '$base'. Switch to a feature branch."

info "Push '$branch' and open a PR into '$base'${draft:+ (draft)}."
confirm "Proceed?" || die "Aborted."

git push -u origin "$branch"

create=(gh pr create --base "$base")
if [[ -n "$title" ]]; then create+=(--title "$title" --body ""); else create+=(--fill); fi
[[ "$draft" == "1" ]] && create+=(--draft)
[[ "$web" == "1" ]] && create+=(--web)
"${create[@]}"
ok "PR opened."
