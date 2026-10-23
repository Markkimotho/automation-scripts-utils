# Migrating from the legacy layout

All 34 original executables were moved into `scripts/<domain>/<topic>/<id>/`. The original `bin/` directory is no longer the primary entry point. Shared helper code is now in `packages/common/`, and `tests/` remains the test directory.

Old:
```bash
export PATH="$PWD/bin:$PATH"
git-conflict-helper.sh --check
```

New:
```bash
export PATH="$PWD/cli:$PATH"
automation info git-conflict-helper
automation run git-conflict-helper -- --check
```

Or:
```bash
bash scripts/developer-tools/git/git-conflict-helper/git-conflict-helper.sh --check
```

Update shell profiles, CI, launch agents, cron jobs and any absolute paths in automation runners. Prefer `automation run` for catalog discovery and confirmation, or direct script calls when exact argument behavior is required.

The existing test suite uses the relocated script paths. Changes in the library should preserve the individual scripts' original documented options where feasible.
