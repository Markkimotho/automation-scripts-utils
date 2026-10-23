"""Offline fixtures for web-researched backup, configuration and office tools."""

from contextlib import closing
from email.message import EmailMessage
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    "sqlite-online-backup": ("python", "backup-recovery/sqlite", "py"),
    "git-bundle-backup": ("bash", "backup-recovery/git", "sh"),
    "toml-settings-diff": ("python", "developer-tools/configuration", "py"),
    "openapi-operation-inventory": ("javascript", "api-integrations/openapi", "js"),
    "csv-formula-audit": ("ruby", "security-compliance/csv", "rb"),
    "eml-attachment-extract": ("python", "messaging-notifications/email", "py"),
}


def entrypoint(identifier):
    _, directory, suffix = ENTRIES[identifier]
    return ROOT / "scripts" / directory / identifier / ("script." + suffix)


class WebAdaptedAutomations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("AUTOMATION_REQUIRE_WEB_RUNTIMES") == "1":
            for runtime in ("node", "ruby", "git"):
                if not shutil.which(runtime):
                    raise RuntimeError(
                        "Required acceptance runtime is missing: " + runtime
                    )

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = os.environ.copy()
        self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def execute(self, identifier, *args, code=0, environment=None):
        language = ENTRIES[identifier][0]
        runtime = {
            "python": sys.executable,
            "bash": shutil.which("bash"),
            "javascript": shutil.which("node"),
            "ruby": shutil.which("ruby"),
        }[language]
        if runtime is None:
            self.skipTest(language + " runtime unavailable; not acceptance evidence")
        result = subprocess.run(
            [runtime, str(entrypoint(identifier)), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            env=environment or self.environment,
        )
        self.assertEqual(result.returncode, code, result.stderr)
        if code == 2:
            self.assertEqual(
                result.stdout, "", "invalid input must not emit a success report"
            )
        return result

    def write(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def database(self):
        path = self.root / "source ü.db"
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE data(value TEXT)")
            db.execute("INSERT INTO data VALUES ('fixture')")
        return path

    def test_help_and_missing_arguments(self):
        for identifier in ENTRIES:
            if identifier == "git-bundle-backup" and os.name == "nt":
                continue
            with self.subTest(script=identifier):
                result = self.execute(identifier, "--help")
                self.assertTrue(result.stdout or result.stderr)
                self.execute(identifier, code=2)

    def test_missing_nonregular_and_oversized_inputs(self):
        missing = self.root / "missing"
        for identifier in ("openapi-operation-inventory", "csv-formula-audit"):
            self.execute(identifier, "--input", missing, code=2)
            self.execute(identifier, "--input", self.root, code=2)
        self.execute(
            "sqlite-online-backup",
            "--source",
            missing,
            "--output",
            self.root / "backup.db",
            code=2,
        )
        self.execute(
            "eml-attachment-extract",
            "--input",
            missing,
            "--output",
            self.root / "attachments",
            code=2,
        )
        large = self.root / "large"
        with large.open("wb") as stream:
            stream.truncate((16 << 20) + 1)
        self.execute("openapi-operation-inventory", "--input", large, code=2)
        self.execute("csv-formula-audit", "--input", large, code=2)
        if os.name != "nt":
            fifo = self.root / "fifo"
            os.mkfifo(fifo)
            self.execute("openapi-operation-inventory", "--input", fifo, code=2)
            self.execute("csv-formula-audit", "--input", fifo, code=2)

    def test_sqlite_preview_apply_and_standalone_snapshot(self):
        source = self.database()
        output = self.root / "backup.db"
        before = source.read_bytes()
        result = self.execute(
            "sqlite-online-backup", "--source", source, "--output", output
        )
        self.assertFalse(json.loads(result.stdout)["apply"])
        self.assertFalse(output.exists())
        self.execute(
            "sqlite-online-backup", "--source", source, "--output", output, "--apply"
        )
        with closing(
            sqlite3.connect(output.as_uri() + "?mode=ro&immutable=1", uri=True)
        ) as db:
            self.assertEqual(
                db.execute("SELECT value FROM data").fetchall(), [("fixture",)]
            )
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse(list(self.root.glob(".sqlite-backup-*")))

    def test_sqlite_wal_content_is_included(self):
        source = self.root / "wal.db"
        with closing(sqlite3.connect(source)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA wal_autocheckpoint=0")
            db.execute("CREATE TABLE data(value)")
            db.execute("INSERT INTO data VALUES (42)")
            db.commit()
            self.assertTrue(Path(str(source) + "-wal").exists())
            output = self.root / "snapshot.db"
            self.execute(
                "sqlite-online-backup",
                "--source",
                source,
                "--output",
                output,
                "--apply",
            )
            with closing(
                sqlite3.connect(output.as_uri() + "?mode=ro&immutable=1", uri=True)
            ) as copied:
                self.assertEqual(
                    copied.execute("SELECT value FROM data").fetchall(), [(42,)]
                )

    def test_sqlite_refuses_existing_and_symlink_outputs(self):
        source = self.database()
        output = self.write("backup.db", "DO NOT REPLACE")
        self.execute(
            "sqlite-online-backup",
            "--source",
            source,
            "--output",
            output,
            "--apply",
            code=2,
        )
        self.assertEqual(output.read_text(), "DO NOT REPLACE")
        self.execute(
            "sqlite-online-backup",
            "--source",
            source,
            "--output",
            source,
            "--apply",
            code=2,
        )
        if os.name != "nt":
            linked = self.root / "linked.db"
            linked.symlink_to(source)
            self.execute(
                "sqlite-online-backup",
                "--source",
                source,
                "--output",
                linked,
                "--apply",
                code=2,
            )
            self.assertTrue(linked.is_symlink())

    def test_sqlite_corruption_limits_and_stage_cleanup(self):
        output = self.root / "snapshot.db"
        source = self.write("invalid.db", "not sqlite")
        self.execute(
            "sqlite-online-backup",
            "--source",
            source,
            "--output",
            output,
            "--apply",
            code=2,
        )
        source = self.database()
        self.execute(
            "sqlite-online-backup",
            "--source",
            source,
            "--output",
            output,
            "--apply",
            "--max-bytes",
            "1",
            code=2,
        )
        for timeout in ("0", "nan", "inf", "301"):
            self.execute(
                "sqlite-online-backup",
                "--source",
                source,
                "--output",
                output,
                "--timeout",
                timeout,
                code=2,
            )
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob(".sqlite-backup-*")))

    def test_sqlite_controlled_deadline_and_publication_collision(self):
        source = self.database()
        output = self.root / "backup.db"
        spec = importlib.util.spec_from_file_location(
            "online_backup", entrypoint("sqlite-online-backup")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        arguments = [
            "backup",
            "--source",
            str(source),
            "--output",
            str(output),
            "--apply",
        ]
        with (
            patch.object(sys, "argv", arguments),
            patch.object(module.time, "monotonic", side_effect=[0, 100]),
        ):
            self.assertEqual(module.main(), 2)
        self.assertFalse(output.exists())

        def collide(staged, destination):
            destination.write_text("WINNER", encoding="utf-8")
            raise FileExistsError

        with (
            patch.object(sys, "argv", arguments),
            patch.object(module.os, "link", side_effect=collide),
        ):
            self.assertEqual(module.main(), 2)
        self.assertEqual(output.read_text(), "WINNER")
        self.assertFalse(list(self.root.glob(".sqlite-backup-*")))

    def test_toml_diff_omits_values_and_distinguishes_key_paths(self):
        left = self.write("left.toml", 'secret="PRIVATE_ONE"\n"a.b"=1\n[a]\nb=2\n')
        right = self.write(
            "right.toml", 'secret="PRIVATE_TWO"\n"a.b"=2\nnew=true\n[a]\nb=2\n'
        )
        result = self.execute(
            "toml-settings-diff", "--left", left, "--right", right, code=1
        )
        report = json.loads(result.stdout)
        self.assertEqual(
            report["changes"],
            [
                {"path": ["a.b"], "change": "changed"},
                {"path": ["new"], "change": "added"},
                {"path": ["secret"], "change": "changed"},
            ],
        )
        self.assertNotIn("PRIVATE", result.stdout + result.stderr)

    def test_toml_semantic_equality_nan_arrays_and_types(self):
        left = self.write("left.toml", "x=nan\ny=[nan,1.00]\nz=2030-01-01T00:00:00Z\n")
        right = self.write(
            "right.toml", "z=2030-01-01T03:00:00+03:00\ny=[nan,1.0]\nx=nan\n"
        )
        self.execute("toml-settings-diff", "--left", left, "--right", right)
        left.write_text("x=[true]\n", encoding="utf-8")
        right.write_text("x=[1]\n", encoding="utf-8")
        self.execute("toml-settings-diff", "--left", left, "--right", right, code=1)

    def test_toml_empty_invalid_missing_and_oversize(self):
        path = self.write("empty.toml", "")
        self.execute("toml-settings-diff", "--left", path, "--right", path)
        for data in ['secret = "SECRET_BAD', "x=1\nx=2", "x=1e999999999999999999999"]:
            invalid = self.write("bad.toml", data)
            result = self.execute(
                "toml-settings-diff", "--left", invalid, "--right", path, code=2
            )
            self.assertNotIn("SECRET_BAD", result.stderr)
        self.execute(
            "toml-settings-diff",
            "--left",
            self.root / "missing",
            "--right",
            path,
            code=2,
        )
        path.write_bytes(b" " * ((2 << 20) + 1))
        self.execute("toml-settings-diff", "--left", path, "--right", path, code=2)

    def openapi(self, paths, **kwargs):
        return self.write(
            "openapi.json", json.dumps({"openapi": "3.1.0", "paths": paths, **kwargs})
        )

    def test_openapi_security_inheritance_and_overrides(self):
        path = self.openapi(
            {
                "/secured": {"get": {"operationId": "secured"}},
                "/anonymous": {"post": {"operationId": "anonymous", "security": []}},
                "/optional": {
                    "get": {
                        "operationId": "optional",
                        "security": [{"apiKey": []}, {}],
                        "deprecated": True,
                    }
                },
            },
            security=[{"apiKey": []}],
        )
        report = json.loads(
            self.execute("openapi-operation-inventory", "--input", path).stdout
        )
        rows = {row["path"]: row for row in report["operations"]}
        self.assertFalse(rows["/secured"]["anonymous_allowed_by_spec"])
        self.assertTrue(rows["/anonymous"]["anonymous_allowed_by_spec"])
        self.assertTrue(rows["/optional"]["anonymous_allowed_by_spec"])
        self.assertTrue(rows["/optional"]["deprecated"])

    def test_openapi_duplicate_missing_ids_and_refs(self):
        path = self.openapi(
            {
                "/a": {"get": {"operationId": "same"}, "post": {}},
                "/b": {"get": {"operationId": "same"}},
                "/external": {"$ref": "https://example.invalid/private-spec"},
            }
        )
        report = json.loads(
            self.execute("openapi-operation-inventory", "--input", path, code=1).stdout
        )
        self.assertEqual(
            {row["reason"] for row in report["findings"]},
            {"missing-operation-id", "duplicate-operation-id"},
        )
        self.assertEqual(report["unresolved_path_refs"], ["/external"])

    def test_openapi_invalid_types_utf8_and_empty_paths(self):
        path = self.openapi({})
        self.execute("openapi-operation-inventory", "--input", path)
        for content in [
            "null",
            "[]",
            '{"openapi":"3.2.0","paths":{}}',
            '{"openapi":"3.1.0","paths":{"bad":{}}}',
            '{"openapi":"3.1.0","paths":{},"security":[null]}',
        ]:
            path.write_text(content, encoding="utf-8")
            self.execute("openapi-operation-inventory", "--input", path, code=2)
        path.write_bytes(b"\xff")
        self.execute("openapi-operation-inventory", "--input", path, code=2)

    def test_openapi_operation_limit(self):
        path = self.openapi(
            {
                "/path" + str(index): {"get": {"operationId": str(index)}}
                for index in range(10001)
            }
        )
        self.execute("openapi-operation-inventory", "--input", path, code=2)

    def test_csv_formula_audit_quotes_unicode_and_no_values(self):
        path = self.write(
            "data.csv",
            'name,value\nSECRET,"=1+1"\n"a,b",＋2\nnormal,\ttext\nnormal, -12\n',
        )
        result = self.execute("csv-formula-audit", "--input", path, code=1)
        report = json.loads(result.stdout)
        self.assertEqual(report["finding_count"], 4)
        self.assertEqual(
            [(item["row"], item["column"]) for item in report["findings"]],
            [(2, 2), (3, 2), (4, 2), (5, 2)],
        )
        self.assertNotIn("SECRET", result.stdout + result.stderr)

    def test_csv_empty_clean_invalid_and_truncation(self):
        path = self.write("data.csv", "")
        self.execute("csv-formula-audit", "--input", path)
        path.write_text("name,value\nAlice,42\n", encoding="utf-8")
        self.execute("csv-formula-audit", "--input", path)
        path.write_text('"unclosed', encoding="utf-8")
        self.execute("csv-formula-audit", "--input", path, code=2)
        path.write_bytes(b"name,value\n\xff,1\n")
        self.execute("csv-formula-audit", "--input", path, code=2)
        path.write_text("=1\n" * 1001, encoding="utf-8")
        report = json.loads(
            self.execute("csv-formula-audit", "--input", path, code=1).stdout
        )
        self.assertEqual(report["finding_count"], 1001)
        self.assertTrue(report["truncated"])
        self.assertEqual(len(report["findings"]), 1000)

    def eml(self, *names):
        message = EmailMessage()
        message["From"] = "fixture@example.invalid"
        message.set_content("Private body, not part of attachment output")
        for name in names:
            message.add_attachment(
                b"PAYLOAD",
                maintype="application",
                subtype="octet-stream",
                filename=name,
            )
        path = self.root / "mail.eml"
        path.write_bytes(message.as_bytes())
        return path

    def test_eml_preview_extract_sanitized_paths_and_privacy(self):
        source = self.eml("../../escape.txt", "C:\\Windows\\file.txt")
        output = self.root / "attachments"
        before = source.read_bytes()
        preview = self.execute(
            "eml-attachment-extract", "--input", source, "--output", output
        )
        self.assertFalse(output.exists())
        self.assertNotIn("PAYLOAD", preview.stdout)
        self.assertNotIn("Private body", preview.stdout)
        result = self.execute(
            "eml-attachment-extract", "--input", source, "--output", output, "--apply"
        )
        names = [row["name"] for row in json.loads(result.stdout)["files"]]
        self.assertEqual(
            names, ["attachment-0001-escape.txt", "attachment-0002-file.txt"]
        )
        self.assertEqual(sorted(path.name for path in output.iterdir()), names)
        for path in output.iterdir():
            self.assertEqual(path.read_bytes(), b"PAYLOAD")
        self.assertEqual(source.read_bytes(), before)

    def test_eml_collision_empty_and_corrupt_encoding(self):
        source = self.eml("file.txt")
        output = self.root / "attachments"
        self.execute(
            "eml-attachment-extract", "--input", source, "--output", output, "--apply"
        )
        self.execute(
            "eml-attachment-extract",
            "--input",
            source,
            "--output",
            output,
            "--apply",
            code=2,
        )
        self.assertEqual((output / "attachment-0001-file.txt").read_bytes(), b"PAYLOAD")
        empty = self.eml()
        self.execute(
            "eml-attachment-extract",
            "--input",
            empty,
            "--output",
            self.root / "unused",
            "--apply",
        )
        self.assertFalse((self.root / "unused").exists())
        corrupt = self.write(
            "bad.eml",
            'MIME-Version: 1.0\nContent-Type: application/octet-stream\nContent-Disposition: attachment; filename="x"\nContent-Transfer-Encoding: base64\n\n%%%%\n',
        )
        self.execute(
            "eml-attachment-extract",
            "--input",
            corrupt,
            "--output",
            self.root / "new",
            "--apply",
            code=2,
        )
        self.assertFalse((self.root / "new").exists())

    def test_eml_oversize(self):
        large = self.root / "large.eml"
        with large.open("wb") as stream:
            stream.truncate((16 << 20) + 1)
        self.execute(
            "eml-attachment-extract",
            "--input",
            large,
            "--output",
            self.root / "unused",
            code=2,
        )

    def test_eml_mime_structure_budget_and_symlink_output(self):
        source = self.write("many.eml", "--boundary\n" * 2001)
        output = self.root / "attachments"
        self.execute(
            "eml-attachment-extract",
            "--input",
            source,
            "--output",
            output,
            "--apply",
            code=2,
        )
        self.assertFalse(output.exists())
        if os.name != "nt":
            target = self.root / "target"
            target.mkdir()
            output.symlink_to(target, target_is_directory=True)
            source = self.eml("file.txt")
            self.execute(
                "eml-attachment-extract",
                "--input",
                source,
                "--output",
                output,
                "--apply",
                code=2,
            )
            self.assertEqual(list(target.iterdir()), [])

    def test_eml_permission_failure_preserves_completed_files(self):
        source = self.eml("one.txt", "two.txt")
        output = self.root / "attachments"
        spec = importlib.util.spec_from_file_location(
            "eml_extractor", entrypoint("eml-attachment-extract")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_link = os.link
        calls = []

        def fail_second(staged, destination):
            calls.append(str(destination))
            if len(calls) == 2:
                raise PermissionError
            original_link(staged, destination)

        args = ["extract", "--input", str(source), "--output", str(output), "--apply"]
        with (
            patch.object(sys, "argv", args),
            patch.object(module.os, "link", side_effect=fail_second),
        ):
            self.assertEqual(module.main(), 2)
        self.assertEqual(
            [path.name for path in output.iterdir()], ["attachment-0001-one.txt"]
        )
        self.assertEqual((output / "attachment-0001-one.txt").read_bytes(), b"PAYLOAD")

    def test_eml_embedded_message_is_rejected(self):
        large = self.root / "embedded.eml"
        message = EmailMessage()
        message.set_content("outer")
        inner = EmailMessage()
        inner.set_content("inner")
        message.add_attachment(inner, filename="embedded.eml")
        large.write_bytes(message.as_bytes())
        self.execute(
            "eml-attachment-extract",
            "--input",
            large,
            "--output",
            self.root / "unused",
            code=2,
        )

    def repository(self):
        path = self.root / "repo with spaces"
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(path)],
            env=self.environment,
            check=True,
        )
        (path / "tracked").write_text("committed", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(path), "add", "tracked"], env=self.environment, check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            env=self.environment,
            check=True,
        )
        return path

    @unittest.skipIf(os.name == "nt", "Bash backup declares POSIX platforms only")
    def test_git_bundle_preview_apply_and_restore(self):
        repository = self.repository()
        output = self.root / "backup with spaces.bundle"
        (repository / "untracked").write_text("not included", encoding="utf-8")
        self.execute(
            "git-bundle-backup", "--repository", repository, "--output", output
        )
        self.assertFalse(output.exists())
        self.execute(
            "git-bundle-backup",
            "--repository",
            repository,
            "--output",
            output,
            "--apply",
        )
        restored = self.root / "restored"
        subprocess.run(
            ["git", "clone", "-q", str(output), str(restored)],
            env=self.environment,
            check=True,
        )
        self.assertEqual((restored / "tracked").read_text(), "committed")
        self.assertFalse((restored / "untracked").exists())
        before = output.read_bytes()
        self.execute(
            "git-bundle-backup",
            "--repository",
            repository,
            "--output",
            output,
            "--apply",
            code=2,
        )
        self.assertEqual(output.read_bytes(), before)
        self.assertFalse(list(self.root.glob(".git-bundle-*")))

    @unittest.skipIf(os.name == "nt", "Bash backup declares POSIX platforms only")
    def test_git_bundle_invalid_empty_and_missing_dependency(self):
        output = self.root / "backup.bundle"
        self.execute(
            "git-bundle-backup", "--repository", self.root, "--output", output, code=2
        )
        empty = self.root / "empty"
        subprocess.run(
            ["git", "init", "-q", str(empty)], check=True, env=self.environment
        )
        self.execute(
            "git-bundle-backup", "--repository", empty, "--output", output, code=2
        )
        repository = self.repository()
        shallow = self.root / "shallow"
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", repository.as_uri(), str(shallow)],
            env=self.environment,
            check=True,
        )
        self.execute(
            "git-bundle-backup",
            "--repository",
            shallow,
            "--output",
            output,
            "--apply",
            code=2,
        )
        self.execute(
            "git-bundle-backup",
            "--repository",
            repository,
            "--output",
            output,
            "--apply",
            "--dry-run",
            code=2,
        )
        environment = dict(self.environment, PATH=str(empty))
        self.execute(
            "git-bundle-backup",
            "--repository",
            repository,
            "--output",
            output,
            environment=environment,
            code=2,
        )

    @unittest.skipIf(os.name == "nt", "Bash backup declares POSIX platforms only")
    def test_git_bundle_directory_race_cannot_redirect_publication(self):
        repository = self.repository()
        output = self.root / "racing.bundle"
        fakebin = self.root / "fakebin"
        fakebin.mkdir()
        wrapper = fakebin / "python3"
        wrapper.write_text(
            '#!/bin/bash\nmkdir -- "$3"\nexec '
            + shlex.quote(sys.executable)
            + ' "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o700)
        environment = dict(
            self.environment, PATH=str(fakebin) + os.pathsep + self.environment["PATH"]
        )
        self.execute(
            "git-bundle-backup",
            "--repository",
            repository,
            "--output",
            output,
            "--apply",
            environment=environment,
            code=2,
        )
        self.assertTrue(output.is_dir())
        self.assertEqual(list(output.iterdir()), [])
        self.assertFalse(list(self.root.glob(".git-bundle-*")))


if __name__ == "__main__":
    unittest.main()
