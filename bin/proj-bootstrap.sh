#!/usr/bin/env bash
# proj-bootstrap.sh — scaffold a new project: git, ignore, README, pre-commit, CI.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
proj-bootstrap.sh — scaffold a new project directory.

Usage:
  proj-bootstrap.sh [dir] [options]

Options:
  --name <name>            Project name (default: dir basename)
  --flavor <python|node|generic>   Picks the .gitignore (default: generic)
  --license <mit|none>     Add an MIT LICENSE (default: none)
  --no-git                 Don't run git init
  -y, --yes                Skip confirmation
  -h, --help

Creates: README.md, .gitignore, .pre-commit-config.yaml,
.github/workflows/ci.yml, and (optionally) LICENSE — without overwriting files
that already exist.
EOF
}

dir="." name="" flavor="generic" license="none" do_git=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) name="$2"; shift 2;;
    --flavor) flavor="$2"; shift 2;;
    --license) license="$2"; shift 2;;
    --no-git) do_git=0; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) dir="$1"; shift;;
  esac
done

[[ "$flavor" =~ ^(python|node|generic)$ ]] || die "Invalid --flavor: $flavor"
[[ -z "$name" ]] && name="$(basename "$(cd "$dir" 2>/dev/null && pwd || echo "$dir")")"

info "Scaffold project '$name' in '$dir' (flavor: $flavor, license: $license)"
confirm "Proceed?" || die "Aborted."

mkdir -p "$dir/.github/workflows"

write_if_absent() {  # path  <<heredoc content on stdin
  local path="$1"
  if [[ -e "$path" ]]; then warn "  skip (exists): ${path#"$dir"/}"; return; fi
  cat > "$path"
  ok "  created: ${path#"$dir"/}"
}

# README
write_if_absent "$dir/README.md" <<EOF
# $name

> One-line description.

## Getting started

\`\`\`bash
# ...
\`\`\`
EOF

# .gitignore by flavor
case "$flavor" in
  python) ignore=$'__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.env\n.pytest_cache/\ndist/\nbuild/\n*.egg-info/\n.DS_Store';;
  node)   ignore=$'node_modules/\ndist/\nbuild/\n.env\nnpm-debug.log*\ncoverage/\n.DS_Store';;
  *)      ignore=$'.env\ndist/\nbuild/\n*.log\n.DS_Store';;
esac
[[ -e "$dir/.gitignore" ]] && warn "  skip (exists): .gitignore" || { printf '%s\n' "$ignore" > "$dir/.gitignore"; ok "  created: .gitignore"; }

# pre-commit
write_if_absent "$dir/.pre-commit-config.yaml" <<'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
EOF

# CI
write_if_absent "$dir/.github/workflows/ci.yml" <<'EOF'
name: CI
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Add your build/test steps here"
EOF

# License
if [[ "$license" == "mit" ]]; then
  year="$(date +%Y)"
  write_if_absent "$dir/LICENSE" <<EOF
MIT License

Copyright (c) $year

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
EOF
fi

if [[ "$do_git" == "1" ]] && command -v git >/dev/null 2>&1; then
  if [[ ! -d "$dir/.git" ]]; then
    git -C "$dir" init -q -b main && ok "  git initialized (branch main)"
  fi
fi

ok "Project '$name' scaffolded."
