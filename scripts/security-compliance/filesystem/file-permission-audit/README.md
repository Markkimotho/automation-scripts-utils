# File Permission Audit

Find world-writable regular files under a directory without following symlinks.

## Usage

```bash
python3 scripts/security-compliance/filesystem/file-permission-audit/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON list of world-writable files; exit 1 if found.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
