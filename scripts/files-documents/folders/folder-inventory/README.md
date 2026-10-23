# Folder Inventory

Inventory regular files recursively with size and modification timestamps, exporting structured JSON or CSV.

## Usage

```bash
python3 scripts/files-documents/folders/folder-inventory/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON or CSV list of files and sizes.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
