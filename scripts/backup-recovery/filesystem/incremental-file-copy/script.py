#!/usr/bin/env python3
"""Preview incremental copies; write only when --apply is supplied."""
import argparse
import os
from pathlib import Path
import shutil

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--destination", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    source, dest = args.source.resolve(), args.destination.resolve()
    if not source.is_dir():
        ap.error("source must be a directory")
    if source == dest or dest.is_relative_to(source) or source.is_relative_to(dest):
        ap.error("source and destination must be separate non-overlapping directories")
    copied = 0
    for folder, directories, files in os.walk(source, followlinks=False):
        directories[:] = [name for name in directories if not (Path(folder) / name).is_symlink()]
        for name in files:
            path = Path(folder) / name
            if path.is_symlink():
                continue
            target = dest / path.relative_to(source)
            if target.is_symlink():
                ap.error(f"destination symlink refused: {target}")
            if target.exists() and not target.is_file():
                ap.error(f"destination is not a regular file: {target}")
            if target.exists() and path.stat().st_size == target.stat().st_size and path.stat().st_mtime_ns <= target.stat().st_mtime_ns:
                continue
            print(("COPY " if args.apply else "WOULD COPY ") + str(path.relative_to(source)))
            if args.apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            copied += 1
    print(f"{copied} files " + ("copied" if args.apply else "would be copied"))

if __name__ == "__main__":
    main()
