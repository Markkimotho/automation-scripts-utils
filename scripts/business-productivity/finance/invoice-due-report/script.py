#!/usr/bin/env python3
"""Report overdue invoices from an offline CSV export."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_file", type=Path)
    ap.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD")
    args = ap.parse_args()
    overdue, total = [], Decimal("0")
    try:
        with args.csv_file.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            required = {"invoice_id", "due_date", "amount", "paid"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                ap.error("CSV must have invoice_id,due_date,amount,paid columns")
            for row in reader:
                if (row["paid"] or "").strip().lower() in ("true", "yes", "1", "paid"):
                    continue
                due = date.fromisoformat(row["due_date"])
                amount = Decimal(row["amount"])
                if not amount.is_finite() or amount < 0:
                    raise ValueError("amount must be finite and nonnegative")
                if due < args.as_of:
                    overdue.append({"invoice_id": row["invoice_id"], "due_date": str(due), "amount": str(amount)})
                    total += amount
        print(json.dumps({"as_of": str(args.as_of), "overdue_count": len(overdue), "total_overdue": str(total), "invoices": overdue}, indent=2))
    except (OSError, ValueError, InvalidOperation) as e:
        ap.exit(2, f"Invalid invoice input: {e}\n")

if __name__ == "__main__":
    main()
