#!/usr/bin/env bash
# precommit-install.sh — install pre-commit hooks consistently in a repo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
precommit-install.sh — install (and optionally scaffold) pre-commit hooks.

Usage:
  precommit-install.sh [options]

Options:
  --with-config   Write a starter .pre-commit-config.yaml if none exists
  -y, --yes       Skip confirmation (e.g. to auto-install pre-commit)
  -h, --help

If 'pre-commit' isn't installed, offers to install it with pip.
EOF
}

with_config=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-config) with_config=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) usage; die "Unexpected argument: $1";;
  esac
done

is_git_repo || die "Not inside a git repository."

if ! command -v pre-commit >/dev/null 2>&1; then
  warn "pre-commit is not installed."
  if confirm "Install it with pip (pip install pre-commit)?"; then
    require_cmd python3
    python3 -m pip install --quiet pre-commit || die "pip install pre-commit failed."
    ok "Installed pre-commit."
  else
    die "pre-commit required — see https://pre-commit.com"
  fi
fi

if [[ ! -e .pre-commit-config.yaml ]]; then
  if [[ "$with_config" == "1" ]]; then
    cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
EOF
    ok "Wrote starter .pre-commit-config.yaml"
  else
    warn "No .pre-commit-config.yaml found. Re-run with --with-config to scaffold one."
  fi
fi

pre-commit install
ok "pre-commit hooks installed."
