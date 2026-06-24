#!/usr/bin/env bash
# gh-create-repo.sh — create a GitHub repo and optionally push a local dir to it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
gh-create-repo.sh — create a GitHub repo and optionally push a local dir to it.

Usage:
  gh-create-repo.sh <name> [options]

Options:
  --public | --private        Visibility (default: private)
  -d, --description <text>     Repo description
  -s, --source <dir>           Local dir to push (default: current dir)
  -p, --push                   Init/commit/push the source dir to the new repo
  -b, --branch <name>          Default branch when initializing (default: main)
  -y, --yes                    Skip confirmation
  -h, --help

Examples:
  gh-create-repo.sh my-tool --public -d "Handy tool" --source . --push
  gh-create-repo.sh private-notes        # just create an empty private repo
EOF
}

name="" vis="--private" desc="" src="." push=0 branch="main"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --public) vis="--public"; shift;;
    --private) vis="--private"; shift;;
    -d|--description) desc="$2"; shift 2;;
    -s|--source) src="$2"; shift 2;;
    -p|--push) push=1; shift;;
    -b|--branch) branch="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) name="$1"; shift;;
  esac
done

[[ -n "$name" ]] || { usage; die "Repo name required."; }
gh_authed
require_cmd git

owner="$(gh api user -q .login)"
info "Will create ${vis#--} repo: $owner/$name"
[[ "$push" == "1" ]] && info "Then push local dir: $(cd "$src" && pwd)"
confirm "Proceed?" || die "Aborted."

create_args=("$name" "$vis")
[[ -n "$desc" ]] && create_args+=(--description "$desc")

if [[ "$push" == "1" ]]; then
  cd "$src"
  if ! is_git_repo; then
    git init -b "$branch" >/dev/null
    ok "Initialized git repo on branch '$branch'."
  fi
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    [[ -n "$(git status --porcelain)" ]] || die "Nothing to commit in '$src'."
    git add -A
    git commit -m "Initial commit" >/dev/null
    ok "Created initial commit."
  fi
  gh repo create "${create_args[@]}" --source=. --remote=origin --push
  ok "Created and pushed: https://github.com/$owner/$name"
else
  gh repo create "${create_args[@]}"
  ok "Created: https://github.com/$owner/$name"
fi
