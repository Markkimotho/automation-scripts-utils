# SQLite Health Check

Check an offline SQLite snapshot for structural and foreign-key problems without creating journal sidecars.

Use before accepting a local database backup or when diagnosing application data inconsistencies.

## Requirements and input

Python >=3.10 with SQLite >=3.31. No third-party packages. Verified on macOS; Linux and Windows verification is pending.

An existing, stable offline SQLite snapshot. Do not use a file that another process may modify. Zero-byte files are valid empty SQLite databases.

## Run

```bash
automation run sqlite-health-check -- --database ./app.db --full
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--database PATH` | Required database file. |
| `--full` | Use the more expensive integrity check; default is quick check. |
| `--timeout SECONDS` | Deadline, default 10; finite, greater than 0 and at most 300. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"healthy": true, "check": "quick_check", "results": ["ok"], "foreign_key_violations": [], "truncated": false}
```

## Safety and limitations

Opens with mode=ro and immutable=1, disables trusted schema behavior and enables query_only. Immutable mode avoids locks and journal writes and requires a stable offline snapshot. Does not repair, vacuum, execute supplied SQL or load extensions. Output may include table names and row IDs. Use a consistent offline copy for backup checks.

- Checks trusted local databases; not a hardened parser for hostile SQLite files.
- The SQLite VM progress callback and lock timeout cannot forcibly interrupt stalled operating-system I/O.
- Files with adjacent -wal, -shm or -journal sidecars are rejected. Create a consistent offline backup with SQLite’s backup API first; do not manually remove active journals.
- Foreign-key findings are capped at 1000; truncated=true means more exist.

## Exit codes and troubleshooting

Exit 2 covers missing/unreadable files, invalid databases, adjacent journal sidecars and deadlines. Retry on an offline backup, increase the deadline for a large database, or check SQLite availability.

- `0`: Report completed without policy findings or differences.
- `1`: Findings, invalid records, differences or unhealthy data.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
