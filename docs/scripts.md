# Script directory

Browse available automations. [Install](install.md) the command and use `automation info SCRIPT-ID` to inspect permissions and requirements.

## Ai Ml Llmops

### `csv-dataset-profile`

Profile a CSV dataset by counting rows and missing values per column without exposing data values.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info csv-dataset-profile
automation run csv-dataset-profile --dry-run
automation run csv-dataset-profile -- --help
```

## Api Integrations

### `http-status-check`

Check HTTP response status and elapsed time for one URL with a configurable timeout.

**Language:** javascript · **Platforms:** linux, macos, windows · **Permissions:** network-read

```bash
automation info http-status-check
automation run http-status-check --dry-run
automation run http-status-check -- --help
```

## Backup Recovery

### `incremental-file-copy`

Preview and optionally copy changed regular files to a separate backup directory without deleting old backups.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-write

```bash
automation info incremental-file-copy
automation run incremental-file-copy --dry-run
automation run incremental-file-copy -- --help
```

### `snapshot`

Timestamped `tar.gz` of a directory before a risky operation.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info snapshot
automation run snapshot --dry-run
automation run snapshot -- --help
```

## Business Productivity

### `invoice-due-report`

Summarize unpaid invoices from a CSV with invoice_id, due_date, amount and paid columns.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info invoice-due-report
automation run invoice-due-report --dry-run
automation run invoice-due-report -- --help
```

## Cloud Devops

### `s3-bucket-audit`

Read-only AWS S3 inventory of bucket-level public access block and default encryption settings.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** cloud-read

```bash
automation info s3-bucket-audit
automation run s3-bucket-audit --dry-run
automation run s3-bucket-audit -- --help
```

### `terraform-workspaces`

List local Terraform workspaces for the selected project directory without changing state.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info terraform-workspaces
automation run terraform-workspaces --dry-run
automation run terraform-workspaces -- --help
```

## Data Engineering

### `data-convert`

Convert between CSV, JSON, and YAML (YAML needs PyYAML).

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info data-convert
automation run data-convert --dry-run
automation run data-convert -- --help
```

## Desktop Personal

### `organize-downloads`

Preview and optionally sort top-level files into extension-named folders without overwriting existing files.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-write

```bash
automation info organize-downloads
automation run organize-downloads --dry-run
automation run organize-downloads -- --help
```

## Developer Tools

### `deps-outdated`

Outdated packages across pip / npm / cargo / go, one table.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info deps-outdated
automation run deps-outdated --dry-run
automation run deps-outdated -- --help
```

### `deps-unused`

Declared-but-never-imported dependencies (Python + Node, heuristic).

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info deps-unused
automation run deps-unused --dry-run
automation run deps-unused -- --help
```

### `dev-doctor`

Report which required tools are present, with install hints. Non-zero if a core tool is missing.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info dev-doctor
automation run dev-doctor --dry-run
automation run dev-doctor -- --help
```

### `env-check`

Diff `.env` against `.env.example`; report missing/extra keys. Language-agnostic.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info env-check
automation run env-check --dry-run
automation run env-check -- --help
```

### `gh-create-repo`

Create a repo and optionally init/commit/push a local dir.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-create-repo
automation run gh-create-repo --dry-run
automation run gh-create-repo -- --help
```

### `gh-enable-pages`

Enable GitHub Pages via the API (Actions or branch source). Repo owner.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-enable-pages
automation run gh-enable-pages --dry-run
automation run gh-enable-pages -- --help
```

### `gh-issues-sync`

Create issues from a JSON list of `{title, body, labels}`. Missing labels are created first (priority `P1`-`P3`, `area:*` and type labels get consistent colors); an issue whose title already exists, open or closed, is skipped, so re-runs never duplicate. Preview by default (exit 2 when there is something to create).

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-write

```bash
automation info gh-issues-sync
automation run gh-issues-sync --dry-run
automation run gh-issues-sync -- --help
```

### `gh-merge-pr`

Merge a PR safely: polls mergeability, refuses `CONFLICTING`, confirms first.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-merge-pr
automation run gh-merge-pr --dry-run
automation run gh-merge-pr -- --help
```

### `gh-org-ci`

Latest GitHub Actions runs for every repo of an org (or `--repos`), one table, with the URL of each failed run. `--wait` polls until nothing is running; exit code 2 when any shown run failed.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info gh-org-ci
automation run gh-org-ci --dry-run
automation run gh-org-ci -- --help
```

### `gh-org-clone`

Clone every repo of an org into one directory; `--pull` fast-forwards existing clones (dirty ones are skipped, never reset).

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info gh-org-clone
automation run gh-org-clone --dry-run
automation run gh-org-clone -- --help
```

### `gh-pr-open`

Push the current branch and open a PR in one step.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-pr-open
automation run gh-pr-open --dry-run
automation run gh-pr-open -- --help
```

### `gh-pr-status`

One table of every open PR with CI / review / mergeable state.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info gh-pr-status
automation run gh-pr-status --dry-run
automation run gh-pr-status -- --help
```

### `gh-release`

Bump version, build a changelog from commits since the last tag, tag, and release.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-write

```bash
automation info gh-release
automation run gh-release --dry-run
automation run gh-release -- --help
```

### `gh-rename-org`

Rename an organization. Checks you own it and the new name is free, opens the settings page (github.com has no rename API), waits until GitHub serves the new name, repoints remotes under `--scan-dir`, and lists files still naming the old org.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-rename-org
automation run gh-rename-org --dry-run
automation run gh-rename-org -- --help
```

### `gh-rename-repo`

Rename a repo and rewrite the local `origin`.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info gh-rename-repo
automation run gh-rename-repo --dry-run
automation run gh-rename-repo -- --help
```

### `git-clean-branches`

Delete branches already merged into the base (local, and `--remote`).

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info git-clean-branches
automation run git-clean-branches --dry-run
automation run git-clean-branches -- --help
```

### `git-conflict-helper`

Rule-based guide to merge/rebase conflicts. See [Resolving conflicts](conflicts.md).

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info git-conflict-helper
automation run git-conflict-helper --dry-run
automation run git-conflict-helper -- --help
```

### `git-replace`

Replace a literal string in every tracked text file. Preview by default (exit 2 when matches exist), `--apply` to write; pathspecs include or exclude files.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info git-replace
automation run git-replace --dry-run
automation run git-replace -- --help
```

### `git-safe-checkout`

Switch branches without silently losing uncommitted work.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info git-safe-checkout
automation run git-safe-checkout --dry-run
automation run git-safe-checkout -- --help
```

### `git-split-repo`

Extract files or directories into a new repo, keeping their commit history (via `git-filter-repo`). Paths can be moved, including to the root; the source repo is never modified. `--publish` creates the GitHub repo and pushes.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info git-split-repo
automation run git-split-repo --dry-run
automation run git-split-repo -- --help
```

### `git-sync`

Catch up: fetch, fast-forward base, prune, rebase current branch. Refuses a dirty tree.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info git-sync
automation run git-sync --dry-run
automation run git-sync -- --help
```

### `lic-audit`

Collect dependency licenses; flag GPL/AGPL/LGPL and unknown.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info lic-audit
automation run lic-audit --dry-run
automation run lic-audit -- --help
```

### `lockfile-drift`

Flag manifests whose lockfile is missing or older than the manifest.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info lockfile-drift
automation run lockfile-drift --dry-run
automation run lockfile-drift -- --help
```

### `precommit-install`

Install (and optionally scaffold) pre-commit hooks; offers to pip-install pre-commit.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info precommit-install
automation run precommit-install --dry-run
automation run precommit-install -- --help
```

### `proj-bootstrap`

Scaffold a new project: git, ignore, README, pre-commit, CI, optional license.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info proj-bootstrap
automation run proj-bootstrap --dry-run
automation run proj-bootstrap -- --help
```

### `py-check`

Run ruff + mypy + pytest (+ coverage) in one pass; skips missing tools.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-read

```bash
automation info py-check
automation run py-check --dry-run
automation run py-check -- --help
```

### `py-venv-rebuild`

Rebuild a virtualenv whose interpreter went stale; reinstall requirements.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info py-venv-rebuild
automation run py-venv-rebuild --dry-run
automation run py-venv-rebuild -- --help
```

### `version-bump`

Bump the project version in whatever manifest(s) the repo uses, atomically.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-write

```bash
automation info version-bump
automation run version-bump --dry-run
automation run version-bump -- --help
```

## Files Documents

### `folder-inventory`

Inventory regular files recursively with size and modification timestamps, exporting structured JSON or CSV.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info folder-inventory
automation run folder-inventory --dry-run
automation run folder-inventory -- --help
```

### `json-property-select`

Select a named top-level property from a JSON object using Node.js TypeScript stripping.

**Language:** typescript · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info json-property-select
automation run json-property-select --dry-run
automation run json-property-select -- --help
```

## Media Processing

### `image-checksum-manifest`

Recursively create a SHA-256 checksum manifest of image files for later integrity comparison.

**Language:** ruby · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info image-checksum-manifest
automation run image-checksum-manifest --dry-run
automation run image-checksum-manifest -- --help
```

## Messaging Notifications

### `eml-headers-report`

Extract email headers from local .eml files without accessing an inbox or sending messages.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info eml-headers-report
automation run eml-headers-report --dry-run
automation run eml-headers-report -- --help
```

## Networking Monitoring

### `tcp-connect-check`

Attempt one TCP connection to a specified host and port and return reachable status and latency.

**Language:** go · **Platforms:** linux, macos, windows · **Permissions:** network-read

```bash
automation info tcp-connect-check
automation run tcp-connect-check --dry-run
automation run tcp-connect-check -- --help
```

## Security Compliance

### `file-permission-audit`

Find world-writable regular files under a directory without following symlinks.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info file-permission-audit
automation run file-permission-audit --dry-run
automation run file-permission-audit -- --help
```

### `secret-scan`

Scan staged files (or given paths) for likely secrets; exits non-zero on a hit.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info secret-scan
automation run secret-scan --dry-run
automation run secret-scan -- --help
```

### `vuln-scan`

Run each ecosystem's audit tool (pip-audit/npm audit/cargo audit/govulncheck) and normalize.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info vuln-scan
automation run vuln-scan --dry-run
automation run vuln-scan -- --help
```

## System Administration

### `clean-artifacts`

Delete build/cache junk (`__pycache__`, `dist`, caches, `.DS_Store`, …). Dry-run by default.

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info clean-artifacts
automation run clean-artifacts --dry-run
automation run clean-artifacts -- --help
```

### `port-kill`

Kill the process **listening** on a TCP port (not a client connected to it).

**Language:** bash · **Platforms:** linux, macos · **Permissions:** filesystem-write

```bash
automation info port-kill
automation run port-kill --dry-run
automation run port-kill -- --help
```

### `windows-services-report`

Read Windows service names, display names and statuses, optionally filtered by service name.

**Language:** powershell · **Platforms:** windows · **Permissions:** filesystem-read

```bash
automation info windows-services-report
automation run windows-services-report --dry-run
automation run windows-services-report -- --help
```

## Testing Qa

### `json-batch-validate`

Validate JSON syntax for a file or folder recursively and report the filename and parse errors.

**Language:** python · **Platforms:** linux, macos, windows · **Permissions:** filesystem-read

```bash
automation info json-batch-validate
automation run json-batch-validate --dry-run
automation run json-batch-validate -- --help
```

## Web Browser

### `page-link-export`

Visit a user-supplied webpage using Playwright and export its visible anchor links as JSON.

**Language:** javascript · **Platforms:** linux, macos, windows · **Permissions:** network-read

```bash
automation info page-link-export
automation run page-link-export --dry-run
automation run page-link-export -- --help
```

