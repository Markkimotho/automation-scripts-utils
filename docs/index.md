# Automation Scripts & Utils

Reusable automation for the everyday tasks developers repeat — creating and
merging repos, untangling git conflicts, rebuilding environments, freeing ports,
and more. Not limited to git or environment chores: anything worth never typing
by hand twice belongs here. Bash today, **Python utilities planned**.

Every script:

- is **self-contained** and has `--help`,
- **confirms** before anything outward-facing or destructive,
- runs **non-interactively** for CI (`ASSUME_YES=1` or `-y`),
- works on **stock macOS bash 3.2** and Linux.

## Install

```bash
git clone https://github.com/Markkimotho/automation-scripts-utils.git
export PATH="$PWD/automation-scripts-utils/bin:$PATH"   # add to ~/.zshrc to persist
```

See [Prerequisites](prerequisites.md) for exactly what each script needs and the
dev-environment edge cases worth knowing. In short: `bash` + `git`; the `gh-*`
scripts need the [GitHub CLI](https://cli.github.com/) (`gh auth login`);
`port-kill.sh` needs `lsof`; `py-venv-rebuild.sh` needs `python3`.

## The scripts

### Git & GitHub

| Script | What it does |
|--------|--------------|
| `gh-merge-pr.sh` | Merge a PR — polls mergeability, refuses conflicting PRs, confirms. |
| `gh-create-repo.sh` | Create a repo and optionally init/commit/push a local dir. |
| `gh-rename-repo.sh` | Rename a repo and update the local `origin` remote. |
| `gh-enable-pages.sh` | Enable GitHub Pages via the API (Actions or branch source). |
| `gh-pr-open.sh` | Push the current branch and open a PR in one step. |
| `gh-pr-status.py` | One table of every open PR with CI / review / mergeable state. |
| `gh-release.py` | Bump, changelog from commits, tag, GitHub release. |
| `git-conflict-helper.sh` | Rule-based guide to git conflicts. |
| `git-safe-checkout.sh` | Switch branches without losing uncommitted work. |
| `git-clean-branches.sh` | Delete branches already merged into the base. |
| `git-sync.sh` | Fetch, fast-forward base, prune, rebase current branch. |

### Dev environment

| Script | What it does |
|--------|--------------|
| `dev-doctor.sh` | Report missing tools with install hints. |
| `proj-bootstrap.sh` | Scaffold git/ignore/README/pre-commit/CI/license. |
| `precommit-install.sh` | Install (and scaffold) pre-commit hooks. |
| `py-venv-rebuild.sh` | Rebuild a stale virtualenv; reinstall requirements. |
| `py-check.sh` | ruff + mypy + pytest in one pass. |

### Cross-language dependency & library tooling (Python, polyglot)

| Script | What it does |
|--------|--------------|
| `deps-outdated.py` | Outdated packages across pip / npm / cargo / go. |
| `deps-unused.py` | Declared-but-never-imported dependencies. |
| `lockfile-drift.py` | Lockfile missing or older than its manifest. |
| `vuln-scan.py` | Run each ecosystem's audit tool, normalize findings. |
| `lic-audit.py` | Collect licenses; flag copyleft / unknown. |
| `version-bump.py` | Bump the version in whatever manifest(s) exist. |
| `env-check.py` | Diff `.env` against `.env.example`. |

### Data & housekeeping

| Script | What it does |
|--------|--------------|
| `data-convert.py` | CSV ↔ JSON ↔ YAML. |
| `clean-artifacts.sh` | Remove build/cache junk (dry-run default). |
| `secret-scan.py` | Scan staged files for likely secrets. |
| `snapshot.sh` | Timestamped backup before risky ops. |
| `port-kill.sh` | Kill the process *listening* on a TCP port. |

See the [script reference](reference.md) for options and examples, and
[resolving conflicts](conflicts.md) for the conflict-helper's rule set.

## Conventions

- `--help` on every script.
- A confirmation prompt before merging, pushing, deleting, or killing. Set
  `ASSUME_YES=1` (or pass `-y`) to skip it in automation.
- `NO_COLOR=1` disables color.
- `set -euo pipefail` throughout.

## Tests

```bash
bash tests/run_tests.sh
```

Deterministic, offline gate tests: shared helpers, conflict detection, and
dirty-tree detection run against throwaway git repos.
