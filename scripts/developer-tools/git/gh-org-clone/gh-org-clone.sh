#!/usr/bin/env bash
# gh-org-clone.sh — clone (or update) every repo of a GitHub org into one workspace.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../../packages/common/common.sh
source "$SCRIPT_DIR/../../../../packages/common/common.sh"

usage() {
  cat <<'EOF'
gh-org-clone.sh — clone (or update) every repo of a GitHub org into one workspace.

Usage:
  gh-org-clone.sh <org> [dir] [options]

Options:
  --https                Clone over HTTPS (default: SSH)
  --include-archived     Also clone archived repos
  --repos <a,b,c>        Only these repos (skips listing the org)
  --base-url <url>       Clone from <url><repo> instead of GitHub (mirrors, tests)
  --pull                 Fast-forward repos that are already cloned
  -h, --help

Notes:
  - dir defaults to ./<org>. Existing clones are never reset or overwritten;
    with --pull they get 'git pull --ff-only' and are skipped if dirty.
  - Exit code 1 if any clone or pull failed; the rest still run.

Examples:
  gh-org-clone.sh kiongahq ~/kionga
  gh-org-clone.sh kiongahq ~/kionga --pull
EOF
}

org="" dir="" proto="ssh" archived=0 repos_csv="" base_url="" pull=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --https) proto="https"; shift;;
    --include-archived) archived=1; shift;;
    --repos) repos_csv="$2"; shift 2;;
    --base-url) base_url="$2"; shift 2;;
    --pull) pull=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *)
      if [[ -z "$org" ]]; then org="$1"
      elif [[ -z "$dir" ]]; then dir="$1"
      else usage; die "Unexpected argument: $1"; fi
      shift;;
  esac
done

[[ -n "$org" ]] || { usage; die "<org> is required."; }
require_cmd git
dir="${dir:-./$org}"
mkdir -p "$dir"

if [[ -n "$repos_csv" ]]; then
  repos="$(printf '%s' "$repos_csv" | tr ',' '\n' | sed '/^$/d')"
else
  gh_authed
  filter='.[] | select(.isArchived == false) | .name'
  [[ "$archived" == "1" ]] && filter='.[].name'
  repos="$(gh repo list "$org" --limit 1000 --json name,isArchived -q "$filter" | sort)"
fi
[[ -n "$repos" ]] || die "No repositories found for $org."

if [[ -z "$base_url" ]]; then
  if [[ "$proto" == "ssh" ]]; then base_url="git@github.com:$org/"; else base_url="https://github.com/$org/"; fi
fi

cloned=0 updated=0 skipped=0 failed=0
while IFS= read -r name; do
  dest="$dir/$name"
  if [[ -d "$dest/.git" || -f "$dest/.git" ]]; then
    if [[ "$pull" == "1" ]]; then
      if [[ -n "$(git -C "$dest" status --porcelain)" ]]; then
        warn "  dirty, skipped: $name"; skipped=$((skipped+1))
      elif git -C "$dest" pull -q --ff-only; then
        ok "  updated: $name"; updated=$((updated+1))
      else
        err "  pull failed: $name"; failed=$((failed+1))
      fi
    else
      say "  present: $name"; skipped=$((skipped+1))
    fi
  elif [[ -e "$dest" ]]; then
    err "  exists and is not a git repo: $dest"; failed=$((failed+1))
  elif git clone -q "${base_url}${name}" "$dest"; then
    ok "  cloned: $name"; cloned=$((cloned+1))
  else
    err "  clone failed: $name"; failed=$((failed+1))
  fi
done <<<"$repos"

info "$org -> $dir: $cloned cloned, $updated updated, $skipped unchanged, $failed failed."
[[ "$failed" -eq 0 ]]
