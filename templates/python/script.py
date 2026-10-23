#!/usr/bin/env python3
"""Template: count bytes in a local file, with explicit input validation."""
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file() or args.input.is_symlink():
        parser.error("input must be a regular file, not a symlink")
    print(f"File bytes: {args.input.stat().st_size}")

if __name__ == "__main__":
    main()
