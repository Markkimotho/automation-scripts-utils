"""Offline behavioral and safety fixtures for the researched local automations."""

import base64
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    "sqlite-health-check": ("python", "data-engineering/sqlite", "py"),
    "zip-safety-audit": ("python", "security-compliance/archives", "py"),
    "jsonl-key-profile": ("python", "testing-qa/jsonl", "py"),
    "csv-key-reconcile": ("ruby", "data-engineering/csv", "rb"),
    "npm-lock-audit": ("javascript", "developer-tools/dependencies", "js"),
    "har-timing-summary": ("javascript", "networking-monitoring/har", "js"),
}


def entrypoint(identifier):
    _, folder, suffix = ENTRIES[identifier]
    return ROOT / "scripts" / folder / identifier / ("script." + suffix)


class VerifiedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("AUTOMATION_REQUIRE_RUNTIMES") == "1":
            for runner in ("node", "ruby"):
                if not shutil.which(runner):
                    raise RuntimeError(runner + " is required for acceptance tests")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_script(self, identifier, *args, code=0):
        language = ENTRIES[identifier][0]
        runner = {"python": sys.executable, "ruby": "ruby", "javascript": "node"}[
            language
        ]
        if not shutil.which(runner):
            self.skipTest(runner + " is unavailable; this is not acceptance evidence")
        result = subprocess.run(
            [runner, str(entrypoint(identifier)), *map(str, args)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, code, result.stderr)
        if code == 2:
            self.assertEqual(
                result.stdout,
                "",
                "invalid input must not emit a partial success report",
            )
        return result

    def write(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_help_missing_arguments_and_missing_file_for_every_script(self):
        flags = {
            "sqlite-health-check": "--database",
            "zip-safety-audit": "--archive",
            "jsonl-key-profile": "--input",
            "npm-lock-audit": "--lockfile",
            "har-timing-summary": "--input",
        }
        for identifier in ENTRIES:
            with self.subTest(script=identifier):
                self.assertTrue(self.run_script(identifier, "--help").stdout)
                self.run_script(identifier, code=2)
                if identifier == "csv-key-reconcile":
                    self.run_script(
                        identifier,
                        "--left",
                        self.root / "missing",
                        "--right",
                        self.root / "missing",
                        "--key",
                        "id",
                        code=2,
                    )
                else:
                    self.run_script(
                        identifier, flags[identifier], self.root / "missing", code=2
                    )

    def database(self):
        path = self.root / ("data ü.db" if sys.platform == "win32" else "data?# ü.db")
        with closing(sqlite3.connect(path)) as db, db:
            db.executescript(
                "CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE child(id REFERENCES parent(id));"
            )
        return path

    def test_sqlite_quick_full_idempotent_and_read_only(self):
        path = self.database()
        before = path.read_bytes()
        for flags in [[], ["--full"], []]:
            report = json.loads(
                self.run_script(
                    "sqlite-health-check", "--database", path, *flags
                ).stdout
            )
            self.assertTrue(report["healthy"])
            self.assertEqual(
                report["check"], "integrity_check" if flags else "quick_check"
            )
        self.assertEqual(before, path.read_bytes())

    def test_sqlite_foreign_key_inconsistency(self):
        path = self.database()
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("INSERT INTO child VALUES (42)")
        report = json.loads(
            self.run_script("sqlite-health-check", "--database", path, code=1).stdout
        )
        self.assertFalse(report["healthy"])
        self.assertEqual(report["foreign_key_violations"][0]["parent"], "parent")

    def test_sqlite_corrupt_empty_and_bad_timeouts(self):
        self.run_script(
            "sqlite-health-check",
            "--database",
            self.write("bad.db", "not a database"),
            code=2,
        )
        # SQLite defines a zero-byte file as a valid empty database.
        self.run_script("sqlite-health-check", "--database", self.write("empty.db", ""))
        for timeout in ["0", "-1", "nan", "inf", "301"]:
            path = self.database()
            self.run_script(
                "sqlite-health-check", "--database", path, "--timeout", timeout, code=2
            )
            path.unlink()

    def test_sqlite_timeout_and_permission_failure(self):
        path = self.database()
        self.run_script(
            "sqlite-health-check",
            "--database",
            path,
            "--timeout",
            "0.000000001",
            code=2,
        )
        # Deterministic permission failure even when CI executes as an administrator.
        spec = importlib.util.spec_from_file_location(
            "sqlite_health", entrypoint("sqlite-health-check")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with (
            patch.object(sys, "argv", ["check", "--database", str(path)]),
            patch.object(module.sqlite3, "connect", side_effect=PermissionError),
        ):
            self.assertEqual(module.main(), 2)

    def test_sqlite_rejects_journal_sidecars(self):
        path = self.database()
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = Path(str(path) + suffix)
            sidecar.write_bytes(b"existing sidecar")
            self.run_script("sqlite-health-check", "--database", path, code=2)
            self.assertEqual(sidecar.read_bytes(), b"existing sidecar")
            sidecar.unlink()

    def make_zip(self, names):
        path = self.root / "archive.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in names:
                archive.writestr(name, content)
        return path

    def test_zip_safe_empty_and_no_extraction(self):
        for names in [[], [("folder/a.txt", "hello")]]:
            path = self.make_zip(names)
            before = path.read_bytes()
            report = json.loads(
                self.run_script("zip-safety-audit", "--archive", path).stdout
            )
            self.assertEqual(report["members"], len(names))
            self.assertEqual(report["findings"], [])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(self.root.iterdir()), [path])

    def test_zip_paths_symlink_ratio_and_total_limit(self):
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        path = self.make_zip(
            [
                ("../escape", "bad"),
                ("C:\\evil", "bad"),
                ("/abs", "bad"),
                ("NUL.txt", "bad"),
                ("A.txt", "a"),
                ("a.txt", "b"),
                (link, "../target"),
                ("compressed", "0" * 100_000),
            ]
        )
        report = json.loads(
            self.run_script(
                "zip-safety-audit", "--archive", path, "--max-bytes", "10", code=1
            ).stdout
        )
        reasons = {reason for row in report["findings"] for reason in row["reasons"]}
        self.assertTrue(
            {
                "unsafe-path",
                "nonportable-path",
                "windows-reserved-name",
                "duplicate-path",
                "symlink",
                "expansion-ratio",
                "total-size-limit",
            }
            <= reasons
        )
        self.assertFalse((self.root.parent / "escape").exists())

    def test_zip_corrupt_and_invalid_limit(self):
        path = self.write("bad.zip", "not zip")
        self.run_script("zip-safety-audit", "--archive", path, code=2)
        self.run_script(
            "zip-safety-audit", "--archive", path, "--max-ratio", "0", code=2
        )

    def test_jsonl_coverage_blanks_and_no_values(self):
        path = self.write("data.jsonl", '{"a":"SECRET","b":null}\n\n{"b":2}\n')
        result = self.run_script("jsonl-key-profile", "--input", path)
        report = json.loads(result.stdout)
        self.assertEqual(
            report["keys"],
            {"a": {"present": 1, "missing": 1}, "b": {"present": 2, "missing": 0}},
        )
        self.assertEqual(report["blank_lines"], 1)
        self.assertNotIn("SECRET", result.stdout)

    def test_jsonl_rejects_nonstandard_duplicate_deep_and_invalid_utf8(self):
        path = self.write(
            "bad.jsonl",
            '{"x":NaN}\n{"a":1,"a":2}\n[]\nbad\n'
            + "[" * 2000
            + "0"
            + "]" * 2000
            + "\n",
        )
        with path.open("ab") as stream:
            stream.write(b"\xff\n")
        report = json.loads(
            self.run_script("jsonl-key-profile", "--input", path, code=1).stdout
        )
        self.assertEqual(report["invalid_count"], 6)
        self.assertEqual(report["invalid_lines"], list(range(1, 7)))

    def test_jsonl_empty_limits_and_truncated_findings(self):
        path = self.write("data.jsonl", "")
        self.assertEqual(
            json.loads(self.run_script("jsonl-key-profile", "--input", path).stdout)[
                "records"
            ],
            0,
        )
        path.write_text("{}\n{}\n")
        self.run_script(
            "jsonl-key-profile", "--input", path, "--max-records", "1", code=2
        )
        self.run_script(
            "jsonl-key-profile", "--input", path, "--max-line-bytes", "1", code=2
        )
        self.run_script(
            "jsonl-key-profile", "--input", path, "--max-line-bytes", "0", code=2
        )
        path.write_text("bad\n" * 1001)
        report = json.loads(
            self.run_script("jsonl-key-profile", "--input", path, code=1).stdout
        )
        self.assertTrue(report["truncated"])
        self.assertEqual(len(report["invalid_lines"]), 1000)

    def test_csv_reconcile_quotes_duplicates_and_exact_keys(self):
        left = self.write("left.csv", 'id,value\n"a,b",SECRET\nx,1\nx,2\n')
        right = self.write("right.csv", 'id,value\n"a,b",other\ny,3\n')
        result = self.run_script(
            "csv-key-reconcile", "--left", left, "--right", right, "--key", "id", code=1
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["common"], 1)
        self.assertEqual(report["only_left"], ["x"])
        self.assertEqual(report["only_right"], ["y"])
        self.assertEqual(report["duplicate_left"], ["x"])
        self.assertNotIn("SECRET", result.stdout)

    def test_csv_empty_malformed_missing_key_and_limits(self):
        valid = self.write("right.csv", "id,value\n")
        self.run_script(
            "csv-key-reconcile", "--left", valid, "--right", valid, "--key", "id"
        )
        for data in [
            "",
            "x,value\n1,2\n",
            "id,id\n1,2\n",
            "id,value\n,1\n",
            'id,value\n"unclosed',
            "id,value\n1\n",
        ]:
            with self.subTest(data=data):
                path = self.write("left.csv", data)
                self.run_script(
                    "csv-key-reconcile",
                    "--left",
                    path,
                    "--right",
                    valid,
                    "--key",
                    "id",
                    code=2,
                )
        path = self.write("left.csv", "id,value\n1,2\n2,3\n")
        self.run_script(
            "csv-key-reconcile",
            "--left",
            path,
            "--right",
            valid,
            "--key",
            "id",
            "--max-rows",
            "1",
            code=2,
        )

    def test_csv_bom_multiline_and_utf8(self):
        path = self.write("left.csv", '\ufeffid,value\n"ü\nkey",data\n')
        self.run_script(
            "csv-key-reconcile", "--left", path, "--right", path, "--key", "id"
        )
        path.write_bytes(b"id,value\n\xff,x\n")
        self.run_script(
            "csv-key-reconcile", "--left", path, "--right", path, "--key", "id", code=2
        )

    def lock(self, packages, version=3):
        return self.write(
            "package-lock.json",
            json.dumps({"lockfileVersion": version, "packages": packages}),
        )

    def test_npm_strong_integrity_links_bundles_and_determinism(self):
        integrity = (
            "sha512-" + base64.b64encode(hashlib.sha512(b"fixture").digest()).decode()
        )
        for version in (2, 3):
            path = self.lock(
                {
                    "": {},
                    "node_modules/a": {
                        "resolved": "https://registry.npmjs.org/a/-/a-1.tgz",
                        "integrity": integrity,
                    },
                    "local": {"link": True},
                    "bundled": {"inBundle": True},
                },
                version,
            )
            before = path.read_bytes()
            first = self.run_script("npm-lock-audit", "--lockfile", path).stdout
            self.assertEqual(
                first, self.run_script("npm-lock-audit", "--lockfile", path).stdout
            )
            self.assertEqual(json.loads(first)["checked"], 1)
            self.assertEqual(path.read_bytes(), before)

    def test_npm_flags_insecure_and_lifecycle_metadata_without_leaking_credentials(
        self,
    ):
        path = self.lock(
            {
                "node_modules/a": {
                    "resolved": "http://user:SECRET@localhost/a",
                    "integrity": "sha512-nope",
                    "hasInstallScript": True,
                }
            }
        )
        result = self.run_script("npm-lock-audit", "--lockfile", path, code=1)
        self.assertEqual(
            set(json.loads(result.stdout)["findings"][0]["reasons"]),
            {
                "missing-or-weak-integrity",
                "non-https-or-missing-source",
                "embedded-credentials",
                "lifecycle-script",
            },
        )
        self.assertNotIn("SECRET", result.stdout + result.stderr)

    def test_npm_invalid_formats_empty_and_oversize(self):
        for data in [
            "",
            "null",
            "[]",
            '{"lockfileVersion":1,"packages":{}}',
            '{"lockfileVersion":3,"packages":{"x":null}}',
        ]:
            self.run_script(
                "npm-lock-audit", "--lockfile", self.write("bad.json", data), code=2
            )
        self.run_script("npm-lock-audit", "--lockfile", self.lock({}))
        path = self.root / "large.json"
        with path.open("wb") as file:
            file.truncate(32 * 1024 * 1024 + 1)
        self.run_script("npm-lock-audit", "--lockfile", path, code=2)

    def har(self, entries):
        return self.write(
            "input.har", json.dumps({"log": {"version": "1.2", "entries": entries}})
        )

    def test_har_aggregate_status_timings_and_privacy(self):
        path = self.har(
            [
                {
                    "time": 1200,
                    "request": {
                        "url": "https://SECRET/",
                        "headers": [{"name": "Cookie", "value": "SECRET"}],
                    },
                    "response": {"status": 500, "bodySize": -1},
                    "timings": {"wait": 1100, "ssl": -1},
                },
                {
                    "time": 100,
                    "response": {"status": 200, "bodySize": 42},
                    "timings": {"wait": 80},
                },
            ]
        )
        result = self.run_script("har-timing-summary", "--input", path)
        report = json.loads(result.stdout)
        self.assertEqual(
            (
                report["requests"],
                report["failed"],
                report["slow"],
                report["mean_request_ms"],
            ),
            (2, 1, 1, 650),
        )
        self.assertEqual(report["timing_ms"], {"wait": 1180})
        self.assertEqual(report["known_body_bytes"], 42)
        self.assertNotIn("SECRET", result.stdout + result.stderr)

    def test_har_empty_invalid_entry_and_thresholds(self):
        self.assertEqual(
            json.loads(
                self.run_script("har-timing-summary", "--input", self.har([])).stdout
            )["requests"],
            0,
        )
        for entry in [
            None,
            {},
            {"time": -1},
            {
                "time": 1,
                "response": {"status": 200, "bodySize": 0},
                "timings": {"wait": -2},
            },
        ]:
            self.run_script("har-timing-summary", "--input", self.har([entry]), code=2)
        for threshold in ["0", "NaN", "Infinity", "-1"]:
            self.run_script(
                "har-timing-summary",
                "--input",
                self.har([]),
                "--slow-ms",
                threshold,
                code=2,
            )
        self.run_script(
            "har-timing-summary", "--input", self.write("bad.har", "{}"), code=2
        )


if __name__ == "__main__":
    unittest.main()
