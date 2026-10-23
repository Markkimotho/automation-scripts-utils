"""Catalog integrity and CLI safety tests; no network or cloud credentials needed."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cli" / "automation"
CATALOG = ROOT / "catalog" / "scripts.json"


class CatalogIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts = json.loads(CATALOG.read_text(encoding="utf-8"))["scripts"]

    def test_unique_ids_and_entries(self):
        ids = [s["id"] for s in self.scripts]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 34)

    def test_metadata_matches_files(self):
        for script in self.scripts:
            with self.subTest(script=script["id"]):
                path = ROOT / script["entrypoint"]
                self.assertTrue(path.is_file(), path)
                self.assertTrue(path.resolve().is_relative_to((ROOT / "scripts").resolve()))
                self.assertEqual(path.parent.name, script["id"])
                metadata = (path.parent / "metadata.yaml").read_text(encoding="utf-8")
                self.assertIn("id: " + script["id"], metadata)
                self.assertIn("entrypoint: " + script["entrypoint"], metadata)
                self.assertTrue((path.parent / "README.md").is_file())
                self.assertTrue(script["description"])
                self.assertTrue(script["platforms"])
                self.assertTrue(script["dependencies"])
                self.assertTrue(script["tags"])
                self.assertTrue(script["permissions"])
                self.assertIn(script["language"], {"python", "bash", "powershell", "javascript", "typescript", "go", "ruby"})
                self.assertEqual(path.parts[1], script["category"])


class CLITests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=ROOT)

    def test_list_category(self):
        result = self.invoke("list", "--category", "developer-tools")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gh-merge-pr", result.stdout)

    def test_search(self):
        result = self.invoke("search", "git")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("git-sync", result.stdout)

    def test_info(self):
        result = self.invoke("info", "data-convert")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], "data-convert")

    def test_dry_run_does_not_execute(self):
        result = self.invoke("run", "port-kill", "--dry-run", "--", "9999")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PREVIEW ONLY", result.stdout)

    def test_invalid_parameters_rejected(self):
        result = self.invoke("run", "port-kill", "--dry-run", "--param", "unknown=1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown or repeated parameter", result.stderr)

    def test_missing_script_rejected(self):
        self.assertEqual(self.invoke("run", "does-not-exist", "--dry-run").returncode, 2)


if __name__ == "__main__":
    unittest.main()
