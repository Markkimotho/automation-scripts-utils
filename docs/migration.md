# Migration checklist

1. Inventory all existing executables and import/sourcing dependencies.
2. Move a coherent domain of scripts in one commit, updating imports and shell helper paths.
3. Move shared Bash/Python helpers to `packages/common/` and update all callers.
4. Move existing test suites to `quality/tests/` and fix fixture paths.
5. Update Makefile, GitHub Actions, MkDocs navigation, install instructions and examples.
6. Verify `--help` for every entry point, run offline tests and docs build.
7. Remove old paths only after all references and compatibility decisions are reviewed.

Do not treat the catalog's 1,200-script target as the number of implemented scripts.
