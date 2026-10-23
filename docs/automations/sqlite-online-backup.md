# SQLite Online Backup

Preview or create a consistent SQLite snapshot through the online backup API, verify it and publish without overwriting files.

Back up a local application database while SQLite manages consistency, including committed data still in WAL files.

## Requirements and inputs

Python >=3.10 with SQLite >=3.31; standard library only. Verified locally on macOS; other platforms are not yet declared supported.

Existing trusted local SQLite database and a new output filename whose parent directory exists.

## Run

```bash
automation run sqlite-online-backup --yes -- --source ./app.db --output ./backup.db
```

The example previews the operation. To create files, append `--apply` after the script options. Keep `--yes` to explicitly approve the script’s write permissions. Library-level `--dry-run` before `--` previews the command without executing the script.

## Options

| Option | Meaning |
| --- | --- |
| `--source PATH` | Required existing database. |
| `--output PATH` | Required new snapshot; existing files and symlinks are refused. |
| `--timeout N` | Best-effort seconds, default 30; finite and greater than 0, up to 300. |
| `--max-bytes N` | Logical/snapshot size budget; default 1073741824, maximum 1099511627776. |
| `--apply` | Create the snapshot. |
| `--dry-run` | Explicit preview; mutually exclusive with --apply. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```json
{"apply":true,"output":"/backups/app.db","bytes":8192,"quick_check":"ok"}
```

## Safety and limitations

Default is preview only. Add --apply to write; the library CLI also requires --yes. The snapshot is private (0600 on POSIX). Source files are not copied byte-for-byte with filesystem tools. Staging is removed on failure; an already published, complete snapshot is retained if a later reporting error occurs.

- Preview checks paths without opening SQLite or creating staging files; it does not certify database contents.
- The source connection is read-only, but SQLite may create or update WAL shared-memory sidecars. No source tables are modified.
- Backups use private staging files and hard-link publication. The filesystem must support hard links; outputs are never replaced.
- Deadlines are checked between SQLite work steps and cannot interrupt stalled operating-system I/O. Size checks can overshoot temporarily by a work chunk before aborting.
- Use trusted local database files and a stable output parent. quick_check does not validate application invariants or foreign keys.

## Exit codes and troubleshooting

Exit 2 covers existing output, invalid or locked source, limits, permissions or unavailable hard-link support. Inspect any existing output before retrying; choose a new filename rather than deleting an active database.

- `0`: Preview or operation completed without report findings.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
