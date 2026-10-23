# Automation CLI and catalog

The CLI is implemented with the Python standard library. Add `cli/` to your PATH or run `python3 cli/automation_cli.py`.

```bash
export PATH="$PWD/cli:$PATH"
automation list
automation list --category developer-tools
automation list --language bash --platform macos
automation list --permission filesystem-write
automation search "git conflict"
automation info git-conflict-helper
automation run git-conflict-helper --dry-run
automation run git-conflict-helper -- --help
```

## Run controls

- `--dry-run` is a **CLI-level preview**, not a guarantee that a script implements its own native dry-run option. It never invokes the target process.
- `--yes` approves mutating operations non-interactively and exports `ASSUME_YES=1` for legacy scripts that support it. Do not pass `--yes` to unknown external scripts casually.
- `--param key=value` checks named parameters against declared type, required status, and choices before forwarding the corresponding `--key value` flag. Unregistered legacy scripts currently have no such parameter schema and validate their own arguments.
- Script-specific flags and positionals are passed after `--`. The CLI never invokes a shell for command assembly.
- Platform support and dependencies are checked on real execution.
- Scripts are resolved only inside `scripts/`; unmanaged paths cannot be executed through the catalog.

## Script inventory

`catalog/scripts.json` is authoritative for currently implemented scripts. Every entry points to a self-contained implementation folder containing `metadata.yaml` and `README.md`. Categories live in `catalog/categories.yaml` and may have no scripts yet.

`automation search "backup postgres"` returns no results until such a specific script is actually committed, reviewed, and added to the catalog.
