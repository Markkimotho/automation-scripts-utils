# Architecture

The automation library is organized by **use case**, with a self-contained folder per script:

```text
scripts/cloud-devops/aws/s3-bucket-audit/
├── script.py
├── metadata.yaml
├── README.md
├── requirements.txt
└── test_script.py
```

Existing executables preserve their historical names (for example, `scripts/developer-tools/git/git-sync/git-sync.sh`) to avoid unnecessary internal rewrites.

- `scripts/`: executable implementations, each with `metadata.yaml` and `README.md`.
- `packages/common/`: migrated common Bash/Python helpers.
- `cli/`: searchable CLI with validated named parameters, dependency/platform checks and safe command previews.
- `tests/`: existing offline gate tests and catalog/CLI integrity checks.
- `catalog/scripts.json`: authoritative list of implemented scripts.
- `catalog/categories.yaml`: 16 domains and their **future** count targets.
- `docs/`: usage, architecture, reference, safety, roadmap.
- `templates/`: consistent contribution scaffolds.

The CLI does not import or execute scripts during discovery. Its `--dry-run` previews commands without executing. Metadata is not a security boundary, and running a script is still subject to its own behavior.

## Migration from the original structure

Former `bin/` scripts have moved to self-contained domain folders. Former `lib/common.sh` and `lib/common.py` are in `packages/common/`. Existing `tests/run_tests.sh` remains under `tests/`, matching the requested layout, and references the new locations.

Because `bin/` paths are no longer provided, update old shell aliases, cron jobs and PATH installations to the new CLI or the explicit new script paths. Read [Migration](migration.md) for examples.
