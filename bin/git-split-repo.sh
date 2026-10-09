#!/usr/bin/env bash
# git-split-repo.sh — extract paths of a repo into a new repo, keeping their history.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-split-repo.sh — extract paths of a repo into a new repo, keeping their history.

Usage:
  git-split-repo.sh <source-repo> <target-dir> [options]

Options:
  -p, --path <src>[=<dest>]    Keep <src> (file or dir/); with =<dest>, move it.
                               Repeatable. Use =. to move a directory to the root.
                               Prefix with ! to drop a path inside a kept one
                               (matched against the source path, e.g. '!docs/draft.md').
  -m, --manifest <file>        Read paths from a file: one "<src> [<dest>]" per line,
                               blank lines and # comments ignored.
  -b, --branch <name>          Branch to split (default: the source's current branch)
      --publish <owner/name>   Create the GitHub repo and push the result
      --public | --private     Visibility when publishing (default: private)
  -d, --description <text>     Repo description when publishing
  -y, --yes                    Skip confirmation
  -h, --help

Notes:
  - Needs git-filter-repo (pip install git-filter-repo). The source is never
    modified: the script works on a fresh clone in <target-dir>.
  - Commits that touched none of the kept paths are dropped; the rest keep their
    authors, dates and messages (hashes change, as with any history rewrite).
  - Only the chosen branch is kept, renamed to 'main'. Tags are dropped.

Examples:
  git-split-repo.sh ~/mlops ~/kionga/sdk-python -p python/mlaiops_sdk/=mlaiops_sdk/
  git-split-repo.sh ~/mlops ~/kionga/docs -m docs.manifest --publish kiongahq/docs --public
EOF
}

src="" target="" branch="" publish="" vis="--private" desc=""
paths=()
excludes=()

add_path() {
  local spec="$1"
  [[ -n "$spec" ]] || return 0
  local bare="${spec#!}"
  [[ "$bare" != /* && "$bare" != *..* && -n "$bare" ]] || die "Paths must be relative and inside the repo: $spec"
  if [[ "$spec" == !* ]]; then excludes+=("$bare"); else paths+=("$spec"); fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--path) add_path "$2"; shift 2;;
    -m|--manifest)
      [[ -f "$2" ]] || die "Manifest not found: $2"
      while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"
        a="" b=""
        read -r a b _ <<<"$line" || true
        [[ -n "$a" ]] || continue
        if [[ -n "$b" ]]; then add_path "$a=$b"; else add_path "$a"; fi
      done < "$2"
      shift 2;;
    -b|--branch) branch="$2"; shift 2;;
    --publish) publish="$2"; shift 2;;
    --public) vis="--public"; shift;;
    --private) vis="--private"; shift;;
    -d|--description) desc="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *)
      if [[ -z "$src" ]]; then src="$1"
      elif [[ -z "$target" ]]; then target="$1"
      else usage; die "Unexpected argument: $1"; fi
      shift;;
  esac
done

[[ -n "$src" && -n "$target" ]] || { usage; die "Source repo and target dir are required."; }
[[ ${#paths[@]} -gt 0 ]] || die "Nothing to keep: give at least one --path or a --manifest."
require_cmd git
git filter-repo --version >/dev/null 2>&1 || die "git-filter-repo not found. Install: pip install git-filter-repo"
git -C "$src" rev-parse --git-dir >/dev/null 2>&1 || die "Not a git repo: $src"
[[ ! -e "$target" ]] || die "Target already exists: $target"
[[ -z "$publish" || "$publish" == */* ]] || die "--publish needs owner/name, got: $publish"

src="$(cd "$src" && pwd)"
[[ -n "$branch" ]] || branch="$(git -C "$src" rev-parse --abbrev-ref HEAD)"
git -C "$src" rev-parse --verify -q "refs/heads/$branch" >/dev/null || die "Branch not found in source: $branch"

filter_args=()
for spec in "${paths[@]}"; do
  from="${spec%%=*}"
  filter_args+=(--path "$from")
  if [[ "$spec" == *=* ]]; then
    to="${spec#*=}"
    [[ "$to" == "." ]] && to=""
    filter_args+=(--path-rename "$from:$to")
  fi
done

info "Split $src ($branch) -> $target"
for spec in "${paths[@]}"; do say "  keep ${spec%%=*}${spec#"${spec%%=*}"}"; done
if [[ ${#excludes[@]} -gt 0 ]]; then
  for ex in "${excludes[@]}"; do say "  drop $ex"; done
fi
[[ -n "$publish" ]] && info "Then publish to github.com/$publish (${vis#--})"
confirm "Proceed?" || die "Aborted."

mkdir -p "$(dirname "$target")"
git clone -q --no-local --single-branch --branch "$branch" "$src" "$target"
(
  cd "$target"
  if [[ ${#excludes[@]} -gt 0 ]]; then
    drop_args=()
    for ex in "${excludes[@]}"; do drop_args+=(--path "$ex"); done
    git filter-repo --quiet --invert-paths "${drop_args[@]}"
    # The clone is no longer fresh after the first pass; it is ours to rewrite.
    git filter-repo --quiet --force "${filter_args[@]}"
  else
    git filter-repo --quiet "${filter_args[@]}"
  fi
  for t in $(git tag -l); do git tag -d "$t" >/dev/null; done
  [[ "$branch" == "main" ]] || git branch -q -m "$branch" main
)

commits="$(git -C "$target" rev-list --count HEAD 2>/dev/null || echo 0)"
files="$(git -C "$target" ls-files | wc -l | tr -d ' ')"
[[ "$commits" -gt 0 && "$files" -gt 0 ]] || die "Split produced an empty repo; check the paths."
ok "Created $target: $commits commits, $files files."

if [[ -n "$publish" ]]; then
  gh_authed
  create_args=("$publish" "$vis" --source "$target" --remote origin --push)
  [[ -n "$desc" ]] && create_args+=(--description "$desc")
  gh repo create "${create_args[@]}"
  ok "Published: https://github.com/$publish"
fi
