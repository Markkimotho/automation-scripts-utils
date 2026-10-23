#!/usr/bin/env python3
"""Inspect ZIP metadata for extraction hazards; never decompress or extract."""

import argparse
import json
from pathlib import Path
import re
import stat
import sys
import zipfile


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument(
        "--max-bytes",
        type=positive,
        default=1_073_741_824,
        help="maximum declared uncompressed bytes",
    )
    parser.add_argument(
        "--max-ratio",
        type=positive,
        default=100,
        help="maximum per-member expansion ratio",
    )
    args = parser.parse_args()
    try:
        if not args.archive.is_file() or args.archive.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("archive must be a regular file no larger than 64 MiB")
        findings, seen, total = [], set(), 0
        with zipfile.ZipFile(args.archive) as archive:
            members = archive.infolist()
            for index, member in enumerate(members):
                # Use the original name so an embedded NUL cannot hide a suffix.
                name = member.orig_filename.replace("\\", "/")
                parts = name.rstrip("/").split("/")
                reasons = []
                if name.startswith("/") or any(p in ("", ".", "..") for p in parts):
                    reasons.append("unsafe-path")
                if any(
                    ":" in p or "\x00" in p or p.endswith((" ", ".")) for p in parts
                ):
                    reasons.append("nonportable-path")
                if any(
                    re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
                    for p in parts
                ):
                    reasons.append("windows-reserved-name")
                normalized = name.rstrip("/").casefold()
                if normalized in seen:
                    reasons.append("duplicate-path")
                seen.add(normalized)
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    reasons.append("symlink")
                elif stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                    reasons.append("special-file")
                if member.flag_bits & 1:
                    reasons.append("encrypted")
                if member.file_size > args.max_ratio * max(1, member.compress_size):
                    reasons.append("expansion-ratio")
                total += member.file_size
                if reasons:
                    findings.append(
                        {
                            "member": index,
                            "name": member.orig_filename,
                            "reasons": reasons,
                        }
                    )
        if total > args.max_bytes:
            findings.append({"reasons": ["total-size-limit"]})
        print(
            json.dumps(
                {
                    "members": len(members),
                    "declared_bytes": total,
                    "findings": findings,
                },
                indent=2,
            )
        )
        return 1 if findings else 0
    except (OSError, ValueError, zipfile.BadZipFile):
        print(
            "zip-safety-audit: archive is missing, unreadable, invalid, or exceeds the input limit",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
