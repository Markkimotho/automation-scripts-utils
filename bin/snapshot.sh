#!/usr/bin/env bash
# snapshot.sh — timestamped tar.gz of a directory before a risky operation.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
snapshot.sh — make a timestamped backup of a directory.

Usage:
  snapshot.sh [dir] [options]

Options:
  -o, --out <dir>   Where to write the archive (default: /tmp)
  -h, --help

Writes <out>/<basename>-<UTC timestamp>.tar.gz. Cheap insurance before anything
destructive.
EOF
}

dir="." out="/tmp"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--out) out="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) dir="$1"; shift;;
  esac
done

[[ -d "$dir" ]] || die "Not a directory: $dir"
require_cmd tar
mkdir -p "$out"

base="$(basename "$(cd "$dir" && pwd)")"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$out/${base}-${ts}.tar.gz"
parent="$(cd "$dir" && cd .. && pwd)"

tar -czf "$archive" -C "$parent" "$base"
size="$(du -h "$archive" | cut -f1)"
ok "Snapshot: $archive ($size)"
