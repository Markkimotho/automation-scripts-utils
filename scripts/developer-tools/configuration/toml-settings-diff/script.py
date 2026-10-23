#!/usr/bin/env python3
"""Compare parsed TOML settings without printing configuration values."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

try:
    import tomllib
except ImportError:
    tomllib = None


def read(path):
    if not path.is_file() or path.stat().st_size > 2 << 20:
        raise ValueError("require regular TOML files <=2 MiB")
    with path.open("rb") as stream:
        data = stream.read((2 << 20) + 1)
    if len(data) > 2 << 20:
        raise ValueError("input grew beyond limit")
    return tomllib.loads(data.decode("utf-8"), parse_float=Decimal)


def equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, Decimal) and left.is_nan() and right.is_nan():
        return True
    if isinstance(left, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            equal(left[key], right[key]) for key in left
        )
    return left == right


def compare(left, right, path, changes):
    for key in sorted(left.keys() | right.keys()):
        current = [*path, key]
        if key not in left:
            changes.append({"path": current, "change": "added"})
        elif key not in right:
            changes.append({"path": current, "change": "removed"})
        elif isinstance(left[key], dict) and isinstance(right[key], dict):
            compare(left[key], right[key], current, changes)
        elif not equal(left[key], right[key]):
            changes.append({"path": current, "change": "changed"})
        if len(changes) > 10_000:
            raise ValueError("more than 10000 changes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    args = parser.parse_args()
    if tomllib is None:
        print("toml-settings-diff: Python >=3.11 is required", file=sys.stderr)
        return 2
    try:
        changes = []
        compare(read(args.left), read(args.right), [], changes)
        print(json.dumps({"changes": changes, "count": len(changes)}))
        return 1 if changes else 0
    except (OSError, ValueError, RecursionError, ArithmeticError):
        print(
            "toml-settings-diff: unreadable/invalid TOML or resource limit exceeded; values omitted",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
