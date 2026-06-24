#!/usr/bin/env bash
# git-clean-branches.sh — delete local (and optionally remote) branches already merged.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-clean-branches.sh — delete branches already merged into the base.

Usage:
  git-clean-branches.sh [options]

Options:
  -b, --base <branch>   Base to check merges against (default: main, else master)
  --remote              Also delete merged branches on 'origin'
  -n, --dry-run         List what would be deleted, change nothing
  -y, --yes             Skip confirmation
  -h, --help

Never touches the base branch, the current branch, or HEAD.
EOF
}

base="" remote=0 dry=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--base) base="$2"; shift 2;;
    --remote) remote=1; shift;;
    -n|--dry-run) dry=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) usage; die "Unexpected argument: $1";;
  esac
done

is_git_repo || die "Not inside a git repository."
require_cmd git

if [[ -z "$base" ]]; then
  if git show-ref --verify --quiet refs/heads/main; then base="main"
  elif git show-ref --verify --quiet refs/heads/master; then base="master"
  else die "No main/master branch — pass --base."; fi
fi
cur="$(current_branch)"

# Local branches merged into base, excluding base and current.
locals=()
while IFS= read -r b; do
  b="${b#"${b%%[![:space:]]*}"}"     # ltrim
  b="${b#\* }"                        # strip current marker
  [[ -z "$b" || "$b" == "$base" || "$b" == "$cur" ]] && continue
  locals+=("$b")
done < <(git branch --merged "$base" 2>/dev/null)

if [[ "${#locals[@]}" -eq 0 ]]; then
  ok "No local branches merged into '$base' to clean."
else
  info "Local branches merged into '$base':"
  for b in "${locals[@]}"; do say "  $b"; done
  if [[ "$dry" == "1" ]]; then
    say "(dry run — nothing deleted)"
  elif confirm "Delete these ${#locals[@]} local branch(es)?"; then
    for b in "${locals[@]}"; do git branch -d "$b" && ok "deleted $b"; done
  fi
fi

if [[ "$remote" == "1" ]]; then
  require_cmd git
  git fetch --prune origin >/dev/null 2>&1 || warn "git fetch failed"
  remotes=()
  while IFS= read -r b; do
    b="${b#"${b%%[![:space:]]*}"}"
    [[ "$b" == origin/HEAD* || "$b" == "origin/$base" ]] && continue
    [[ "$b" == origin/* ]] || continue
    remotes+=("${b#origin/}")
  done < <(git branch -r --merged "origin/$base" 2>/dev/null)

  if [[ "${#remotes[@]}" -eq 0 ]]; then
    ok "No remote branches merged into 'origin/$base' to clean."
  else
    info "Remote branches merged into 'origin/$base':"
    for b in "${remotes[@]}"; do say "  origin/$b"; done
    if [[ "$dry" == "1" ]]; then
      say "(dry run — nothing deleted)"
    elif confirm "Delete these ${#remotes[@]} remote branch(es) on origin?"; then
      for b in "${remotes[@]}"; do git push origin --delete "$b" && ok "deleted origin/$b"; done
    fi
  fi
fi
