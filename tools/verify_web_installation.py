#!/usr/bin/env python3
"""Exercise installed web-adapted tools on private disposable fixtures."""

import argparse
from email.message import EmailMessage
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("automation", type=Path)
    args = parser.parse_args()
    executable = str(args.automation.resolve(strict=True))
    environment = os.environ.copy()
    for name in ("AUTOMATION_ROOT", "PYTHONPATH"):
        environment.pop(name, None)
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    checks = []
    with tempfile.TemporaryDirectory() as directory:
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
                timeout=60,
            )
            if result.returncode != code:
                raise RuntimeError(
                    f"Expected {code}; got {result.returncode}: {result.stderr}"
                )
            checks.append({"arguments": list(arguments), "expected_exit": code})
            return result.stdout

        catalog = json.loads(run("list", "--json"))
        connection = sqlite3.connect(root / "source.db")
        connection.execute("CREATE TABLE example(id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO example VALUES (42)")
        connection.commit()
        connection.close()
        (root / "left.toml").write_text('secret="one"\n', encoding="utf-8")
        (root / "right.toml").write_text('secret="two"\n', encoding="utf-8")
        (root / "openapi.json").write_text(
            json.dumps(
                {
                    "openapi": "3.1.0",
                    "paths": {"/health": {"get": {"operationId": "health"}}},
                }
            ),
            encoding="utf-8",
        )
        (root / "data.csv").write_text("name,value\nAlice,42\n", encoding="utf-8")
        message = EmailMessage()
        message.set_content("fixture body")
        message.add_attachment(
            b"fixture",
            maintype="application",
            subtype="octet-stream",
            filename="../../record.bin",
        )
        (root / "message.eml").write_bytes(message.as_bytes())

        source = ["--source", "source.db", "--output", "backup.db"]
        run("run", "sqlite-online-backup", "--", *source, "--apply", code=2)
        run("run", "sqlite-online-backup", "--yes", "--", *source)
        if (root / "backup.db").exists():
            raise ValueError("Preview created a snapshot")
        run("run", "sqlite-online-backup", "--yes", "--", *source, "--apply")
        run("run", "sqlite-online-backup", "--yes", "--", *source, "--apply", code=2)
        connection = sqlite3.connect(root / "backup.db")
        try:
            if connection.execute("SELECT id FROM example").fetchall() != [(42,)]:
                raise ValueError("Snapshot content mismatch")
        finally:
            connection.close()

        report = json.loads(
            run(
                "run",
                "toml-settings-diff",
                "--",
                "--left",
                "left.toml",
                "--right",
                "right.toml",
                code=1,
            )
        )
        if report["changes"] != [{"path": ["secret"], "change": "changed"}]:
            raise ValueError("Configuration comparison mismatch")
        run("run", "openapi-operation-inventory", "--param", "input=openapi.json")
        run("run", "csv-formula-audit", "--", "--input", "data.csv")
        (root / "data.csv").write_text("value\n=1+1\n", encoding="utf-8")
        run("run", "csv-formula-audit", "--", "--input", "data.csv", code=1)
        extract = [
            "run",
            "eml-attachment-extract",
            "--yes",
            "--",
            "--input",
            "message.eml",
            "--output",
            "attachments",
        ]
        run(*extract)
        if (root / "attachments").exists():
            raise ValueError("Preview created an extraction directory")
        run(*extract, "--apply")
        if (root / "attachments/attachment-0001-record.bin").read_bytes() != b"fixture":
            raise ValueError("Extracted content mismatch")

        if os.name != "nt":
            repository = root / "repo"
            subprocess.run(
                ["git", "init", "-q", "-b", "main", str(repository)],
                env=environment,
                check=True,
            )
            (repository / "tracked").write_text("committed fixture", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(repository), "add", "tracked"],
                env=environment,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "-c",
                    "user.name=Fixture",
                    "-c",
                    "user.email=fixture@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                env=environment,
                check=True,
            )
            bundle = [
                "run",
                "git-bundle-backup",
                "--yes",
                "--",
                "--repository",
                "repo",
                "--output",
                "backup.bundle",
            ]
            run(*bundle)
            if (root / "backup.bundle").exists():
                raise ValueError("Preview created a Git bundle")
            run(*bundle, "--apply")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "-q",
                    str(root / "backup.bundle"),
                    str(root / "restored"),
                ],
                env=environment,
                check=True,
            )
            if (root / "restored/tracked").read_text() != "committed fixture":
                raise ValueError("Git bundle restore mismatch")
        preview = run("run", "sqlite-online-backup", "--dry-run", "--", *source)
        if "share/automation-scripts-utils" not in preview.replace("\\", "/"):
            raise ValueError("Preview did not use installed sources")
    print(
        json.dumps(
            {
                "result": "passed",
                "catalog_entries": len(catalog),
                "checks": checks,
                "note": "Installed CLI executed outside checkout; previews, write approval, restore content, findings and collisions verified.",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
