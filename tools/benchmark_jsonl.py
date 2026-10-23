#!/usr/bin/env python3
"""Measure the JSONL profiler on a deterministic temporary 100000-row input."""

import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "input.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            for index in range(100_000):
                stream.write(json.dumps({"id": index, "group": index % 10}) + "\n")
        start = time.monotonic()
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/testing-qa/jsonl/jsonl-key-profile/script.py"),
                "--input",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        elapsed = time.monotonic() - start
        report = json.loads(result.stdout)
        if report["records"] != 100_000 or report["invalid_count"] != 0:
            raise ValueError("Incorrect benchmark result")
        peak_bytes = None
        if sys.platform in ("darwin", "linux"):
            import resource

            peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            peak_bytes = peak if sys.platform == "darwin" else peak * 1024
        print(
            json.dumps(
                {
                    "platform": platform.platform(),
                    "python": platform.python_version(),
                    "records": 100_000,
                    "input_bytes": path.stat().st_size,
                    "elapsed_seconds": elapsed,
                    "child_peak_rss_bytes": peak_bytes,
                    "result": "passed",
                    "note": "One local measurement; not a cross-platform performance guarantee.",
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
