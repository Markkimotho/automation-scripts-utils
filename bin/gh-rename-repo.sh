#!/usr/bin/env bash
# gh-rename-repo.sh — rename a GitHub repo and update the local 'origin' remote.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
gh-rename-repo.sh — rename a GitHub repo and update the local 'origin' remote.

Usage:
  gh-rename-repo.sh <new-name> [options]

Options:
  -r, --repo <owner/name>     Repo to rename (default: current repo)
  --no-remote-update          Don't rewrite the local 'origin' URL
  -y, --yes                   Skip confirmation
  -h, --help

Notes:
  - GitHub keeps a redirect from the old name, but updating 'origin' avoids
    surprises on the next push.
  - A repo with GitHub Pages keeps Pages, but the project-site URL changes to
    the new name — update any site_url/links and redeploy.

Examples:
  gh-rename-repo.sh new-name
  gh-rename-repo.sh new-name -r owner/old-name --yes
EOF
}

new_name="" repo="" update_remote=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo) repo="$2"; shift 2;;
    --no-remote-update) update_remote=0; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) new_name="$1"; shift;;
  esac
done

[[ -n "$new_name" ]] || { usage; die "New name required."; }
gh_authed

[[ -n "$repo" ]] || repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
[[ -n "$repo" ]] || die "No repo given and not inside a GitHub repo."

owner="${repo%%/*}"
old_name="${repo##*/}"
[[ "$new_name" != "$old_name" ]] || die "New name is the same as the current name."

info "Rename $owner/$old_name  ->  $owner/$new_name"
confirm "Proceed?" || die "Aborted."

gh repo rename "$new_name" --repo "$repo" --yes
ok "Renamed to $owner/$new_name."

if [[ "$update_remote" == "1" ]] && is_git_repo; then
  cur="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -n "$cur" && "$cur" == *"$old_name"* ]]; then
    suffix=""; [[ "$cur" == *.git ]] && suffix=".git"
    base="${cur%.git}"      # strip trailing .git if present
    base="${base%/*}"       # strip the old repo-name segment
    newurl="$base/$new_name$suffix"
    git remote set-url origin "$newurl"
    ok "Updated origin -> $newurl"
  else
    warn "origin doesn't reference '$old_name' — left unchanged."
  fi
fi

url="$(gh repo view "$owner/$new_name" --json url -q .url 2>/dev/null || true)"
[[ -n "$url" ]] && say "Repo URL: $url"
