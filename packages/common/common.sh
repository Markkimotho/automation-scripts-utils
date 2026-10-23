#!/usr/bin/env bash
# common.sh — shared helpers for the automation scripts.
# Source this file; do not execute it directly.
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/../lib/common.sh"

# Colors, disabled when not a TTY or when NO_COLOR is set.
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  _C_RED=$'\033[31m'; _C_GRN=$'\033[32m'; _C_YEL=$'\033[33m'
  _C_BLU=$'\033[34m'; _C_DIM=$'\033[2m';  _C_RST=$'\033[0m'
else
  _C_RED=; _C_GRN=; _C_YEL=; _C_BLU=; _C_DIM=; _C_RST=
fi

say()  { printf '%s\n' "$*"; }
info() { printf '%s%s%s\n' "$_C_BLU" "$*" "$_C_RST"; }
ok()   { printf '%s%s%s\n' "$_C_GRN" "$*" "$_C_RST"; }
warn() { printf '%s%s%s\n' "$_C_YEL" "$*" "$_C_RST" >&2; }
err()  { printf '%s%s%s\n' "$_C_RED" "$*" "$_C_RST" >&2; }
die()  { err "$*"; exit 1; }

# require_cmd cmd...  — die if any command is missing.
require_cmd() {
  local c
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || die "Required command not found: $c"
  done
}

# confirm "prompt"  — return 0 on yes.
# Honors ASSUME_YES=1 for non-interactive/CI use; refuses on a non-TTY otherwise.
confirm() {
  local prompt="${1:-Proceed?}" reply
  if [[ "${ASSUME_YES:-0}" == "1" ]]; then return 0; fi
  if [[ ! -t 0 ]]; then
    warn "Not a TTY and ASSUME_YES != 1 — refusing: $prompt"
    return 1
  fi
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]([Ee][Ss])?$ ]]
}

is_git_repo()    { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }
current_branch() { git rev-parse --abbrev-ref HEAD 2>/dev/null; }

# 0 (true) if there are staged or unstaged changes to tracked files.
has_uncommitted() {
  ! git diff --quiet --ignore-submodules 2>/dev/null \
  || ! git diff --cached --quiet --ignore-submodules 2>/dev/null
}

# 0 (true) if there are untracked, non-ignored files.
has_untracked() {
  [[ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]]
}

# gh_authed — die unless the GitHub CLI is installed and logged in.
gh_authed() {
  require_cmd gh
  gh auth status >/dev/null 2>&1 || die "gh is not authenticated. Run: gh auth login"
}
