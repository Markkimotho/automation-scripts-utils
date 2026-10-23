"""Real PostgreSQL roundtrip checks on owned Unix-socket-only fixture clusters."""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/backup-recovery/postgres/postgres-verified-backup/script.py"
spec = importlib.util.spec_from_file_location("verified_postgres", SCRIPT)
postgres = importlib.util.module_from_spec(spec)
spec.loader.exec_module(postgres)


class PostgresBackupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == "nt" or not hasattr(os, "geteuid") or os.geteuid() == 0:
            raise unittest.SkipTest(
                "PostgreSQL verifier requires a non-root POSIX user"
            )
        try:
            cls.tools = postgres.binaries(os.environ.get("AUTOMATION_PG_BIN"))
            version = subprocess.check_output(
                [cls.tools["postgres"], "--version"], text=True, encoding="utf-8"
            )
            if int(re.search(r"(\d+)\.", version).group(1)) < 15:
                raise ValueError("PostgreSQL >=15 is required")
        except (OSError, ValueError):
            if os.environ.get("AUTOMATION_REQUIRE_POSTGRES") == "1":
                raise RuntimeError("PostgreSQL >=15 server/client tools are required")
            raise unittest.SkipTest(
                "PostgreSQL tools unavailable; not acceptance evidence"
            )
        cls.source = postgres.PrivateCluster(cls.tools, time.monotonic() + 300)
        cls.source.__enter__()
        cls.addClassCleanup(cls.source.close)
        cls.source.sql("CREATE DATABASE source_data")
        cls.environment = dict(cls.source.environment, PGDATABASE="source_data")
        cls.source.sql(
            "CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL); INSERT INTO items VALUES (1,'first fixture'),(2,'second fixture')",
            cls.environment,
        )
        cls.binary_directory = str(Path(cls.tools["postgres"]).parent)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "backup.dump"
        self.arguments = [
            "--database",
            "source_data",
            "--username",
            "automation_admin",
            "--host",
            self.source.environment["PGHOST"],
            "--output",
            str(self.output),
            "--pg-bin",
            self.binary_directory,
        ]

    def execute(self, *extra, code=0, arguments=None, environment=None):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                *(arguments if arguments is not None else self.arguments),
                *extra,
            ],
            env=environment or self.environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        self.assertEqual(result.returncode, code, result.stderr)
        if code == 2:
            self.assertEqual(result.stdout, "")
        return result

    def test_preview_requires_no_connection_or_output(self):
        arguments = list(self.arguments)
        arguments[arguments.index("--host") + 1] = "/tmp/nonexistent-automation-fixture"
        result = self.execute(arguments=arguments)
        self.assertFalse(json.loads(result.stdout)["apply"])
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.iterdir()), [])
        self.execute("--help", arguments=[])
        self.execute(arguments=[], code=2)

    def test_backup_restores_actual_schema_and_rows(self):
        result = self.execute("--apply")
        report = json.loads(result.stdout)
        self.assertTrue(report["restore_verified"])
        self.assertEqual(report["verified_tables"], 1)
        self.assertGreater(report["bytes"], 0)
        self.assertEqual(self.output.read_bytes()[:5], b"PGDMP")
        self.source.sql("CREATE DATABASE externally_restored")
        environment = dict(self.environment, PGDATABASE="externally_restored")
        postgres.checked(
            [
                self.tools["pg_restore"],
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "--no-password",
                "--dbname=externally_restored",
                str(self.output),
            ],
            environment,
            time.monotonic() + 30,
        )
        rows = self.source.sql(
            "SELECT id || ':' || value FROM items ORDER BY id", environment
        )
        self.assertEqual(rows.splitlines(), ["1:first fixture", "2:second fixture"])
        self.assertFalse(list(self.root.glob(".postgres-backup-*")))

    def test_verifier_is_non_superuser_and_has_no_tcp_listener(self):
        with postgres.PrivateCluster(self.tools, time.monotonic() + 60) as cluster:
            self.assertEqual(cluster.sql("SHOW listen_addresses"), "")
            verifier = cluster.verifier()
            self.assertEqual(
                cluster.sql("SELECT current_user", verifier), "automation_restore"
            )
            self.assertEqual(
                cluster.sql(
                    "SELECT rolsuper FROM pg_roles WHERE rolname=current_user", verifier
                ),
                "f",
            )
            with self.assertRaises(ValueError):
                cluster.sql("SELECT pg_read_file('postgresql.conf')", verifier)
            self.assertEqual(verifier["PGPASSFILE"], os.devnull)
            self.assertNotIn("PGPASSWORD", verifier)
            directory = Path(cluster.temporary.name)
        self.assertFalse(directory.exists())

    def test_existing_output_and_invalid_target_are_refused(self):
        self.output.write_text("KEEP", encoding="utf-8")
        self.execute("--apply", code=2)
        self.assertEqual(self.output.read_text(), "KEEP")
        self.output.unlink()
        for flag, value in [
            ("--port", "0"),
            ("--timeout", "nan"),
            ("--timeout", "0"),
            ("--max-bytes", "0"),
        ]:
            self.execute(flag, value, code=2)
        arguments = list(self.arguments)
        arguments[arguments.index("--database") + 1] = "postgres://user:SECRET@host/db"
        result = self.execute(arguments=arguments, code=2)
        self.assertNotIn("SECRET", result.stderr)

    def test_dump_budget_and_failed_connection_leave_no_archive(self):
        self.execute("--apply", "--max-bytes", "1", code=2)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".postgres-backup-*")))
        arguments = list(self.arguments)
        arguments[arguments.index("--host") + 1] = "/tmp/nonexistent-automation-fixture"
        environment = dict(self.environment, PGPASSWORD="SECRET_SENTINEL")
        result = self.execute(
            "--apply", arguments=arguments, environment=environment, code=2
        )
        self.assertNotIn("SECRET_SENTINEL", result.stdout + result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".postgres-backup-*")))

    def test_credentials_are_not_forwarded_to_private_cluster(self):
        with patch.dict(
            os.environ,
            {
                "PGPASSWORD": "SECRET_SENTINEL",
                "PGSERVICE": "unsafe-service",
                "PGHOSTADDR": "192.0.2.1",
            },
        ):
            environment = postgres.clean_environment()
        self.assertNotIn("PGPASSWORD", environment)
        self.assertNotIn("PGSERVICE", environment)
        self.assertNotIn("PGHOSTADDR", environment)
        self.assertEqual(environment["PGPASSFILE"], os.devnull)

    def test_root_execution_is_rejected_without_starting_processes(self):
        with (
            patch.object(sys, "argv", ["backup", *self.arguments, "--apply"]),
            patch.object(postgres.os, "geteuid", return_value=0),
            patch.object(postgres.subprocess, "Popen") as started,
        ):
            self.assertEqual(postgres.main(), 2)
            started.assert_not_called()

    def test_dump_deadline_terminates_the_owned_child(self):
        destination = self.root / "timed-out.dump"
        with self.assertRaises((OSError, ValueError, subprocess.SubprocessError)):
            postgres.dump(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                postgres.clean_environment(),
                time.monotonic() + 0.1,
                destination,
                1000,
            )
        # The caller owns staging cleanup; this direct helper never publishes it.
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
