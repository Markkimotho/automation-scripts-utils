#!/usr/bin/env bash
# run_tests.sh — gate tests for the automation scripts. No network, fast.
# Exercises the pure/local logic: shared helpers, conflict detection, and the
# dirty-tree detection in safe-checkout. Outward-facing gh calls are not tested
# here (they need auth/network) — those scripts share the same helpers that are.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/bin"
PASS=0 FAIL=0

# Named with a t_ prefix so sourcing lib/common.sh (which defines ok/say/...)
# can't clobber the test result counters.
t_pass() { printf '  \033[32mPASS\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
t_fail() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
check()  { if eval "$2"; then t_pass "$1"; else t_fail "$1"; fi; }

# Isolated git identity so commits work in CI.
export GIT_AUTHOR_NAME=test GIT_AUTHOR_EMAIL=test@test \
       GIT_COMMITTER_NAME=test GIT_COMMITTER_EMAIL=test@test \
       ASSUME_YES=1 NO_COLOR=1

echo "== lib/common.sh =="
# shellcheck source=../lib/common.sh
source "$ROOT/lib/common.sh"
check "require_cmd finds bash"              "require_cmd bash"
check "confirm honors ASSUME_YES"           "confirm 'x'"
check "has_uncommitted is a function"       "declare -F has_uncommitted >/dev/null"

echo "== git-conflict-helper.sh --check =="
TMP="$(mktemp -d)"
(
  cd "$TMP"
  git init -q -b main
  printf 'line1\nline2\n' > f.txt
  git add f.txt && git commit -qm init
  git checkout -q -b feature
  printf 'line1\nFEATURE\n' > f.txt && git commit -qam feature
  git checkout -q main
  printf 'line1\nMAIN\n' > f.txt && git commit -qam main
  git merge feature >/dev/null 2>&1 || true   # induce a conflict
)
# clean repo elsewhere reports 0
TMP2="$(mktemp -d)"; ( cd "$TMP2"; git init -q -b main; printf x > a; git add a; git commit -qm x )
( cd "$TMP2"; "$BIN/git-conflict-helper.sh" --check >/dev/null 2>&1 ); rc_clean=$?
( cd "$TMP";  "$BIN/git-conflict-helper.sh" --check >/dev/null 2>&1 ); rc_conf=$?
check "clean repo -> exit 0"                "[ $rc_clean -eq 0 ]"
check "conflicted repo -> exit 2"           "[ $rc_conf -eq 2 ]"
# Capture to a var first: piping the script into grep under pipefail would
# surface the script's exit (2), not grep's match result.
out_list="$( cd "$TMP"; "$BIN/git-conflict-helper.sh" --check 2>/dev/null || true )"
if printf '%s' "$out_list" | grep -q 'f.txt'; then
  t_pass "lists the conflicted file"
else
  t_fail "lists the conflicted file"
fi

echo "== git-safe-checkout.sh --check =="
( cd "$TMP2"; "$BIN/git-safe-checkout.sh" --check >/dev/null 2>&1 ); rc_cleanwt=$?
( cd "$TMP2"; echo dirty >> a; "$BIN/git-safe-checkout.sh" --check >/dev/null 2>&1 ); rc_dirty=$?
check "clean tree -> exit 0"                "[ $rc_cleanwt -eq 0 ]"
check "dirty tree -> exit 2"                "[ $rc_dirty -eq 2 ]"

echo "== git-clean-branches.sh --dry-run =="
TMP3="$(mktemp -d)"
(
  cd "$TMP3"
  git init -q -b main
  printf base > f; git add f; git commit -qm init
  git checkout -q -b done-feature
  printf more >> f; git commit -qam feature
  git checkout -q main
  git merge -q --no-edit done-feature   # cleanly merged -> eligible for cleanup
)
out_clean="$( cd "$TMP3"; "$BIN/git-clean-branches.sh" --dry-run 2>/dev/null || true )"
if printf '%s' "$out_clean" | grep -q 'done-feature'; then
  t_pass "lists merged branch in dry-run"
else
  t_fail "lists merged branch in dry-run"
fi

echo "== bash usage/help exits 0 =="
for s in gh-merge-pr gh-create-repo gh-enable-pages gh-rename-repo \
         git-conflict-helper git-safe-checkout git-clean-branches gh-pr-open git-sync \
         py-venv-rebuild port-kill; do
  ( "$BIN/$s.sh" --help >/dev/null 2>&1 ); check "$s --help" "[ $? -eq 0 ]"
done

echo "== python lane =="
PY="$(command -v python3 || true)"
if [[ -z "$PY" ]]; then
  t_fail "python3 available"
else
  t_pass "python3 available"
  check "common.py imports"  "$PY -c 'import sys;sys.path.insert(0,\"$ROOT/lib\");import common'"
  for s in gh-pr-status gh-release; do
    ( "$PY" "$BIN/$s.py" --help >/dev/null 2>&1 ); check "$s --help" "[ $? -eq 0 ]"
  done
fi

rm -rf "$TMP" "$TMP2" "$TMP3"
echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
