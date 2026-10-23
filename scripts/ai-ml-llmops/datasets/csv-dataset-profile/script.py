#!/usr/bin/env python3
"""Profile a CSV file using only the Python standard library."""
import argparse
import csv
import json
from pathlib import Path

def profile(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        names = reader.fieldnames
        missing = {name: 0 for name in names}
        count = 0
        for row in reader:
            count += 1
            for name in names:
                if row.get(name) is None or not str(row[name]).strip():
                    missing[name] += 1
        return {"rows": count, "columns": len(names), "missing_by_column": missing}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(profile(args.csv_file), indent=2))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"Dataset profile failed: {error}\n")

if __name__ == "__main__":
    main()
