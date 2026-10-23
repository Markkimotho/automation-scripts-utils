# Automation Scripts & Utils

A community-driven, multi-language toolkit for practical tasks across developer workflows, operating systems, cloud, AI/ML, business, files, networking, security, media and personal productivity.

**Implemented:** 49 real catalog entries across 16 categories. **Roadmap:** at least 1,200 verified scripts (the requested category targets sum to 1,280); the long-term design can support 5,000–10,000. Roadmap counts are not implemented counts.

## Get started

```bash
git clone https://github.com/Markkimotho/automation-scripts-utils.git
cd automation-scripts-utils
export PATH="$PWD/cli:$PATH"
automation list
automation search "git"
automation list --category security-compliance
automation info git-conflict-helper
automation run git-conflict-helper --dry-run
automation run git-conflict-helper -- --help
```

The CLI uses Python 3.10+ and only the standard library. Individual scripts require their own documented runtimes and external dependencies.

## Explore the library

- [CLI guide and catalog](cli.md) — search, filtering, parameter checking and safe execution
- [Script reference](reference.md) — original 34 scripts and their CLI arguments
- [Architecture](architecture.md) — domain folders, shared helpers and tests
- [Prerequisites](prerequisites.md) — OS compatibility and dependency setup
- [Migration](migration.md) — replacement paths for the previous `bin/` layout
- [Roadmap](roadmap.md) — 16 categories, phased targets and quality requirements
- [Contributing](contributing.md) — metadata, tests and pull request guidance
- [Resolving conflicts](conflicts.md) — Git conflict handling rules

The searchable catalog is in `catalog/scripts.json`. A script folder includes a runnable implementation, `metadata.yaml`, and its own `README.md`. Use `automation info <id>` for exact entrypoint, supported platforms and declared permissions.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
bash tests/run_tests.sh
```

CI checks Python and Bash syntax, catalog integrity, offline behavior, the legacy regression suite, and strict MkDocs site builds. Browser and cloud operations require external test environments for end-to-end validation.
