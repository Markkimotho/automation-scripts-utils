# Csv Dataset Profile

Profile a CSV dataset by counting rows and missing values per column without exposing data values.

## Usage

```bash
python3 scripts/ai-ml-llmops/datasets/csv-dataset-profile/script.py --help
```

## Requirements

Python 3.10+. Supported on Linux, macOS and Windows; read-only operation.

## Expected output

JSON row count and per-column missing value counts.

## Tests

Run `python3 -m unittest discover -s tests -p 'test_*.py'` from the repository root.
