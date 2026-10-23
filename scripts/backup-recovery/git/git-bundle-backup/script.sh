#!/usr/bin/env bash
# Create a new committed-history backup without replacing existing archives.
set -euo pipefail
usage() {
  cat <<'USAGE'
Usage: git-bundle-backup --repository DIR --output FILE [--apply | --dry-run]
Default: preview only. --apply creates and verifies a new Git bundle of all refs.
Working-tree/index files, hooks and repository configuration are not backed up.
USAGE
}
fail() { printf 'git-bundle-backup: %s\n' "$1" >&2; exit 2; }
repository='' output='' apply=0 mode=''
while (($#)); do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --repository|--output)
      (($# >= 2)) || fail 'missing option value'
      if [[ "$1" == --repository ]]; then repository=$2; else output=$2; fi
      shift 2 ;;
    --apply|--dry-run)
      [[ -z "$mode" ]] || fail 'choose exactly one execution mode'
      mode=$1
      [[ "$1" != --apply ]] || apply=1
      shift ;;
    *) fail 'unknown option' ;;
  esac
done
[[ -n "$repository" && -n "$output" ]] || fail 'require --repository and --output'
for dependency in git python3 mktemp rm dirname basename; do
  command -v "$dependency" >/dev/null 2>&1 || fail "missing dependency: $dependency"
done
export GIT_ALLOW_PROTOCOL='' GIT_NO_LAZY_FETCH=1 GIT_TERMINAL_PROMPT=0
repository=$(cd -- "$repository" 2>/dev/null && pwd -P) || fail 'repository directory not found'
parent=$(dirname -- "$output")
parent=$(cd -- "$parent" 2>/dev/null && pwd -P) || fail 'output parent directory not found'
name=$(basename -- "$output")
output="$parent/$name"
[[ ! -e "$output" && ! -L "$output" ]] || fail 'output already exists'
git -C "$repository" rev-parse --git-dir >/dev/null 2>&1 || fail 'not a Git repository'
git -C "$repository" rev-parse --verify HEAD >/dev/null 2>&1 || fail 'repository has no commits'
[[ "$(git -C "$repository" rev-parse --is-shallow-repository)" == false ]] || fail 'shallow repositories are not complete backups'
if ((apply == 0)); then
  printf 'PREVIEW ONLY: create and verify a new bundle of all refs at %q\n' "$output"
  exit 0
fi
umask 077
stage=$(mktemp -d "$parent/.git-bundle-XXXXXXXX") || fail 'cannot create private staging directory'
trap 'rm -rf -- "$stage"' EXIT
if ! git -C "$repository" bundle create "$stage/backup.bundle" --all; then
  printf 'git-bundle-backup: bundle creation failed\n' >&2; exit 1
fi
if ! git -C "$repository" bundle verify "$stage/backup.bundle" >/dev/null; then
  printf 'git-bundle-backup: bundle verification failed\n' >&2; exit 1
fi
# os.link treats an existing destination directory as a collision, unlike ln.
if ! python3 - "$stage/backup.bundle" "$output" <<'PY'
import os
import sys
try:
    os.link(sys.argv[1], sys.argv[2])
except OSError:
    sys.exit(1)
PY
then
  fail 'cannot publish bundle; output exists or hard links are unavailable'
fi
printf 'Created verified bundle: %s\n' "$output"
