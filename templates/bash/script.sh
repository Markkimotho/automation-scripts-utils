#!/usr/bin/env bash
set -euo pipefail
usage() { printf 'Usage: script.sh --path DIRECTORY\n'; }
path=""
while (($#)); do
  case "$1" in
    --path) [[ $# -ge 2 ]] || exit 2; path="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) usage >&2; exit 2;;
  esac
done
[[ -d "$path" ]] || { usage >&2; exit 2; }
printf 'Directory exists: %s\n' "$path"
