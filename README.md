# automation scripts & utils

Reusable automation for the everyday tasks developers repeat — creating, renaming,
and merging repos, untangling git conflicts, rebuilding environments, freeing
ports, and more. Not limited to git or environment chores: anything worth never
typing by hand twice belongs here. Bash today, **Python utilities planned**.

Every script is self-contained, has `--help`, confirms before anything
outward-facing or destructive, runs non-interactively (`ASSUME_YES=1`) for CI,
and works on stock macOS bash 3.2.

## Scripts

| Script | What it does |
|--------|--------------|
| [`bin/gh-merge-pr.sh`](bin/gh-merge-pr.sh) | Merge a PR from the CLI — polls mergeability, refuses conflicting PRs, confirms first. |
| [`bin/gh-create-repo.sh`](bin/gh-create-repo.sh) | Create a GitHub repo and optionally init/commit/push a local dir to it. |
| [`bin/gh-rename-repo.sh`](bin/gh-rename-repo.sh) | Rename a GitHub repo and update the local `origin` remote. |
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
git clone https://github.com/Markkimotho/automation-scripts-utils.git
export PATH="$PWD/automation-scripts-utils/bin:$PATH"   # add to ~/.zshrc to persist
```

Prerequisites per script — and the dev-environment edge cases worth knowing — are
documented in [`docs/prerequisites.md`](docs/prerequisites.md). In short: `bash` +
`git`; the `gh-*` scripts need the [GitHub CLI](https://cli.github.com/)
(`gh auth login`); `port-kill.sh` needs `lsof`; `py-venv-rebuild.sh` needs `python3`.

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
