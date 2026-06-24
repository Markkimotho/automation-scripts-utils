# automation scripts & utils

Reusable automation for the everyday tasks developers repeat — creating, renaming,
and merging repos, untangling git conflicts, rebuilding environments, freeing
ports, and more. Not limited to git or environment chores: anything worth never
typing by hand twice belongs here. Bash today, **Python utilities planned**.

Every script is self-contained, has `--help`, confirms before anything
outward-facing or destructive, runs non-interactively (`ASSUME_YES=1`) for CI,
and works on stock macOS bash 3.2.

## Scripts

28 scripts across four areas. Full options and examples are in the
[script reference](docs/reference.md); per-script prerequisites in
[docs/prerequisites.md](docs/prerequisites.md).

**Git & GitHub** — `gh-merge-pr`, `gh-create-repo`, `gh-rename-repo`,
`gh-enable-pages`, `gh-pr-open`, `gh-pr-status.py`, `gh-release.py`,
`git-conflict-helper`, `git-safe-checkout`, `git-clean-branches`, `git-sync`.

**Dev environment** — `dev-doctor`, `proj-bootstrap`, `precommit-install`,
`py-venv-rebuild`, `py-check`.

**Cross-language dependency & library tooling** (Python, polyglot — handle pip,
npm, cargo, go, bundler in one run) — `deps-outdated.py`, `deps-unused.py`,
`lockfile-drift.py`, `vuln-scan.py`, `lic-audit.py`, `version-bump.py`,
`env-check.py`.

**Data & housekeeping** — `data-convert.py`, `clean-artifacts`, `secret-scan.py`,
`snapshot`, `port-kill`.

Shared helpers live in [`lib/common.sh`](lib/common.sh) (bash) and
[`lib/common.py`](lib/common.py) (Python): logging, `confirm`, dependency checks,
and manifest detection for the polyglot tools.

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
