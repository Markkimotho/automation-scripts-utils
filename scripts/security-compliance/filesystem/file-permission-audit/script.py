#!/usr/bin/env python3
"""List world-writable files without changing permissions."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("root must be a directory")
    results = []
    for base, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if not (Path(base) / name).is_symlink()]
        for name in files:
            path = Path(base) / name
            if path.is_symlink():
                continue
            try:
                mode = path.stat().st_mode
            except OSError as error:
                print(f"Skipping {path}: {error}", file=sys.stderr)
                continue
            if stat.S_ISREG(mode) and mode & stat.S_IWOTH:
                results.append(str(path.relative_to(root)))
    print(json.dumps({"world_writable_files": sorted(results)}, indent=2))
    return 1 if results else 0

if __name__ == "__main__":
    raise SystemExit(main())
