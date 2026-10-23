#!/usr/bin/env python3
"""Exercise an installed CLI from a temporary directory, independent of the checkout."""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "automation", type=Path, help="absolute path to installed automation command"
    )
    args = parser.parse_args()
    executable = str(args.automation.resolve(strict=True))
    environ = os.environ.copy()
    for name in ("AUTOMATION_ROOT", "PYTHONPATH"):
        environ.pop(name, None)
    checks = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        def run(*arguments):
            result = subprocess.run(
                [executable, *arguments],
                cwd=root,
                env=environ,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            checks.append(list(arguments))
            return result.stdout

        entries = json.loads(run("list", "--json"))
        assert any(x["id"] == "git-conflict-helper" for x in entries)
        run("run", "git-conflict-helper", "--", "--help")
        (root / "input.jsonl").write_text('{"id":1}\n', encoding="utf-8")
        (root / "data.csv").write_text("id,value\n1,test\n", encoding="utf-8")
        (root / "package-lock.json").write_text(
            '{"lockfileVersion":3,"packages":{}}', encoding="utf-8"
        )
        (root / "input.har").write_text(
            '{"log":{"version":"1.2","entries":[]}}', encoding="utf-8"
        )
        connection = sqlite3.connect(root / "data.db")
        connection.execute("CREATE TABLE example(id INTEGER PRIMARY KEY)")
        connection.close()
        import zipfile

        with zipfile.ZipFile(root / "data.zip", "w") as archive:
            archive.writestr("a.txt", "safe")
        fixtures = {
            "sqlite-health-check": ["database=data.db"],
            "zip-safety-audit": ["archive=data.zip"],
            "jsonl-key-profile": ["input=input.jsonl"],
            "csv-key-reconcile": ["left=data.csv", "right=data.csv", "key=id"],
            "npm-lock-audit": ["lockfile=package-lock.json"],
            "har-timing-summary": ["input=input.har"],
        }
        for identifier, params in fixtures.items():
            info = json.loads(run("info", identifier))
            assert info["provenance_ref"] == identifier
            arguments = ["run", identifier]
            for parameter in params:
                arguments.extend(["--param", parameter])
            result = json.loads(run(*arguments))
            assert isinstance(result, dict)
            preview = run(*arguments, "--dry-run")
            assert (
                "PREVIEW ONLY" in preview
                and "share/automation-scripts-utils" in preview.replace("\\", "/")
            )
        print(
            json.dumps(
                {
                    "result": "passed",
                    "catalog_entries": len(entries),
                    "checks": checks,
                    "note": "All six new scripts executed from a temporary working directory using the installed CLI.",
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
