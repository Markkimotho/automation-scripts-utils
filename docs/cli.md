# CLI reference

## Discover

```bash
automation list
automation list --category developer-tools
automation list --language python --platform linux
automation list --permission filesystem-read
automation search "git conflict"
automation search "backup"
automation list --json
```

## Inspect

```bash
automation info git-conflict-helper
```

This displays the script's purpose, platform, dependencies and permissions.

## Execute

```bash
automation run git-conflict-helper --dry-run
automation run git-conflict-helper -- --help
automation run json-batch-validate -- /path/to/json-files
```

Script-specific arguments follow `--`.

## Options

- `--dry-run`: preview the command without executing the script.
- `--yes`: approve an operation requiring confirmation.
- `--param KEY=VALUE`: validate a declared parameter before execution.

See [Safety](safety.md) and [Script directory](scripts.md).
