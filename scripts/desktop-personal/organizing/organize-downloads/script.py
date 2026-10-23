#!/usr/bin/env python3
"""Organize non-symlink files by extension, with no overwrite."""
import argparse
from pathlib import Path
import shutil

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        ap.error("directory must exist")
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        group = path.suffix.lower().lstrip(".") or "no-extension"
        target_folder = root / group
        candidate = target_folder / path.name
        suffix = 1
        while candidate.exists():
            candidate = target_folder / f"{path.stem}-{suffix}{path.suffix}"
            suffix += 1
        print(f"{'MOVE' if args.apply else 'WOULD MOVE'} {path.name} -> {candidate.relative_to(root)}")
        if args.apply:
            target_folder.mkdir(exist_ok=True)
            shutil.move(str(path), str(candidate))

if __name__ == "__main__":
    main()
