# Script reference

All examples assume `bin/` is on your `PATH`.

---

## `gh-merge-pr.sh`

Merge a GitHub PR from the CLI, safely.

```text
gh-merge-pr.sh <pr-number> [options]

  -m, --method <merge|squash|rebase>   Merge method (default: squash)
  -d, --delete-branch                  Delete the head branch after merge
  -r, --repo <owner/name>              Target repo (default: current)
  -y, --yes                            Skip confirmation
```

- Verifies `gh` auth and polls the PR's mergeable state (~30s).
- **Refuses** to merge a `CONFLICTING` PR — run `git-conflict-helper.sh` first.
- Confirms before merging (outward-facing).

```bash
gh-merge-pr.sh 12 --squash --delete-branch
gh-merge-pr.sh 7 -m merge -r owner/repo -y
```

---

## `gh-create-repo.sh`

Create a GitHub repo and optionally push a local dir to it.

```text
gh-create-repo.sh <name> [options]

  --public | --private        Visibility (default: private)
  -d, --description <text>     Repo description
  -s, --source <dir>           Local dir to push (default: current dir)
  -p, --push                   Init/commit/push the source dir
  -b, --branch <name>          Default branch when initializing (default: main)
  -y, --yes                    Skip confirmation
```

```bash
gh-create-repo.sh my-tool --public -d "Handy tool" --source . --push
gh-create-repo.sh private-notes              # empty private repo
```

---

## `gh-rename-repo.sh`

Rename a GitHub repo and update the local `origin` remote.

```text
gh-rename-repo.sh <new-name> [options]

  -r, --repo <owner/name>     Repo to rename (default: current repo)
  --no-remote-update          Don't rewrite the local 'origin' URL
  -y, --yes                   Skip confirmation
```

GitHub keeps a redirect from the old name, but `origin` is rewritten so the next
push just works. A repo with Pages keeps Pages, but the project-site URL changes
to the new name — update `site_url`/links and redeploy.

```bash
gh-rename-repo.sh new-name
gh-rename-repo.sh new-name -r owner/old-name --yes
```

---

## `gh-enable-pages.sh`

Enable GitHub Pages via the API. Requires repo-owner access and a `gh` token
with the `repo`/Pages scope.

```text
gh-enable-pages.sh [owner/name] [options]

  --workflow              Source = GitHub Actions (default).
  --branch <branch>       Source = a branch (classic), e.g. gh-pages.
  --path </ or /docs>     Path for branch source (default: /).
  -y, --yes               Skip confirmation
```

- No repo argument → uses the current repo.
- If Pages already exists, its build type is updated instead of failing.

```bash
gh-enable-pages.sh                           # current repo, Actions source
gh-enable-pages.sh owner/site --branch gh-pages
```

---

## `git-conflict-helper.sh`

Rule-based guide for git merge/rebase/cherry-pick conflicts. See
[Resolving conflicts](conflicts.md) for the full rule set.

```text
git-conflict-helper.sh [--check]

  --check    Non-interactive. Report state + conflicted files only.
             Exit 0 = clean, 2 = conflicts present.
```

```bash
git-conflict-helper.sh            # interactive guide
git-conflict-helper.sh --check    # for scripts/CI
```

---

## `git-safe-checkout.sh`

Switch branches without silently losing uncommitted work.

```text
git-safe-checkout.sh <branch> [options]

  -b, --create     Create the branch (git checkout -b)
  --check          Report dirty state only. Exit 0 = clean, 2 = dirty.
  -y, --yes        Assume "stash" for the dirty prompt (non-interactive)
```

When the tree is dirty it shows what's dirty and asks you to **commit / stash /
discard / abort** before switching.

```bash
git-safe-checkout.sh feature -b
git-safe-checkout.sh main
```

---

## `py-venv-rebuild.sh`

Rebuild a virtualenv whose interpreter went stale (the base Python moved or was
removed, so `.venv/bin/python` is a dangling symlink).

```text
py-venv-rebuild.sh [options]

  --python <bin|version>   Interpreter: a path, or a version like 3.12.4
                           (resolved via pyenv, then pythonX.Y, python3)
  --venv <dir>             Venv directory (default: .venv)
  -r, --requirements <f>   Requirements file (default: requirements.txt if present)
  -y, --yes                Skip the delete confirmation
```

```bash
py-venv-rebuild.sh --python 3.12.4
py-venv-rebuild.sh --venv .venv -r requirements.txt -y
```

---

## `port-kill.sh`

Kill the process **listening** on one or more TCP ports. By default it targets
only listeners — so it won't kill a process that merely holds an *outbound*
connection to that port (a common, painful mistake).

```text
port-kill.sh <port> [port...] [options]

  --all        Match ANY socket on the port, not just listeners.
  -9, --force  Use SIGKILL instead of SIGTERM.
  -y, --yes    Skip confirmation.
```

```bash
port-kill.sh 8080 8090          # free up two listener ports
port-kill.sh 6380 --force -y
```
