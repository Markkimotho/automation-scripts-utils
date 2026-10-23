#!/usr/bin/env bash
# gh-org-ci.sh — latest GitHub Actions runs for every repo of an org, in one table.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../../packages/common/common.sh
source "$SCRIPT_DIR/../../../../packages/common/common.sh"

usage() {
  cat <<'EOF'
gh-org-ci.sh — latest GitHub Actions runs for every repo of an org, in one table.

Usage:
  gh-org-ci.sh <org> [options]

Options:
  --repos <a,b,c>     Only these repos (default: every non-archived repo)
  -n, --runs <N>      Runs per repo (default: 3)
  --failed            Only show failed runs
  --wait              Poll every 30s until nothing is queued or in progress
  -h, --help

Exit codes: 0 all shown runs succeeded or are still running,
            2 at least one shown run failed (useful in scripts).

Examples:
  gh-org-ci.sh kiongahq
  gh-org-ci.sh kiongahq --repos serving,deploy --wait
EOF
}

org="" repos_csv="" runs=3 only_failed=0 wait=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repos) repos_csv="$2"; shift 2;;
    -n|--runs) runs="$2"; shift 2;;
    --failed) only_failed=1; shift;;
    --wait) wait=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) org="$1"; shift;;
  esac
done
[[ -n "$org" ]] || { usage; die "<org> is required."; }
[[ "$runs" =~ ^[1-9][0-9]*$ ]] || die "--runs must be a positive integer"
gh_authed

if [[ -n "$repos_csv" ]]; then
  repos="$(printf '%s' "$repos_csv" | tr ',' '\n' | sed '/^$/d')"
else
  repos="$(gh repo list "$org" --limit 1000 --json name,isArchived \
    -q '.[] | select(.isArchived == false) | .name' | sort)"
fi
[[ -n "$repos" ]] || die "No repositories found for $org."

# snapshot prints "repo<TAB>workflow<TAB>ref<TAB>status<TAB>conclusion<TAB>url" rows.
# A missing conclusion is "-": read with a tab IFS collapses empty fields.
snapshot() {
  local repo
  while IFS= read -r repo; do
    gh run list -R "$org/$repo" --limit "$runs" \
      --json workflowName,headBranch,status,conclusion,url \
      -q ".[] | [\"$repo\", .workflowName, .headBranch, .status, (if (.conclusion // \"\") == \"\" then \"-\" else .conclusion end), .url] | @tsv" \
      2>/dev/null || true
  done <<<"$repos"
}

rows="$(snapshot)"
if [[ "$wait" == "1" ]]; then
  while grep -qE $'\t(queued|in_progress|waiting|pending)\t' <<<"$rows"; do
    info "Runs still in progress; checking again in 30s..."
    sleep 30
    rows="$(snapshot)"
  done
fi

failed=0
printf '%-20s %-26s %-28s %s\n' REPO WORKFLOW REF RESULT
while IFS=$'\t' read -r repo workflow ref status conclusion url; do
  [[ -n "$repo" ]] || continue
  result="$conclusion"; [[ "$result" == "-" ]] && result="$status"
  [[ "$result" == "failure" || "$result" == "timed_out" ]] && failed=1
  [[ "$only_failed" == "1" && "$result" != "failure" && "$result" != "timed_out" ]] && continue
  printf '%-20s %-26s %-28s %s\n' "$repo" "${workflow:0:26}" "${ref:0:28}" "$result"
  [[ "$result" == "failure" ]] && say "  $url"
done <<<"$rows"

if [[ "$failed" == "1" ]]; then exit 2; fi
exit 0
