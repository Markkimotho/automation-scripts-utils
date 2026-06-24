# Script reference

All scripts self-document with `--help`. Examples assume `bin/` is on your `PATH`.
Bash scripts run on macOS bash 3.2+; Python scripts need `python3`.

---

## Git & GitHub

### `gh-merge-pr.sh`

Merge a PR safely: polls mergeability, refuses `CONFLICTING`, confirms first.

```text
gh-merge-pr.sh <pr-number> [-m merge|squash|rebase] [-d] [-r owner/name] [-y]
```

### `gh-create-repo.sh`

Create a repo and optionally init/commit/push a local dir.

```text
gh-create-repo.sh <name> [--public|--private] [-d desc] [-s dir] [-p] [-y]
```

### `gh-rename-repo.sh`

Rename a repo and rewrite the local `origin`.

```text
gh-rename-repo.sh <new-name> [-r owner/name] [--no-remote-update] [-y]
```

### `gh-enable-pages.sh`

Enable GitHub Pages via the API (Actions or branch source). Repo owner.

```text
gh-enable-pages.sh [owner/name] [--workflow | --branch <b> --path </>] [-y]
```

### `gh-pr-open.sh`

Push the current branch and open a PR in one step.

```text
gh-pr-open.sh [-t title] [-b base] [-d] [-w] [-y]
```

### `gh-pr-status.py`

One table of every open PR with CI / review / mergeable state.

```text
gh-pr-status.py [-r owner/name] [-a @me]
```

### `gh-release.py`

Bump version, build a changelog from commits since the last tag, tag, and release.

```text
gh-release.py [major|minor|patch] [--set X.Y.Z] [-n]
```

### `git-conflict-helper.sh`

Rule-based guide to merge/rebase conflicts. See [Resolving conflicts](conflicts.md).

```text
git-conflict-helper.sh [--check]
```

### `git-safe-checkout.sh`

Switch branches without silently losing uncommitted work.

```text
git-safe-checkout.sh <branch> [-b] [--check] [-y]
```

### `git-clean-branches.sh`

Delete branches already merged into the base (local, and `--remote`).

```text
git-clean-branches.sh [-b base] [--remote] [-n] [-y]
```

### `git-sync.sh`

Catch up: fetch, fast-forward base, prune, rebase current branch. Refuses a dirty tree.

```text
git-sync.sh [-b base] [--no-rebase] [-y]
```

---

## Dev environment

### `dev-doctor.sh`

Report which required tools are present, with install hints. Non-zero if a core tool is missing.

```text
dev-doctor.sh
```

### `proj-bootstrap.sh`

Scaffold a new project: git, ignore, README, pre-commit, CI, optional license.

```text
proj-bootstrap.sh [dir] [--name n] [--flavor python|node|generic] [--license mit|none] [--no-git] [-y]
```

### `precommit-install.sh`

Install (and optionally scaffold) pre-commit hooks; offers to pip-install pre-commit.

```text
precommit-install.sh [--with-config] [-y]
```

### `py-venv-rebuild.sh`

Rebuild a virtualenv whose interpreter went stale; reinstall requirements.

```text
py-venv-rebuild.sh [--python bin|version] [--venv dir] [-r requirements.txt] [-y]
```

### `py-check.sh`

Run ruff + mypy + pytest (+ coverage) in one pass; skips missing tools.

```text
py-check.sh [path] [--no-cov]
```

---

## Cross-language dependency & library tooling

Python-powered, **polyglot**: each detects the manifests present
(`requirements.txt`/`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`,
`Gemfile`, `pom.xml`) and acts on all of them. Toolchains that aren't installed
are skipped with a note rather than failing.

### `deps-outdated.py`

Outdated packages across pip / npm / cargo / go, one table.

```text
deps-outdated.py [--root .]
```

### `deps-unused.py`

Declared-but-never-imported dependencies (Python + Node, heuristic).

```text
deps-unused.py [--root .] [--warn-only]
```

### `lockfile-drift.py`

Flag manifests whose lockfile is missing or older than the manifest.

```text
lockfile-drift.py [--root .]
```

### `vuln-scan.py`

Run each ecosystem's audit tool (pip-audit/npm audit/cargo audit/govulncheck) and normalize.

```text
vuln-scan.py [--root .] [--warn-only]
```

### `lic-audit.py`

Collect dependency licenses; flag GPL/AGPL/LGPL and unknown.

```text
lic-audit.py [--root .] [--strict]
```

### `version-bump.py`

Bump the project version in whatever manifest(s) the repo uses, atomically.

```text
version-bump.py [major|minor|patch] [--set X.Y.Z] [--root .] [-n]
```

### `env-check.py`

Diff `.env` against `.env.example`; report missing/extra keys. Language-agnostic.

```text
env-check.py [--env .env] [--example .env.example] [--strict]
```

---

## Data & housekeeping

### `data-convert.py`

Convert between CSV, JSON, and YAML (YAML needs PyYAML).

```text
data-convert.py <input|-> --to csv|json|yaml [--from fmt] [-o out]
```

### `clean-artifacts.sh`

Delete build/cache junk (`__pycache__`, `dist`, caches, `.DS_Store`, …). Dry-run by default.

```text
clean-artifacts.sh [dir] [--apply] [--node] [-y]
```

### `secret-scan.py`

Scan staged files (or given paths) for likely secrets; exits non-zero on a hit.

```text
secret-scan.py [paths...] [--all] [--root .]
```

### `snapshot.sh`

Timestamped `tar.gz` of a directory before a risky operation.

```text
snapshot.sh [dir] [-o out-dir]
```

### `port-kill.sh`

Kill the process **listening** on a TCP port (not a client connected to it).

```text
port-kill.sh <port> [port...] [--all] [-9] [-y]
```
