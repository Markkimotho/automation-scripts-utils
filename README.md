# bash automation scripts & utils

Small, reusable Bash scripts for the day-to-day git/GitHub and dev-environment
chores — the kind you keep re-typing by hand. Every script is self-contained,
has `--help`, confirms before anything outward-facing or destructive, and works
non-interactively (`ASSUME_YES=1`) for CI.

## Scripts

| Script | What it does |
|--------|--------------|
| [`bin/gh-merge-pr.sh`](bin/gh-merge-pr.sh) | Merge a PR from the CLI — polls mergeability, refuses conflicting PRs, confirms first. |
| [`bin/gh-create-repo.sh`](bin/gh-create-repo.sh) | Create a GitHub repo and optionally init/commit/push a local dir to it. |
| [`bin/gh-enable-pages.sh`](bin/gh-enable-pages.sh) | Enable GitHub Pages via the API (Actions or branch source) — repo owner. |
| [`bin/git-conflict-helper.sh`](bin/git-conflict-helper.sh) | Rule-based guide to git conflicts: explains the likely cause and walks resolution. |
| [`bin/git-safe-checkout.sh`](bin/git-safe-checkout.sh) | Switch branches without silently losing uncommitted work. |
| [`bin/py-venv-rebuild.sh`](bin/py-venv-rebuild.sh) | Rebuild a virtualenv whose interpreter went stale; reinstall requirements. |
| [`bin/port-kill.sh`](bin/port-kill.sh) | Kill the process *listening* on a TCP port (not a client connected to it). |

[`lib/common.sh`](lib/common.sh) holds the shared helpers (logging, `confirm`,
`require_cmd`, git/gh checks).

## Install

Clone and put `bin/` on your `PATH`:

```bash
git clone https://github.com/<you>/bash-automation-scripts-utils.git
export PATH="$PWD/bash-automation-scripts-utils/bin:$PATH"   # add to ~/.zshrc to persist
```

Requirements: `bash`, `git`. The `gh-*` scripts need the [GitHub CLI](https://cli.github.com/)
(`gh auth login`); `port-kill.sh` needs `lsof`.

## Usage

Every script self-documents:

```bash
gh-merge-pr.sh --help
git-conflict-helper.sh        # interactive guide
git-safe-checkout.sh feature -b
port-kill.sh 8080 8090 -y
```

## Conventions

- `--help` on every script.
- Confirmation prompt before merging, pushing, deleting, or killing. Set
  `ASSUME_YES=1` (or `-y`) to skip in automation.
- `NO_COLOR=1` disables color.
- `set -euo pipefail` throughout.

## Tests

```bash
bash tests/run_tests.sh
```

Gate tests are deterministic and offline: shared helpers, conflict detection,
and dirty-tree detection run against throwaway git repos. Outward-facing `gh`
calls aren't exercised here.

## Docs

A documentation site is built from `docs/` with MkDocs Material and published to
GitHub Pages by [`.github/workflows/docs.yml`](.github/workflows/docs.yml).
Preview locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```
