# Prerequisites

What each script needs before it will run, how to install it, and the edge cases
that bite when setting up a dev environment.

## Per-script requirements

Every script needs **`bash` (3.2+, the macOS default is fine)**. Beyond that:

| Script | Mandatory | Notes |
|--------|-----------|-------|
| `gh-merge-pr.sh` | `gh` (authenticated), `git`, `jq` | `gh` must be logged in; `jq` parses the API JSON. |
| `gh-create-repo.sh` | `gh` (authenticated), `git` | — |
| `gh-enable-pages.sh` | `gh` (authenticated) | Token needs the **`repo`** scope (and you must own the repo). |
| `gh-rename-repo.sh` | `gh` (authenticated), `git` | `git` only used to rewrite `origin`. |
| `git-conflict-helper.sh` | `git` | — |
| `git-safe-checkout.sh` | `git` | — |
| `py-venv-rebuild.sh` | `python3` | `pyenv` optional (used to resolve a version like `3.12.4`). |
| `port-kill.sh` | `lsof` | Present on macOS by default; install on minimal Linux. |

Scripts fail fast with a clear message (`Required command not found: …`) when a
prerequisite is missing — they won't half-run.

## Install the prerequisites

=== "macOS (Homebrew)"

    ```bash
    brew install gh git jq        # lsof and python3 ship with macOS
    # newer bash only if you write bash 4+ features (scripts here don't need it):
    brew install bash
    ```

=== "Debian / Ubuntu"

    ```bash
    sudo apt-get update
    sudo apt-get install -y git jq lsof python3 python3-venv
    # GitHub CLI:
    sudo apt-get install -y gh   # or follow https://cli.github.com for the latest
    ```

## Set up the GitHub CLI

The `gh-*` scripts assume `gh` is installed **and authenticated**:

```bash
gh auth login            # interactive: pick GitHub.com, HTTPS or SSH, a browser login
gh auth status           # verify — every gh-* script runs this check internally
```

For **`gh-enable-pages.sh`** the token must carry the `repo` scope. If you hit a
`404`/permission error enabling Pages, refresh the scopes:

```bash
gh auth refresh -h github.com -s repo
```

## Edge cases when setting up a dev environment

These are the ones that actually cost time:

!!! warning "macOS ships bash 3.2"
    `/bin/bash` on macOS is from 2007 and lacks `mapfile`, associative arrays,
    and `${var,,}`. These scripts are written to run on it. If *you* add bash 4+
    features, `brew install bash` and use `#!/usr/bin/env bash` (Homebrew bash
    lands on `PATH` ahead of `/bin/bash`).

!!! warning "A virtualenv can outlive its interpreter"
    If you built `.venv` with a `pyenv`/conda Python that was later removed or
    moved, `.venv/bin/python` becomes a dangling symlink and *every* command
    fails cryptically. Fix: `py-venv-rebuild.sh --python 3.12.4`.

!!! warning "`gh` not authenticated, wrong account, or missing scopes"
    `gh auth status` tells you who you are and which scopes you hold. Enabling
    Pages needs `repo`; a fresh `gh auth login` via browser usually grants it,
    older tokens may not — `gh auth refresh -s repo`.

!!! warning "git identity unset breaks commits (especially in CI)"
    Without `user.name`/`user.email`, `git commit` aborts. Set them once:
    ```bash
    git config --global user.name  "Your Name"
    git config --global user.email "you@example.com"
    ```

!!! warning "`bin/` not on PATH, or scripts not executable"
    Either add `bin/` to `PATH` (see [Home](index.md#install)) or run a script
    explicitly: `bash bin/port-kill.sh 8080`. After `git clone`, `chmod +x bin/*.sh`
    if the execute bit didn't survive.

!!! warning "Killing a port hits the wrong process"
    `lsof -i:PORT` matches both listeners *and* clients connected to that port.
    `port-kill.sh` targets **listeners only** by default for exactly this reason.
    Use `--all` only when you mean it.

!!! warning "GitHub Pages must be enabled before a deploy can publish"
    The build job succeeds but `deploy` 404s until Pages is on. Enable it with
    `gh-enable-pages.sh` or in repo **Settings → Pages → Source = GitHub Actions**.
    Also: `actions/setup-python` with `cache: pip` needs a requirements file to
    key on — set `cache-dependency-path` if yours isn't named `requirements.txt`.

!!! warning "Line endings (CRLF vs LF) cause phantom conflicts"
    Whole-file diffs with no visible change usually mean line-ending drift.
    Check with `git diff --check` and review `git config core.autocrlf`.

!!! warning "Non-interactive shells refuse confirmation prompts"
    In CI or piped contexts there's no TTY, so `confirm` declines by default to
    avoid acting blindly. Pass `-y` or set `ASSUME_YES=1` to proceed.
