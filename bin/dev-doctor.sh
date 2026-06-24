#!/usr/bin/env bash
# dev-doctor.sh — check the tools these scripts (and common dev work) need.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
dev-doctor.sh — report which required dev tools are present, with install hints.

Usage:
  dev-doctor.sh [-h|--help]

Exit code is non-zero if any CORE tool (git, bash) is missing. Optional tools
only warn. This is the runnable version of the Prerequisites page.
EOF
}

case "${1:-}" in -h|--help) usage; exit 0;; "") ;; *) usage; die "Unknown option: $1";; esac

missing_core=0

# check_tool <name> <core|opt> <why> <brew-pkg> <apt-pkg>
check_tool() {
  local name="$1" kind="$2" why="$3" brew="$4" apt="$5"
  if command -v "$name" >/dev/null 2>&1; then
    local ver; ver="$("$name" --version 2>&1 | head -1 | cut -c1-60)"
    ok "  ✓ $name — ${ver:-installed}"
  else
    if [[ "$kind" == "core" ]]; then
      err "  ✗ $name MISSING (core) — $why"; missing_core=1
    else
      warn "  ○ $name missing (optional) — $why"
    fi
    say "       brew install $brew   |   apt-get install $apt"
  fi
}

info "Core"
check_tool git  core "version control; most scripts need it"       git  git
check_tool bash core "the scripts run on bash 3.2+"                bash bash

info "GitHub automation (gh-* scripts)"
check_tool gh opt "GitHub API/PR/repo automation"                gh   gh
check_tool jq opt "JSON parsing for gh-merge-pr"                 jq   jq

info "Environments & ports"
check_tool python3 opt "py-* and polyglot tooling"               python python3
check_tool lsof    opt "port-kill targets listeners"             lsof   lsof
check_tool pre-commit opt "git hook management"                  pre-commit pre-commit
check_tool docker  opt "containers / compose workflows"          docker docker.io

# gh installed but not authenticated is a common trap.
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    ok "  ✓ gh authenticated"
  else
    warn "  ○ gh installed but NOT authenticated — run: gh auth login"
  fi
fi

say ""
if [[ "$missing_core" -eq 0 ]]; then
  ok "Core tooling present."
else
  die "Missing core tooling — install the items marked ✗ above."
fi
