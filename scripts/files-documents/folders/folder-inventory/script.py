#!/usr/bin/env python3
"""Inventory ordinary files without following directory symlinks."""
import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--format", choices=["json", "csv"], default="json")
    args = ap.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        ap.error("root must be a directory")
    rows = []
    for folder, directories, files in os.walk(root, followlinks=False):
        directories[:] = [n for n in directories if not (Path(folder) / n).is_symlink()]
        for name in files:
            path = Path(folder) / name
            if path.is_symlink():
                continue
            try:
                stats = path.stat()
            except OSError as err:
                print(f"Skipping {path}: {err}", file=sys.stderr)
                continue
            rows.append({"path": str(path.relative_to(root)), "bytes": stats.st_size, "modified_utc": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat()})
    rows.sort(key=lambda row: row["path"])
    if args.format == "json":
        print(json.dumps(rows, indent=2))
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=["path", "bytes", "modified_utc"])
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
