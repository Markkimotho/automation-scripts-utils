# Incremental File Copy

Preview and optionally copy changed regular files to a separate backup directory without deleting old backups.

## Usage

```bash
python3 scripts/backup-recovery/filesystem/incremental-file-copy/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; preview by default, with writes only when --apply is supplied.

## Expected output

Planned or copied file paths; destination never pruned.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
