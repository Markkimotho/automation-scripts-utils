# Resolving conflicts

`git-conflict-helper.sh` is a guided walkthrough, not a magic resolver. It tells
you **why** a conflict probably happened and walks you through fixing it safely.

## What it does

1. Confirms you're in a git repo and reports the operation in progress
   (**merge**, **rebase**, or **cherry-pick**).
2. Lists every conflicted file with its conflict-marker count.
3. Walks the common **causes**, in order, and asks the key question: *did you
   commit or stash before you switched/pulled?*
4. Offers safe per-file actions: keep **ours**, keep **theirs**, edit by hand,
   show the diff, or skip.

```bash
git-conflict-helper.sh          # interactive
git-conflict-helper.sh --check  # report only: exit 0 clean, 2 conflicts
```

## The rule set

The guide reasons through these causes in order:

### 1. Same lines edited on both sides
Both branches changed the same lines. This is the normal case — pick a winner or
combine the two.

### 2. You didn't commit/stash before switching or pulling
Uncommitted edits collide with incoming changes. The fix going forward is a
habit: commit or stash **before** `checkout` / `pull` / `merge`. That's exactly
what [`git-safe-checkout.sh`](reference.md#git-safe-checkoutsh) enforces.

### 3. Your branch is stale (behind the base)
The base moved on while you worked. Re-sync:

```bash
git fetch origin
git merge origin/<base>      # or: git rebase origin/<base>
```

### 4. Edit-vs-delete, or a rename
A file was deleted/renamed on one side and edited on the other. git can't
auto-merge that — decide whether to keep or remove it.

### 5. Whitespace / line-ending churn (CRLF vs LF)
Whole-file conflicts with no real change usually mean line-ending drift:

```bash
git diff --check        # flags whitespace/EOL problems
git config core.autocrlf   # review the setting
```

## Escape hatches

If you're in over your head, backing out is always safe:

```bash
git merge --abort        # or rebase --abort / cherry-pick --abort
```

Then re-do the operation from a clean, committed state.

## Marking a file resolved

After editing a conflicted file to remove the `<<<<<<<`, `=======`, `>>>>>>>`
markers:

```bash
git add <file>           # marks it resolved
git merge --continue     # or rebase --continue
```

The helper does the `git add` for you when you pick ours/theirs or confirm after
editing.
