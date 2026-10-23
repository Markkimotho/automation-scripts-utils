#!/usr/bin/env python3
"""Measure bounded SQLite backup and CSV audit workloads on temporary fixtures."""

from contextlib import closing
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    ruby = shutil.which("ruby")
    if ruby is None:
        raise RuntimeError("Ruby is required for the CSV benchmark")
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, output = root / "source.db", root / "snapshot.db"
        with closing(sqlite3.connect(source)) as connection, connection:
            connection.execute("CREATE TABLE data(value TEXT)")
            connection.executemany(
                "INSERT INTO data VALUES (?)", (("fixture" * 64,) for _ in range(10000))
            )
        command = [
            sys.executable,
            str(ROOT / "scripts/backup-recovery/sqlite/sqlite-online-backup/script.py"),
            "--source",
            str(source),
            "--output",
            str(output),
            "--apply",
        ]
        start = time.perf_counter()
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=30,
        )
        elapsed = time.perf_counter() - start
        with closing(sqlite3.connect(output)) as connection:
            if connection.execute("SELECT COUNT(*) FROM data").fetchone()[0] != 10000:
                raise ValueError("Snapshot content is incomplete")
        results.append(
            {
                "tool": "sqlite-online-backup",
                "rows": 10000,
                "source_bytes": source.stat().st_size,
                "output_bytes": output.stat().st_size,
                "elapsed_seconds": elapsed,
                "result": "passed",
            }
        )
        csv = root / "data.csv"
        csv.write_text(
            "name,value\n" + "".join(f"person-{index},42\n" for index in range(10000)),
            encoding="utf-8",
        )
        start = time.perf_counter()
        result = subprocess.run(
            [
                ruby,
                str(
                    ROOT / "scripts/security-compliance/csv/csv-formula-audit/script.rb"
                ),
                "--input",
                str(csv),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=30,
        )
        elapsed = time.perf_counter() - start
        report = json.loads(result.stdout)
        if report["rows"] != 10001 or report["finding_count"] != 0:
            raise ValueError("Incorrect CSV audit result")
        results.append(
            {
                "tool": "csv-formula-audit",
                "records_including_header": 10001,
                "input_bytes": csv.stat().st_size,
                "elapsed_seconds": elapsed,
                "result": "passed",
            }
        )
    print(
        json.dumps(
            {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "results": results,
                "note": "Single local end-to-end measurements, including runtime startup; not cross-platform performance guarantees.",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
