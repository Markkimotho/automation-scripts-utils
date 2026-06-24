#!/usr/bin/env bash
# clean-artifacts.sh — remove build/cache junk. Dry-run by default.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
clean-artifacts.sh — delete build/cache artifacts. Lists by default; --apply deletes.

Usage:
  clean-artifacts.sh [dir] [options]

Options:
  --apply      Actually delete (default: dry-run, list only)
  --node       Also remove node_modules
  -y, --yes    Skip confirmation when applying
  -h, --help

Targets: __pycache__, *.pyc, .pytest_cache, .mypy_cache, .ruff_cache, dist,
build, *.egg-info, .DS_Store (+ node_modules with --node).
EOF
}

dir="." apply=0 node=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) apply=1; shift;;
    --node) node=1; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) dir="$1"; shift;;
  esac
done

[[ -d "$dir" ]] || die "Not a directory: $dir"

# Build the find expression for matching artifacts.
names=(__pycache__ .pytest_cache .mypy_cache .ruff_cache dist build "*.egg-info")
[[ "$node" == "1" ]] && names+=(node_modules)

targets=()
while IFS= read -r p; do [[ -n "$p" ]] && targets+=("$p"); done < <(
  for n in "${names[@]}"; do
    find "$dir" -name "$n" -prune -print 2>/dev/null
  done
  find "$dir" -type f \( -name '*.pyc' -o -name '.DS_Store' \) 2>/dev/null
)

if [[ "${#targets[@]}" -eq 0 ]]; then
  ok "No artifacts found under '$dir'."
  exit 0
fi

info "Artifacts under '$dir' (${#targets[@]}):"
for t in "${targets[@]}"; do say "  $t"; done

if [[ "$apply" != "1" ]]; then
  say "(dry run — nothing deleted; pass --apply to remove)"
  exit 0
fi

confirm "Delete these ${#targets[@]} item(s)?" || die "Aborted."
for t in "${targets[@]}"; do rm -rf "$t"; done
ok "Removed ${#targets[@]} item(s)."
