#!/usr/bin/env python3
"""Validate JSON syntax without requiring an external JSON Schema engine."""
import argparse
import json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path)
    args = ap.parse_args()
    if not args.path.exists():
        ap.error("input path does not exist")
    paths = sorted(args.path.rglob("*.json")) if args.path.is_dir() else [args.path]
    results = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            results.append({"file": str(path), "valid": True})
        except (OSError, UnicodeError, json.JSONDecodeError) as e:
            results.append({"file": str(path), "valid": False, "error": str(e)})
    invalid = sum(1 for r in results if not r["valid"])
    print(json.dumps({"files_checked": len(results), "invalid": invalid, "results": results}, indent=2))
    return 1 if invalid else 0

if __name__ == "__main__":
    raise SystemExit(main())
