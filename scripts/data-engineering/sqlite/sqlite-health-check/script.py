#!/usr/bin/env python3
"""Check an offline SQLite snapshot without creating locks or journal sidecars."""

import argparse
import json
import math
from pathlib import Path
import sqlite3
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument(
        "--full", action="store_true", help="use integrity_check instead of quick_check"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="maximum seconds per database check (0 < n <= 300)",
    )
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 300:
        parser.error("timeout must be finite and between 0 and 300 seconds")
    try:
        path = args.database.resolve(strict=True)
        if not path.is_file():
            raise ValueError("database must be a regular file")
        if any(
            Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")
        ):
            raise ValueError("requires an offline snapshot without journal sidecars")
        deadline = time.monotonic() + args.timeout
        connection = sqlite3.connect(
            path.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=args.timeout
        )
        try:
            connection.set_progress_handler(
                lambda: int(time.monotonic() >= deadline), 1000
            )
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
            check = "integrity_check" if args.full else "quick_check"
            checks = [row[0] for row in connection.execute("PRAGMA " + check)]
            # Bound output and memory even for a badly inconsistent database.
            rows = connection.execute("PRAGMA foreign_key_check").fetchmany(1001)
            if time.monotonic() >= deadline:
                raise TimeoutError("database check exceeded deadline")
            truncated = len(rows) > 1000
            violations = [
                dict(zip(("table", "rowid", "parent", "constraint"), row))
                for row in rows[:1000]
            ]
            healthy = checks == ["ok"] and not rows
            print(
                json.dumps(
                    {
                        "healthy": healthy,
                        "check": check,
                        "results": checks,
                        "foreign_key_violations": violations,
                        "truncated": truncated,
                    },
                    indent=2,
                )
            )
            return 0 if healthy else 1
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.Error):
        print(
            "sqlite-health-check: cannot check database (missing, unreadable, invalid, journal sidecars, or timed out)",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
