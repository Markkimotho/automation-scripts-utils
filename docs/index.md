# Bash Automation Scripts & Utils

Small, reusable Bash scripts for the day-to-day git/GitHub and dev-environment
chores — the kind you keep re-typing by hand.

Every script:

- is **self-contained** and has `--help`,
- **confirms** before anything outward-facing or destructive,
- runs **non-interactively** for CI (`ASSUME_YES=1` or `-y`),
- works on **stock macOS bash 3.2** and Linux.

## Install

```bash
git clone https://github.com/Markkimotho/bash-automation-scripts-utils.git
export PATH="$PWD/bash-automation-scripts-utils/bin:$PATH"   # add to ~/.zshrc to persist
```

Requirements: `bash`, `git`. The `gh-*` scripts need the
[GitHub CLI](https://cli.github.com/) (`gh auth login`); `port-kill.sh` needs `lsof`.

## The scripts

| Script | What it does |
|--------|--------------|
| `gh-merge-pr.sh` | Merge a PR from the CLI — polls mergeability, refuses conflicting PRs, confirms first. |
| `gh-create-repo.sh` | Create a GitHub repo and optionally init/commit/push a local dir. |
| `gh-enable-pages.sh` | Enable GitHub Pages via the API (Actions or branch source). |
| `git-conflict-helper.sh` | Rule-based guide to git conflicts: explains the likely cause and walks resolution. |
| `git-safe-checkout.sh` | Switch branches without silently losing uncommitted work. |
| `py-venv-rebuild.sh` | Rebuild a virtualenv whose interpreter went stale; reinstall requirements. |
| `port-kill.sh` | Kill the process *listening* on a TCP port (not a client connected to it). |

See the [script reference](reference.md) for full options and examples, and
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
