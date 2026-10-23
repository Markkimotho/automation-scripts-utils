#!/usr/bin/env python3
"""Preview or create a verified SQLite snapshot using the online backup API."""

import argparse
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--max-bytes", type=int, default=1 << 30)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if (
        not math.isfinite(args.timeout)
        or not 0 < args.timeout <= 300
        or not 0 < args.max_bytes <= 1 << 40
    ):
        parser.error(
            "timeout must be finite in (0,300]; max-bytes must be in 1..1099511627776"
        )
    try:
        source = args.source.expanduser().resolve(strict=True)
        output = args.output.expanduser().absolute()
        output = output.parent.resolve(strict=True) / output.name
        if not source.is_file() or os.path.lexists(output):
            raise ValueError("require an existing source and a new output path")
        if not args.apply:
            print(
                json.dumps(
                    {"apply": False, "source": str(source), "output": str(output)}
                )
            )
            return 0
        deadline = time.monotonic() + args.timeout
        with tempfile.TemporaryDirectory(
            prefix=".sqlite-backup-", dir=output.parent
        ) as directory:
            staged = Path(directory) / "snapshot.db"
            staged.touch(mode=0o600, exist_ok=False)
            reader = sqlite3.connect(
                source.as_uri() + "?mode=ro", uri=True, timeout=min(5, args.timeout)
            )
            try:
                reader.execute("PRAGMA trusted_schema=OFF")
                reader.execute("PRAGMA query_only=ON")
                page_size = reader.execute("PRAGMA page_size").fetchone()[0]

                def progress(_status, _remaining, total):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("backup deadline exceeded")
                    if total * page_size > args.max_bytes:
                        raise ValueError("logical database exceeds max-bytes")

                writer = sqlite3.connect(staged)
                try:
                    reader.backup(writer, pages=128, progress=progress, sleep=0.01)
                    writer.execute("PRAGMA trusted_schema=OFF")
                    writer.set_progress_handler(
                        lambda: int(time.monotonic() >= deadline), 1000
                    )
                    checks = writer.execute("PRAGMA quick_check").fetchmany(101)
                    if checks != [("ok",)] or time.monotonic() >= deadline:
                        raise ValueError(
                            "snapshot integrity check failed or deadline exceeded"
                        )
                finally:
                    writer.close()
            finally:
                reader.close()
            if staged.stat().st_size > args.max_bytes:
                raise ValueError("snapshot exceeds max-bytes")
            with staged.open("rb+") as stream:
                os.fsync(stream.fileno())
            # Same-filesystem hard-link publication is atomic and never replaces a file.
            os.link(staged, output)
            size = output.stat().st_size
        print(
            json.dumps(
                {
                    "apply": True,
                    "output": str(output),
                    "bytes": size,
                    "quick_check": "ok",
                }
            )
        )
        return 0
    except (OSError, ValueError, sqlite3.Error):
        print(
            "sqlite-online-backup: unreadable/invalid database, existing output, unsupported hard links, resource limit or I/O failure",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
