#!/usr/bin/env python3
"""Stream JSON Lines and report object key coverage without printing values."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys


def reject_constant(_):
    raise ValueError("nonstandard JSON constant")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--max-line-bytes", type=int, default=1_048_576)
    parser.add_argument("--max-records", type=int, default=1_000_000)
    args = parser.parse_args()
    if not 0 < args.max_line_bytes <= 16_777_216 or args.max_records <= 0:
        parser.error("limits must be positive; max-line-bytes cannot exceed 16 MiB")
    keys, invalid, records, lines, blanks = Counter(), [], 0, 0, 0
    try:
        if not args.input.is_file():
            raise ValueError("input must be a regular file")
        with args.input.open("rb") as stream:
            while True:
                line = stream.readline(args.max_line_bytes + 1)
                if not line:
                    break
                lines += 1
                if lines > args.max_records or len(line) > args.max_line_bytes:
                    raise ValueError("input exceeds configured line or record limit")
                if not line.strip():
                    blanks += 1
                    continue
                try:
                    item = json.loads(
                        line.decode("utf-8"),
                        parse_constant=reject_constant,
                        object_pairs_hook=unique_object,
                    )
                    if not isinstance(item, dict):
                        raise ValueError("expected an object")
                except (ValueError, UnicodeError, RecursionError):
                    if len(invalid) < 1000:
                        invalid.append(lines)
                    continue
                records += 1
                keys.update(item.keys())
                if len(keys) > 10_000:
                    raise ValueError("more than 10000 distinct top-level keys")
        invalid_count = lines - records - blanks
        print(
            json.dumps(
                {
                    "lines": lines,
                    "records": records,
                    "blank_lines": blanks,
                    "invalid_count": invalid_count,
                    "invalid_lines": invalid,
                    "truncated": invalid_count > len(invalid),
                    "keys": {
                        key: {"present": count, "missing": records - count}
                        for key, count in sorted(keys.items())
                    },
                },
                indent=2,
            )
        )
        return 1 if invalid_count else 0
    except (OSError, ValueError):
        print(
            "jsonl-key-profile: input unreadable or resource limit exceeded",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
