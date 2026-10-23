# Invoice Due Report

Summarize unpaid invoices from a CSV with invoice_id, due_date, amount and paid columns.

## Usage

```bash
python3 scripts/business-productivity/finance/invoice-due-report/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON overdue invoice list and total amount.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
