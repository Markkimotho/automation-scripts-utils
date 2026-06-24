#!/usr/bin/env bash
# py-check.sh — run ruff + mypy + pytest (+ coverage) in one pass.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
py-check.sh — run the common Python checks in one shot.

Usage:
  py-check.sh [path] [options]

Options:
  --no-cov     Run pytest without coverage
  -h, --help

Runs whichever of ruff, mypy, and pytest are installed (skips the rest with a
note). Exit code is non-zero if any check fails.
EOF
}

path="." cov=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cov) cov=0; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) path="$1"; shift;;
  esac
done

fail=0
ran=0

run_step() {  # label  cmd...
  local label="$1"; shift
  info "› $label"
  if "$@"; then ok "  $label passed"; else err "  $label FAILED"; fail=1; fi
  ran=$((ran+1))
}

if command -v ruff >/dev/null 2>&1; then run_step "ruff" ruff check "$path"
else warn "ruff not installed — skipped"; fi

if command -v mypy >/dev/null 2>&1; then run_step "mypy" mypy "$path"
else warn "mypy not installed — skipped"; fi

if command -v pytest >/dev/null 2>&1; then
  if [[ "$cov" == "1" ]] && python3 -c "import pytest_cov" >/dev/null 2>&1; then
    run_step "pytest" pytest --cov="$path" -q
  else
    run_step "pytest" pytest -q
  fi
else warn "pytest not installed — skipped"; fi

say ""
if [[ "$ran" -eq 0 ]]; then
  warn "No Python checkers installed (ruff/mypy/pytest). Nothing run."
  exit 0
fi
[[ "$fail" -eq 0 ]] && ok "All checks passed." || die "Some checks failed."
