# Json Batch Validate

Validate JSON syntax for a file or folder recursively and report the filename and parse errors.

## Usage

```bash
python3 scripts/testing-qa/json/json-batch-validate/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON summary of valid and invalid JSON files.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
