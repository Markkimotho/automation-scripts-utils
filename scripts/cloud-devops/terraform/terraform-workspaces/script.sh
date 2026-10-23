#!/usr/bin/env bash
set -euo pipefail
usage() { printf 'Usage: terraform-workspaces.sh [--dir PATH]\nList workspaces without modifying state.\n'; }
dir="."
while (($#)); do
  case "$1" in
    -h|--help) usage; exit 0;;
    --dir) [[ $# -gt 1 ]] || { usage >&2; exit 2; }; dir="$2"; shift 2;;
    *) usage >&2; exit 2;;
  esac
done
[[ -d "$dir" ]] || { echo "Directory does not exist: $dir" >&2; exit 2; }
command -v terraform >/dev/null || { echo "terraform is required" >&2; exit 2; }
cd "$dir"
terraform workspace list -no-color
