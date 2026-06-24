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

echo "== dev-doctor.sh =="
( "$BIN/dev-doctor.sh" >/dev/null 2>&1 ); check "exits 0 (git+bash present)" "[ $? -eq 0 ]"

echo "== proj-bootstrap.sh =="
TMP4="$(mktemp -d)"
( "$BIN/proj-bootstrap.sh" "$TMP4/proj" --name proj --flavor python --license mit -y >/dev/null 2>&1 )
check "creates README"      "[ -f '$TMP4/proj/README.md' ]"
check "creates .gitignore"  "[ -f '$TMP4/proj/.gitignore' ]"
check "creates pre-commit"  "[ -f '$TMP4/proj/.pre-commit-config.yaml' ]"
check "creates CI workflow" "[ -f '$TMP4/proj/.github/workflows/ci.yml' ]"
check "creates LICENSE"     "[ -f '$TMP4/proj/LICENSE' ]"
check "git initialized"     "[ -d '$TMP4/proj/.git' ]"

echo "== bash usage/help exits 0 =="
for s in gh-merge-pr gh-create-repo gh-enable-pages gh-rename-repo \
         git-conflict-helper git-safe-checkout git-clean-branches gh-pr-open git-sync \
         dev-doctor proj-bootstrap precommit-install \
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
  for s in gh-pr-status gh-release env-check version-bump lockfile-drift \
           deps-unused deps-outdated vuln-scan lic-audit; do
    ( "$PY" "$BIN/$s.py" --help >/dev/null 2>&1 ); check "$s --help" "[ $? -eq 0 ]"
  done

  echo "== env-check.py =="
  TMP5="$(mktemp -d)"
  printf 'A=1\nB=2\nC=3\n' > "$TMP5/.env.example"
  printf 'A=x\nB=y\n' > "$TMP5/.env"           # missing C
  ( cd "$TMP5"; "$PY" "$BIN/env-check.py" >/dev/null 2>&1 ); check "missing key -> exit 2" "[ $? -eq 2 ]"
  printf 'A=x\nB=y\nC=z\n' > "$TMP5/.env"      # complete
  ( cd "$TMP5"; "$PY" "$BIN/env-check.py" >/dev/null 2>&1 ); check "complete -> exit 0" "[ $? -eq 0 ]"

  echo "== version-bump.py =="
  TMP6="$(mktemp -d)"
  printf '{"name":"x","version":"1.2.3"}\n' > "$TMP6/package.json"
  ( cd "$TMP6"; "$PY" "$BIN/version-bump.py" patch >/dev/null 2>&1 )
  check "package.json bumped to 1.2.4" "grep -q '1.2.4' '$TMP6/package.json'"
  ( cd "$TMP6"; "$PY" "$BIN/version-bump.py" minor >/dev/null 2>&1 )
  check "minor bump -> 1.3.0" "grep -q '1.3.0' '$TMP6/package.json'"

  echo "== lockfile-drift.py =="
  TMP7="$(mktemp -d)"
  printf '{"name":"x"}\n' > "$TMP7/package.json"   # no lockfile -> drift
  ( cd "$TMP7"; "$PY" "$BIN/lockfile-drift.py" >/dev/null 2>&1 ); check "missing lock -> exit 2" "[ $? -eq 2 ]"
  printf '{}' > "$TMP7/package-lock.json"; sleep 1; touch "$TMP7/package-lock.json"
  ( cd "$TMP7"; "$PY" "$BIN/lockfile-drift.py" >/dev/null 2>&1 ); check "lock present+newer -> exit 0" "[ $? -eq 0 ]"

  echo "== deps-unused.py =="
  TMP8="$(mktemp -d)"
  printf 'requests\nclick\n' > "$TMP8/requirements.txt"
  printf 'import requests\nrequests.get("x")\n' > "$TMP8/app.py"   # click unused
  out_unused="$( cd "$TMP8"; "$PY" "$BIN/deps-unused.py" 2>/dev/null || true )"
  if printf '%s' "$out_unused" | grep -q 'click'; then t_pass "flags unused click"; else t_fail "flags unused click"; fi
  if printf '%s' "$out_unused" | grep -q 'requests'; then t_fail "does not flag used requests"; else t_pass "does not flag used requests"; fi

  echo "== empty-dir behavior (polyglot tools exit 0) =="
  TMP9="$(mktemp -d)"
  for s in lockfile-drift deps-outdated vuln-scan; do
    ( cd "$TMP9"; "$PY" "$BIN/$s.py" >/dev/null 2>&1 ); check "$s empty dir -> exit 0" "[ $? -eq 0 ]"
  done
  rm -rf "$TMP5" "$TMP6" "$TMP7" "$TMP8" "$TMP9"
fi

rm -rf "$TMP" "$TMP2" "$TMP3" "$TMP4"
echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
