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

Go scripts require an installed Go compiler. The CLI builds a temporary executable, runs it in your current working directory, and removes it afterward. This preserves the script's exit codes: for the offline audit tools, `0` means no findings, `1` means findings, and `2` means invalid input or an execution error. Compilation failures return `2` and print the compiler diagnostics.

Go execution needs writable temporary storage and a writable Go build cache. `--dry-run` shows both the build and execution commands without compiling or reading input files.

## Options

- `--dry-run`: preview the command without executing the script.
- `--yes`: approve an operation requiring confirmation.
- `--param KEY=VALUE`: validate a declared parameter before execution.

See [Safety](safety.md) and [Script directory](scripts.md).
