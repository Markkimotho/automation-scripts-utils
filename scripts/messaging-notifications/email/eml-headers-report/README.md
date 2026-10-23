# Eml Headers Report

Extract email headers from local .eml files without accessing an inbox or sending messages.

## Usage

```bash
python3 scripts/messaging-notifications/email/eml-headers-report/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON list of local mail headers.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
