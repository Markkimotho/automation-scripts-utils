"""Functional fixtures for newly added Python automations."""
from __future__ import annotations

import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "folder-inventory": "files-documents/folders",
    "csv-dataset-profile": "ai-ml-llmops/datasets",
    "file-permission-audit": "security-compliance/filesystem",
    "invoice-due-report": "business-productivity/finance",
    "eml-headers-report": "messaging-notifications/email",
    "incremental-file-copy": "backup-recovery/filesystem",
    "json-batch-validate": "testing-qa/json",
    "organize-downloads": "desktop-personal/organizing",
}

def execute(identifier, *args):
    path = ROOT / "scripts" / SCRIPTS[identifier] / identifier / "script.py"
    return subprocess.run([sys.executable, str(path), *map(str, args)], capture_output=True, text=True)

class PythonAutomations(unittest.TestCase):
    def test_file_inventory_and_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.txt").write_text("abc")
            result = execute("folder-inventory", "--root", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(result.stdout)
            self.assertEqual([(x["path"], x["bytes"]) for x in rows], [("a.txt", 3)])

    def test_dataset_missing_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.csv"
            path.write_text("a,b\n1,\n,2\n")
            result = execute("csv-dataset-profile", path)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["missing_by_column"], {"a": 1, "b": 1})

    @unittest.skipIf(sys.platform == "win32", "POSIX mode bits differ on Windows")
    def test_permission_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "world.txt"
            path.write_text("x")
            path.chmod(0o666)
            result = execute("file-permission-audit", "--root", folder)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["world_writable_files"], ["world.txt"])

    def test_invoice_due_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invoices.csv"
            path.write_text("invoice_id,due_date,amount,paid\nA,2025-01-01,12.50,no\nB,2025-01-01,7,yes\n")
            result = execute("invoice-due-report", path, "--as-of", "2025-01-02")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["total_overdue"], "12.50")

    def test_local_eml_headers(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "m.eml").write_bytes(b"From: me@example.org\nTo: you@example.org\nSubject: Hello\n\nBody\n")
            result = execute("eml-headers-report", folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)[0]["subject"], "Hello")

    def test_incremental_backup_preview_and_apply(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, dst = root / "src", root / "dst"
            src.mkdir()
            (src / "a.txt").write_text("backup")
            preview = execute("incremental-file-copy", "--source", src, "--destination", dst)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertFalse(dst.exists())
            applied = execute("incremental-file-copy", "--source", src, "--destination", dst, "--apply")
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual((dst / "a.txt").read_text(), "backup")

    def test_json_validation_finds_bad_files(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "good.json").write_text('{"x":1}')
            (Path(folder) / "bad.json").write_text('{"x":')
            result = execute("json-batch-validate", folder)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["invalid"], 1)

    def test_organizer_preview_and_apply(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "report.pdf"
            file.write_bytes(b"%PDF")
            preview = execute("organize-downloads", "--directory", folder)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertTrue(file.exists())
            apply = execute("organize-downloads", "--directory", folder, "--apply")
            self.assertEqual(apply.returncode, 0, apply.stderr)
            self.assertEqual((Path(folder) / "pdf" / "report.pdf").read_bytes(), b"%PDF")

if __name__ == "__main__":
    unittest.main()
