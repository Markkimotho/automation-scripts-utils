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

echo "== clean-artifacts.sh =="
TMPA="$(mktemp -d)"
mkdir -p "$TMPA/pkg/__pycache__"; printf x > "$TMPA/pkg/__pycache__/m.pyc"; printf y > "$TMPA/.DS_Store"
out_art="$( "$BIN/clean-artifacts.sh" "$TMPA" 2>/dev/null || true )"
if printf '%s' "$out_art" | grep -q '__pycache__'; then t_pass "dry-run lists __pycache__"; else t_fail "dry-run lists __pycache__"; fi
check "dry-run leaves files"  "[ -d '$TMPA/pkg/__pycache__' ]"
( "$BIN/clean-artifacts.sh" "$TMPA" --apply -y >/dev/null 2>&1 )
check "apply removes __pycache__" "[ ! -d '$TMPA/pkg/__pycache__' ]"

echo "== snapshot.sh =="
TMPB="$(mktemp -d)"; printf data > "$TMPB/file.txt"; OUTB="$(mktemp -d)"
( "$BIN/snapshot.sh" "$TMPB" --out "$OUTB" >/dev/null 2>&1 )
check "creates a tar.gz" "ls '$OUTB'/*.tar.gz >/dev/null 2>&1"

echo "== git-split-repo.sh =="
TMPS="$(mktemp -d)"
(
  cd "$TMPS"
  git init -q -b main src && cd src
  mkdir -p python/sdk docs go
  printf a > python/sdk/a.py; printf d > docs/i.md; git add .; git commit -qm one
  printf b > python/sdk/b.py; git add .; git commit -qm two
  printf g > go/x.go; git add .; git commit -qm go-only; git tag v1
)
printf '# comment\npython/sdk/ sdk/\n\ndocs/\n' > "$TMPS/m.txt"
( "$BIN/git-split-repo.sh" "$TMPS/src" "$TMPS/out" -m "$TMPS/m.txt" >/dev/null 2>&1 )
check "split creates repo"                  "[ -d '$TMPS/out/.git' ]"
check "split keeps touching commits only"   "[ \"\$(git -C '$TMPS/out' rev-list --count HEAD)\" = 2 ]"
check "split moves path (sdk/a.py)"         "git -C '$TMPS/out' ls-files --error-unmatch sdk/a.py >/dev/null 2>&1"
check "split drops other paths (go/)"       "[ -z \"\$(git -C '$TMPS/out' ls-files go)\" ]"
check "split drops tags"                    "[ -z \"\$(git -C '$TMPS/out' tag)\" ]"
check "split leaves source untouched"       "[ \"\$(git -C '$TMPS/src' rev-list --count HEAD)\" = 3 ]"
( "$BIN/git-split-repo.sh" "$TMPS/src" "$TMPS/root" -p python/sdk/=. >/dev/null 2>&1 )
check "split moves dir to root (=.)"        "[ -f '$TMPS/root/a.py' ]"
printf 'draft' > "$TMPS/src/docs/draft 2.md"; ( cd "$TMPS/src"; git add .; git commit -qm draft )
( "$BIN/git-split-repo.sh" "$TMPS/src" "$TMPS/ex" -p docs/=. -p '!docs/draft 2.md' >/dev/null 2>&1 )
check "split excludes a path in a kept dir" "[ -f '$TMPS/ex/i.md' ] && [ ! -e '$TMPS/ex/draft 2.md' ] && [ -z \"\$(git -C '$TMPS/ex' log --all --format=%H -- 'draft 2.md')\" ]"
git -C "$TMPS/src" reset -q --hard HEAD~1
( "$BIN/git-split-repo.sh" "$TMPS/src" "$TMPS/out" -p docs/ >/dev/null 2>&1 ); rc=$?
check "split refuses existing target"       "[ $rc -ne 0 ]"
( "$BIN/git-split-repo.sh" "$TMPS/src" "$TMPS/esc" -p ../etc >/dev/null 2>&1 ); rc=$?
check "split refuses paths outside repo"    "[ $rc -ne 0 ] && [ ! -e '$TMPS/esc' ]"

echo "== git-replace.sh =="
(
  cd "$TMPS/src"
  printf 'see github.com/ml-ai-ops/platform\nML-AI-OPS stays\n' > r.md
  printf 'ml-ai-ops untracked\n' > untracked.md
  git add r.md; git commit -qm r
)
( cd "$TMPS/src"; "$BIN/git-replace.sh" ml-ai-ops kiongahq >/dev/null 2>&1 ); rc=$?
check "replace preview exits 2"             "[ $rc -eq 2 ]"
check "replace preview writes nothing"      "grep -q ml-ai-ops '$TMPS/src/r.md'"
( cd "$TMPS/src"; "$BIN/git-replace.sh" ml-ai-ops kiongahq --apply >/dev/null 2>&1 )
check "replace --apply rewrites"            "grep -q 'github.com/kiongahq/platform' '$TMPS/src/r.md'"
check "replace is case-sensitive"           "grep -q 'ML-AI-OPS stays' '$TMPS/src/r.md'"
check "replace skips untracked files"       "grep -q ml-ai-ops '$TMPS/src/untracked.md'"
( cd "$TMPS/src"; "$BIN/git-replace.sh" ml-ai-ops kiongahq --apply >/dev/null 2>&1 ); rc=$?
check "replace with nothing left exits 0"   "[ $rc -eq 0 ]"

echo "== gh-rename-org.sh --remotes-only =="
(
  cd "$TMPS/src"
  git remote add origin git@github.com:ml-ai-ops/platform.git
  git remote add up https://github.com/ML-AI-OPS/x.git
  git remote add other git@github.com:someone/ml-ai-ops.git
)
( "$BIN/gh-rename-org.sh" ml-ai-ops kiongahq --remotes-only -s "$TMPS" >/dev/null 2>&1 ); rc=$?
check "rename-org exits 0"                  "[ $rc -eq 0 ]"
check "rewrites ssh remote"                 "[ \"\$(git -C '$TMPS/src' remote get-url origin)\" = git@github.com:kiongahq/platform.git ]"
check "rewrites https remote (any case)"    "[ \"\$(git -C '$TMPS/src' remote get-url up)\" = https://github.com/kiongahq/x.git ]"
check "leaves repo named like the org"      "[ \"\$(git -C '$TMPS/src' remote get-url other)\" = git@github.com:someone/ml-ai-ops.git ]"
# A fake gh that behaves like the real one on a 404: error JSON on stdout, exit 1.
# orgs/<new> starts resolving on the second poll, as after a rename.
FAKEBIN="$TMPS/fakebin"; mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/gh" <<'FAKE'
#!/usr/bin/env bash
nf() { echo '{"message":"Not Found","status":"404"}'; exit 1; }
case "$1 $2" in
  "auth status") exit 0;;
  "repo list") echo platform; exit 0;;
  "api orgs/old-org") echo 42;;
  "api users/taken-org") [[ "$4" == .type ]] && echo Organization || echo 7;;
  "api users/new-org") nf;;
  "api user/memberships/orgs/old-org") echo admin;;
  "api orgs/new-org")
    if [[ -f "$FAKE_STATE" ]]; then echo 42; else touch "$FAKE_STATE"; nf; fi;;
  *) nf;;
esac
FAKE
chmod +x "$FAKEBIN/gh"
out_free="$( PATH="$FAKEBIN:$PATH" FAKE_STATE="$TMPS/polled" GH_RENAME_ORG_POLL=0 \
  "$BIN/gh-rename-org.sh" old-org new-org 2>&1 )"; rc=$?
check "free name (gh 404 on stdout) -> waits and succeeds" "[ $rc -eq 0 ]"
if printf '%s' "$out_free" | grep -q 'now serves the org as new-org'; then t_pass "detects completed rename by org id"; else t_fail "detects completed rename by org id"; fi
( PATH="$FAKEBIN:$PATH" "$BIN/gh-rename-org.sh" old-org taken-org >/dev/null 2>&1 ); rc=$?
check "taken name -> refuses"               "[ $rc -ne 0 ]"
( "$BIN/gh-rename-org.sh" ml-ai-ops ML-AI-OPS --remotes-only >/dev/null 2>&1 ); rc=$?
check "refuses same name (case-insensitive)" "[ $rc -ne 0 ]"
( "$BIN/gh-rename-org.sh" ml-ai-ops bad_name --remotes-only >/dev/null 2>&1 ); rc=$?
check "refuses invalid name"                "[ $rc -ne 0 ]"

echo "== gh-org-clone.sh (local base url) =="
( "$BIN/gh-org-clone.sh" x "$TMPS/ws" --repos out,root --base-url "$TMPS/" >/dev/null 2>&1 ); rc=$?
check "clones listed repos"                 "[ $rc -eq 0 ] && [ -d '$TMPS/ws/out/.git' ] && [ -d '$TMPS/ws/root/.git' ]"
printf dirty >> "$TMPS/ws/out/sdk/a.py"
( "$BIN/gh-org-clone.sh" x "$TMPS/ws" --repos out,root,missing --base-url "$TMPS/" --pull >/dev/null 2>&1 ); rc=$?
check "missing repo -> exit 1"              "[ $rc -eq 1 ]"
check "dirty clone left untouched"          "grep -q dirty '$TMPS/ws/out/sdk/a.py'"
rm -rf "$TMPS"

echo "== bash usage/help exits 0 =="
for s in gh-merge-pr gh-create-repo gh-enable-pages gh-rename-repo \
         gh-rename-org gh-org-clone git-split-repo git-replace \
         git-conflict-helper git-safe-checkout git-clean-branches gh-pr-open git-sync \
         dev-doctor proj-bootstrap precommit-install py-check \
         clean-artifacts snapshot py-venv-rebuild port-kill; do
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
           deps-unused deps-outdated vuln-scan lic-audit data-convert secret-scan; do
    ( "$PY" "$BIN/$s.py" --help >/dev/null 2>&1 ); check "$s --help" "[ $? -eq 0 ]"
  done

  echo "== data-convert.py (csv -> json) =="
  TMPC="$(mktemp -d)"
  printf 'name,age\nAda,36\nLin,28\n' > "$TMPC/in.csv"
  out_json="$( "$PY" "$BIN/data-convert.py" "$TMPC/in.csv" --to json 2>/dev/null || true )"
  if printf '%s' "$out_json" | grep -q '"name": "Ada"'; then t_pass "csv->json"; else t_fail "csv->json"; fi

  echo "== secret-scan.py =="
  TMPD="$(mktemp -d)"
  printf 'key = "AKIAIOSFODNN7EXAMPLE"\n' > "$TMPD/leak.py"
  ( "$PY" "$BIN/secret-scan.py" "$TMPD/leak.py" >/dev/null 2>&1 ); check "flags AWS key -> exit 2" "[ $? -eq 2 ]"
  printf 'x = 1\n' > "$TMPD/clean.py"
  ( "$PY" "$BIN/secret-scan.py" "$TMPD/clean.py" >/dev/null 2>&1 ); check "clean file -> exit 0" "[ $? -eq 0 ]"
  rm -rf "$TMPC" "$TMPD"

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

rm -rf "$TMP" "$TMP2" "$TMP3" "$TMP4" "$TMPA" "$TMPB" "$OUTB"
echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
