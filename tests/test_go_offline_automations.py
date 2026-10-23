"""Native Go suites and real catalog execution, with no network dependencies."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    "pem-expiry-report": "security-compliance/certificates",
    "cidr-overlap-report": "networking-monitoring/ip-addressing",
    "checksum-manifest-verify": "backup-recovery/integrity",
}


class GoOfflineAutomations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("go"):
            if os.environ.get("AUTOMATION_REQUIRE_GO") == "1":
                raise RuntimeError("Go >=1.24 is required for acceptance")
            raise unittest.SkipTest("Go unavailable; not acceptance evidence")
        cls.environment = os.environ.copy()
        cls.environment.update(GOTOOLCHAIN="local", GOPROXY="off", GOWORK="off")
        # An isolated test catalog exercises the runner on every CI OS before
        # the product advertises platform compatibility for these entries.
        fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(fixture.cleanup)
        fixture_root = Path(fixture.name)
        identifiers = {*ENTRIES, "tcp-connect-check", "jsonl-key-profile"}
        entries = [
            entry
            for entry in json.loads(
                (ROOT / "catalog/scripts.json").read_text(encoding="utf-8")
            )["scripts"]
            if entry["id"] in identifiers
        ]
        if len(entries) != len(identifiers):
            raise RuntimeError("Go batch registrations are missing")
        for entry in entries:
            destination = fixture_root / entry["entrypoint"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / entry["entrypoint"], destination)
            entry["platforms"] = ["macos", "linux", "windows"]
            if entry["language"] == "python":
                entry["dependencies"] = [sys.executable]
        (fixture_root / "catalog").mkdir()
        (fixture_root / "catalog/scripts.json").write_text(
            json.dumps({"schema_version": 1, "scripts": entries}), encoding="utf-8"
        )
        cls.environment["AUTOMATION_ROOT"] = str(fixture_root)

    def invoke(self, *args, code=0):
        result = subprocess.run(
            [sys.executable, str(ROOT / "cli/automation"), *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
            env=self.environment,
        )
        self.assertEqual(result.returncode, code, result.stderr)
        return result

    def test_native_suites(self):
        for identifier, directory in ENTRIES.items():
            with self.subTest(script=identifier):
                path = ROOT / "scripts" / directory / identifier
                result = subprocess.run(
                    [
                        "go",
                        "test",
                        "-vet=all",
                        "-count=1",
                        str(path / "script.go"),
                        str(path / "script_test.go"),
                    ],
                    env=self.environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=180,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_go_source_formatting(self):
        paths = [
            str(ROOT / "scripts" / directory / identifier / name)
            for identifier, directory in ENTRIES.items()
            for name in ("script.go", "script_test.go")
        ]
        for path in paths:
            # Compare normalized newlines so Windows checkout CRLF is harmless.
            source = Path(path).read_text(encoding="utf-8")
            result = subprocess.run(
                ["gofmt"],
                input=source,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
                env=self.environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, source, path + " requires gofmt")

    def test_cli_cidr_valid_findings_and_invalid_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "networks.txt"
            path.write_text("192.0.2.0/24\n", encoding="utf-8")
            result = self.invoke(
                "run", "cidr-overlap-report", "--param", "input=" + str(path)
            )
            self.assertEqual(json.loads(result.stdout)["overlap_count"], 0)
            path.write_text("10.0.0.0/8\n10.1.0.0/16\n", encoding="utf-8")
            self.invoke("run", "cidr-overlap-report", "--", "--input", path, code=1)
            path.write_text("invalid", encoding="utf-8")
            result = self.invoke(
                "run", "cidr-overlap-report", "--", "--input", path, code=2
            )
            self.assertEqual(result.stdout, "")

    def test_cli_checksum_roundtrip_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "image.png"
            payload.write_bytes(b"fixture")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    [
                        {
                            "path": "image.png",
                            "bytes": 7,
                            "sha256": hashlib.sha256(b"fixture").hexdigest(),
                        }
                    ]
                ),
                encoding="utf-8",
            )
            arguments = [
                "run",
                "checksum-manifest-verify",
                "--param",
                "root=" + str(root),
                "--param",
                "manifest=" + str(manifest),
            ]
            report = json.loads(self.invoke(*arguments).stdout)
            self.assertEqual(report, {"verified": 1, "findings": []})
            payload.write_bytes(b"changed")
            self.invoke(*arguments, code=1)
            manifest.write_text("null", encoding="utf-8")
            self.invoke(*arguments, code=2)

    def test_cli_pem_help_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.pem"
            path.write_text("untrusted content", encoding="utf-8")
            self.invoke("run", "pem-expiry-report", "--", "--help")
            self.invoke(
                "run", "pem-expiry-report", "--param", "input=" + str(path), code=2
            )
            preview = self.invoke(
                "run", "pem-expiry-report", "--dry-run", "--param", "input=" + str(path)
            )
            self.assertIn("go build", preview.stdout)
            self.assertIn("<temporary executable>", preview.stdout)

    def test_existing_go_script_help(self):
        self.invoke("run", "tcp-connect-check", "--", "-h")

    def test_python_passthrough_and_named_validation(self):
        self.invoke("run", "jsonl-key-profile", "--", "--help")
        self.invoke("run", "jsonl-key-profile", "--dry-run", code=2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"id":1}\n', encoding="utf-8")
            report = json.loads(
                self.invoke("run", "jsonl-key-profile", "--", "--input", path).stdout
            )
            self.assertEqual(report["records"], 1)
            self.invoke(
                "run",
                "jsonl-key-profile",
                "--param",
                "input=" + str(path),
                "--",
                "--max-line-bytes",
                "1000",
            )
            self.invoke(
                "run",
                "jsonl-key-profile",
                "--param",
                "input=" + str(path),
                "--param",
                "max_line_bytes=bad",
                code=2,
            )

    def test_go_build_failure_is_an_execution_error(self):
        path = (
            Path(self.environment["AUTOMATION_ROOT"])
            / "scripts/networking-monitoring/ip-addressing/cidr-overlap-report/script.go"
        )
        original = path.read_bytes()
        try:
            path.write_text("package main\nthis is invalid Go\n", encoding="utf-8")
            result = self.invoke("run", "cidr-overlap-report", "--", "--help", code=2)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr)
        finally:
            path.write_bytes(original)

    def test_missing_go_compiler_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(self.environment, PATH=directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "cli/automation"),
                    "run",
                    "pem-expiry-report",
                    "--",
                    "--help",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
                env=environment,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("Missing dependencies: go", result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
