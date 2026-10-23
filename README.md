# Automation Scripts & Utils

A community-driven, multi-language collection of practical automation for software development, operations, data, business workflows, research, and everyday computing.

**Implemented today:** 49 registered scripts (34 migrated and 15 new implementations) (see [catalog/scripts.json](catalog/scripts.json)). **Growth goal:** at least 1,200 tested scripts (1,280 in the full per-category allocation), with an architecture designed to accommodate 5,000–10,000. These targets are a roadmap, **not** a claim about current inventory.

## Get started

Prerequisites: Python 3.10+ for the catalog CLI; individual scripts declare additional dependencies.

```bash
git clone https://github.com/Markkimotho/automation-scripts-utils.git
cd automation-scripts-utils
export PATH="$PWD/cli:$PATH"
automation list --category developer-tools
automation search "git"
automation info git-sync
automation run git-sync --dry-run
automation run git-sync -- --help
```

Add the PATH export to your shell profile for permanent access. The CLI works with only the Python standard library.

**Safety:** `automation run <id> --dry-run` previews the planned command and does not run the script. Actual runs check declared dependencies and request confirmation for mutating operations. `--yes` explicitly confirms non-interactive execution. Forward script-specific options after `--`.

To invoke a script directly without the CLI:

```bash
bash scripts/developer-tools/git/git-conflict-helper/git-conflict-helper.sh --help
python3 scripts/data-engineering/conversion/data-convert/data-convert.py --help
```

## Structure

```text
.github/workflows/       Continuous integration and documentation publishing
catalog/categories.yaml  16 automation domains and targets
catalog/scripts.json     Real registered scripts (machine-readable)
scripts/<domain>/<topic>/<id>/  Implementation, metadata.yaml, README.md
packages/common/         Shared Bash and Python utilities
cli/                     Search, metadata inspection, and safe execution
templates/               Contribution templates
tests/                   Offline regression and catalog tests
docs/                    MkDocs and contribution documentation
examples/                Runnable examples
```

## Coverage roadmap

| Category | Target |
|---|---:|
| Cloud infrastructure and DevOps | 120 |
| Linux, Windows and macOS administration | 120 |
| Files, folders and documents | 100 |
| Data engineering and databases | 100 |
| Web scraping and browser automation | 100 |
| APIs, integrations and webhooks | 80 |
| AI, ML and LLMOps | 100 |
| Security, auditing and compliance | 80 |
| Developer productivity and Git | 80 |
| Networking and monitoring | 70 |
| Business and office productivity | 70 |
| Email, messaging and notifications | 50 |
| Backup, recovery and storage | 50 |
| Media, image, audio and video | 50 |
| Personal and desktop automation | 50 |
| Testing, QA and performance | 60 |
| **Total planned** | **1,280** |

See [the roadmap](docs/roadmap.md) for the four delivery phases. Existing scripts are grouped by domain and have individually documented prerequisites, security classification, and `--help` behavior.

## Test and contribute

```bash
bash tests/run_tests.sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
pip install -r requirements-docs.txt
mkdocs serve
```

Every script requires real behavior, a stable ID, a self-contained directory, valid metadata, clear usage/outputs, appropriate tests, no embedded secrets, and confirmation for destructive behavior. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [CLI guide](docs/cli.md).

## License

MIT; see [LICENSE](LICENSE).
