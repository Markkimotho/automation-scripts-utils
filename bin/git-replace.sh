#!/usr/bin/env bash
# git-replace.sh — replace a literal string in every tracked text file of a repo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-replace.sh — replace a literal string in every tracked text file of a repo.

Usage:
  git-replace.sh <old> <new> [options] [-- <pathspec>...]

Options:
  -C <dir>        Repo to work in (default: current dir)
  -i, --ignore-case  Match <old> case-insensitively (the replacement is used as given)
  --apply         Write the changes (default: preview only)
  -y, --yes       Skip confirmation with --apply
  -h, --help

Notes:
  - Literal match, not a regex. Binary and untracked files are never touched.
  - Pathspecs limit or exclude files, e.g.  -- . ':!vendor' ':!*.lock'
  - Exit codes: 0 = done or nothing to do, 2 = preview found matches.

Examples:
  git-replace.sh ml-ai-ops kiongahq                       # preview
  git-replace.sh ml-ai-ops kiongahq --apply -- . ':!CHANGELOG.md'
EOF
}

old="" new="" dir="." apply=0 icase=0 have_new=0
pathspecs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -C) dir="$2"; shift 2;;
    -i|--ignore-case) icase=1; shift;;
    --apply) apply=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    --) shift; pathspecs=("$@"); break;;
    -*) usage; die "Unknown option: $1";;
    *)
      if [[ -z "$old" ]]; then old="$1"
      elif [[ "$have_new" == "0" ]]; then new="$1"; have_new=1
      else usage; die "Unexpected argument: $1"; fi
      shift;;
  esac
done

[[ -n "$old" && "$have_new" == "1" ]] || { usage; die "<old> and <new> are required."; }
[[ "$old" != "$new" ]] || die "<old> and <new> are the same."
require_cmd git perl
cd "$dir"
is_git_repo || die "Not a git repo: $dir"
cd "$(git rev-parse --show-toplevel)"

grep_flags=(-I -F -c)
[[ "$icase" == "1" ]] && grep_flags+=(-i)
[[ ${#pathspecs[@]} -gt 0 ]] || pathspecs=(.)

matches="$(git grep "${grep_flags[@]}" -e "$old" -- "${pathspecs[@]}" 2>/dev/null || true)"
if [[ -z "$matches" ]]; then
  ok "No tracked text file contains '$old'."
  exit 0
fi

nfiles=0 nrefs=0
while IFS= read -r row; do
  n="${row##*:}"; f="${row%:*}"
  say "  $n  $f"
  nfiles=$((nfiles+1)); nrefs=$((nrefs+n))
done <<<"$matches"
info "$nrefs occurrences of '$old' in $nfiles files."

if [[ "$apply" == "0" ]]; then
  say "Preview only. Re-run with --apply to replace with '$new'."
  exit 2
fi
confirm "Replace '$old' with '$new' in $nfiles files?" || die "Aborted."

flags="g"; [[ "$icase" == "1" ]] && flags="gi"
while IFS= read -r row; do
  f="${row%:*}"
  OLD="$old" NEW="$new" perl -pi -e "s/\\Q\$ENV{OLD}\\E/\$ENV{NEW}/$flags" -- "$f"
done <<<"$matches"

left="$(git grep "${grep_flags[@]}" -e "$old" -- "${pathspecs[@]}" 2>/dev/null || true)"
[[ -z "$left" ]] || die "Some occurrences remain:"$'\n'"$left"
ok "Replaced $nrefs occurrences in $nfiles files. Review with: git diff --stat"
