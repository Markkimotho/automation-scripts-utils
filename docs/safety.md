# Safe execution

Inspect a script before running it:

```bash
automation info organize-downloads
automation run organize-downloads --dry-run
```

The CLI's `--dry-run` previews the command **without executing it**. A script's own preview or dry-run option may provide additional details.

Scripts with declared write permissions prompt for confirmation. To approve a non-interactive operation, pass `--yes` only after reviewing the script and its arguments.

```bash
automation run organize-downloads --yes -- --directory ~/Downloads --apply
```

Use the least-privileged credentials possible. Only access systems and websites you are authorized to inspect. Back up important data before deletion, replacement or cleanup.
