#!/usr/bin/env bash
# gh-enable-pages.sh — enable GitHub Pages from the CLI via the API (repo owner).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
gh-enable-pages.sh — enable GitHub Pages via the API. Requires repo-owner access.

Usage:
  gh-enable-pages.sh [owner/name] [options]

Options:
  --workflow                 Source = GitHub Actions (default; modern deploys).
  --branch <branch>          Source = a branch (classic), e.g. gh-pages.
  --path </ or /docs>        Path for branch source (default: /).
  -y, --yes                  Skip confirmation.
  -h, --help

Notes:
  - With no repo argument, the current repo is used.
  - If Pages already exists, its build type is updated instead.
  - Needs the 'repo' (and Pages) scope on your gh token.

Examples:
  gh-enable-pages.sh                       # current repo, Actions source
  gh-enable-pages.sh owner/site --branch gh-pages --path /
EOF
}

repo="" build_type="workflow" branch="" path="/"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow) build_type="workflow"; shift;;
    --branch) build_type="legacy"; branch="$2"; shift 2;;
    --path) path="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) repo="$1"; shift;;
  esac
done

gh_authed
[[ -n "$repo" ]] || repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
[[ -n "$repo" ]] || die "No repo given and not inside a GitHub repo."

if [[ "$build_type" == "workflow" ]]; then
  info "Enable Pages for $repo with source = GitHub Actions"
else
  info "Enable Pages for $repo from branch '$branch' (path $path)"
fi
confirm "Proceed?" || die "Aborted."

api_set() {  # $1 = HTTP method
  if [[ "$build_type" == "workflow" ]]; then
    gh api -X "$1" "repos/$repo/pages" -f build_type=workflow >/dev/null 2>&1
  else
    gh api -X "$1" "repos/$repo/pages" \
      -f build_type=legacy \
      -f "source[branch]=$branch" -f "source[path]=$path" >/dev/null 2>&1
  fi
}

# POST creates; if it already exists, PUT updates.
if api_set POST; then
  ok "Pages enabled for $repo."
elif api_set PUT; then
  ok "Pages updated for $repo."
else
  die "Failed to enable Pages. Confirm you own '$repo' and gh has the 'repo'/Pages scope."
fi

url="$(gh api "repos/$repo/pages" -q .html_url 2>/dev/null || true)"
[[ -n "$url" ]] && say "Site URL: $url"
