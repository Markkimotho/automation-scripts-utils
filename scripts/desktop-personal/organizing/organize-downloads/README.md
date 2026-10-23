# Organize Downloads

Preview and optionally sort top-level files into extension-named folders without overwriting existing files.

## Usage

```bash
python3 scripts/desktop-personal/organizing/organize-downloads/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; preview by default, with writes only when --apply is supplied.

## Expected output

Planned or completed moves by extension.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
