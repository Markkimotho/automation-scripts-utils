#!/usr/bin/env bash
# git-conflict-helper.sh — a rule-based guide to understanding & resolving
# git merge/rebase/cherry-pick conflicts.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
git-conflict-helper.sh — rule-based guide for git conflicts.

Usage:
  git-conflict-helper.sh [--check]

Options:
  --check    Non-interactive. Report state + conflicted files only.
             Exit 0 = clean, 2 = conflicts present.
  -h, --help

What it does:
  1. Confirms you're in a git repo and reports any operation in progress
     (merge / rebase / cherry-pick).
  2. Walks the common REASONS a conflict happens, and what to check — including
     asking whether you committed/stashed before you switched or pulled.
  3. Lists every conflicted file with its conflict-marker count.
  4. Offers safe per-file next steps (keep ours/theirs, edit, abort).
EOF
}

check_only=0
case "${1:-}" in
  --check) check_only=1;;
  -h|--help) usage; exit 0;;
  "") ;;
  *) usage; die "Unknown option: $1";;
esac

is_git_repo || die "Not inside a git repository."

git_dir="$(git rev-parse --git-dir)"
op="none"
if   [[ -f "$git_dir/MERGE_HEAD" ]]; then op="merge"
elif [[ -d "$git_dir/rebase-merge" || -d "$git_dir/rebase-apply" ]]; then op="rebase"
elif [[ -f "$git_dir/CHERRY_PICK_HEAD" ]]; then op="cherry-pick"
fi

conflicts=()
while IFS= read -r _line; do [[ -n "$_line" ]] && conflicts+=("$_line"); done \
  < <(git diff --name-only --diff-filter=U 2>/dev/null || true)

info "== git conflict helper =="
say "Branch:     $(current_branch)"
say "Operation:  $op in progress"
say "Conflicts:  ${#conflicts[@]} file(s)"

if [[ "${#conflicts[@]}" -eq 0 ]]; then
  if [[ "$op" == "none" ]]; then
    ok "No conflicts and no merge/rebase in progress. You're clean."
    exit 0
  fi
  warn "A $op is in progress but nothing is currently conflicted."
  say  "Resolved everything?  git $op --continue"
  say  "Want to bail out?      git $op --abort"
  exit 0
fi

say ""
info "Conflicted files:"
for f in "${conflicts[@]}"; do
  n="$(grep -c '^<<<<<<<' "$f" 2>/dev/null || echo 0)"
  say "  • $f  ($n conflict block(s))"
done

[[ "$check_only" == "1" ]] && exit 2

say ""
info "Why this conflict likely happened — check these in order:"
cat <<'RULES'
  1. Same lines edited on both sides.
     Both branches changed the SAME lines. Normal case — pick a winner or combine.

  2. You didn't commit/stash before switching or pulling.
     Uncommitted edits collide with incoming changes. Going forward: commit or
     stash BEFORE checkout / pull / merge.

  3. Your branch is stale (behind the base).
     The base moved on while you worked. Re-sync:
        git fetch origin
        git merge origin/<base>      (or:  git rebase origin/<base>)

  4. Edit-vs-delete or a rename.
     A file was deleted/renamed on one side and edited on the other. git can't
     auto-merge that — decide whether to keep or remove it.

  5. Whitespace / line-ending churn (CRLF vs LF).
     Whole-file conflicts with no real change usually mean line-ending drift.
     Inspect:  git diff --check    and review core.autocrlf.
RULES

say ""
if confirm "Did you commit or stash your branch BEFORE you switched/pulled?"; then
  ok "Good — then this is most likely cause #1 or #3 above."
else
  warn "That is very likely the cause."
  say  "In future run 'git status' and commit/stash first."
  say  "Right now your changes are mixed into the $op. To redo cleanly:  git $op --abort"
fi

for f in "${conflicts[@]}"; do
  say ""
  info "Resolve: $f"
  say "  [o] keep OURS (current branch)   [t] keep THEIRS (incoming)"
  say "  [e] edit by hand (\$EDITOR)        [d] show diff   [s] skip"
  while true; do
    read -r -p "  choice [o/t/e/d/s]: " ch || break
    case "$ch" in
      o) git checkout --ours   -- "$f" && git add -- "$f" && ok "  kept ours, marked resolved";   break;;
      t) git checkout --theirs -- "$f" && git add -- "$f" && ok "  kept theirs, marked resolved"; break;;
      e) "${EDITOR:-vi}" "$f"; confirm "  mark resolved (git add)?" && { git add -- "$f"; ok "  marked resolved"; }; break;;
      d) git diff -- "$f" | sed -n '1,60p';;
      s) say "  skipped"; break;;
      *) say "  pick o / t / e / d / s";;
    esac
  done
done

say ""
remaining="$(git diff --name-only --diff-filter=U | wc -l | tr -d ' ')"
if [[ "$remaining" == "0" ]]; then
  ok "All conflicts marked resolved. Finish with:  git $op --continue"
else
  warn "$remaining file(s) still conflicted. Re-run when ready."
fi
