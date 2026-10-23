#!/usr/bin/env python3
"""Check installed PostgreSQL backup behavior using only an owned fixture server."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("automation", type=Path)
    parser.add_argument("--pg-bin", type=Path)
    args = parser.parse_args()
    executable = str(args.automation.resolve(strict=True))
    spec = importlib.util.spec_from_file_location(
        "postgres_fixture",
        ROOT / "scripts/backup-recovery/postgres/postgres-verified-backup/script.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tools = module.binaries(args.pg_bin)
    checks = []
    with (
        module.PrivateCluster(tools, time.monotonic() + 120) as source,
        tempfile.TemporaryDirectory() as directory,
    ):
        source.sql("CREATE DATABASE installation_fixture")
        environment = dict(source.environment, PGDATABASE="installation_fixture")
        source.sql(
            "CREATE TABLE data(id INTEGER PRIMARY KEY); INSERT INTO data VALUES (42)",
            environment,
        )
        for name in ("AUTOMATION_ROOT", "PYTHONPATH"):
            environment.pop(name, None)
        environment["PATH"] = (
            str(Path(tools["postgres"]).parent)
            + os.pathsep
            + environment.get("PATH", "")
        )
        root = Path(directory)

        def run(*arguments, code=0):
            result = subprocess.run(
                [executable, *arguments],
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
            if result.returncode != code:
                raise RuntimeError(
                    f"Expected {code}, got {result.returncode}: {result.stderr}"
                )
            checks.append({"arguments": list(arguments), "expected_exit": code})
            return result.stdout

        catalog = json.loads(run("list", "--json"))
        script_args = [
            "--database",
            "installation_fixture",
            "--username",
            "automation_admin",
            "--host",
            source.environment["PGHOST"],
            "--output",
            "snapshot.dump",
            "--pg-bin",
            str(Path(tools["postgres"]).parent),
        ]
        run("run", "postgres-verified-backup", "--", *script_args, "--apply", code=2)
        report = json.loads(
            run("run", "postgres-verified-backup", "--yes", "--", *script_args)
        )
        if report["apply"] or (root / "snapshot.dump").exists():
            raise ValueError("Preview created an archive")
        report = json.loads(
            run(
                "run",
                "postgres-verified-backup",
                "--yes",
                "--",
                *script_args,
                "--apply",
            )
        )
        if not report["restore_verified"] or report["verified_tables"] != 1:
            raise ValueError("Installed restore verification failed")
        if (root / "snapshot.dump").read_bytes()[:5] != b"PGDMP":
            raise ValueError("Wrong archive format")
        run(
            "run",
            "postgres-verified-backup",
            "--yes",
            "--",
            *script_args,
            "--apply",
            code=2,
        )
        preview = run(
            "run", "postgres-verified-backup", "--dry-run", "--", *script_args
        )
        if "share/automation-scripts-utils" not in preview.replace("\\", "/"):
            raise ValueError("Preview did not use installed sources")
        if source.sql("SELECT id FROM data", environment) != "42":
            raise ValueError("Source fixture changed")
    print(
        json.dumps(
            {
                "result": "passed",
                "catalog_entries": len(catalog),
                "checks": checks,
                "note": "Installed CLI used outside checkout; private fixture server only, write approval, preview, restore and collision checks passed.",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
