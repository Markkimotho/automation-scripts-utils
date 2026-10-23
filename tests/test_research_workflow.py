"""Test discovery deduplication and promotion gates without network access."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "research_tools", ROOT / "tools/research.py"
)
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


class ResearchWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.inventory = research.read(ROOT / "research/candidates.json")

    def test_inventory_and_acceptance_evidence(self):
        research.validate(self.inventory)

    def test_repeated_import_preserves_completed_reviews(self):
        before = deepcopy(self.inventory)
        self.assertEqual(research.ingest(self.inventory, deepcopy(self.inventory)), 0)
        self.assertEqual(self.inventory, before)

    def test_import_deduplicates_urls_and_rejects_identifier_collisions(self):
        candidate = deepcopy(self.inventory["candidates"][0])
        candidate["id"] = "another-name"
        candidate["status"] = "discovered"
        self.assertEqual(
            research.ingest(self.inventory, {"candidates": [candidate]}), 0
        )
        candidate["id"] = self.inventory["candidates"][0]["id"]
        candidate["source_url"] = "https://example.org/another-source"
        with self.assertRaisesRegex(ValueError, "collision"):
            research.ingest(self.inventory, {"candidates": [candidate]})

    def test_new_import_cannot_self_promote(self):
        candidate = deepcopy(self.inventory["candidates"][0])
        candidate.update(id="new-candidate", source_url="https://example.org/reference")
        with self.assertRaisesRegex(ValueError, "discovered"):
            research.ingest(self.inventory, {"candidates": [candidate]})
        candidate["status"] = "discovered"
        self.assertEqual(
            research.ingest(self.inventory, {"candidates": [candidate, candidate]}), 1
        )

    def test_copied_code_requires_license_and_pinned_revision(self):
        candidate = self.inventory["candidates"][0]
        candidate.update(reuse="copied", source_revision=None)
        with self.assertRaisesRegex(ValueError, "pinned revision"):
            research.validate(self.inventory)

    def test_catalog_cannot_reference_unaccepted_candidate(self):
        self.inventory["candidates"][0]["status"] = "adapted"
        with self.assertRaisesRegex(ValueError, "not accepted"):
            research.validate(self.inventory)

    def test_evidence_path_traversal_is_rejected(self):
        self.inventory["candidates"][0]["test_evidence"] = "../outside.json"
        with self.assertRaisesRegex(ValueError, "unsafe evidence path"):
            research.validate(self.inventory)

    def test_stale_evidence_and_unverified_platform_claim_are_rejected(self):
        original_read = research.read
        evidence_path = self.inventory["candidates"][0]["test_evidence"]
        for change, message in [("hash", "stale"), ("platform", "Untested platform")]:
            evidence = deepcopy(original_read(ROOT / evidence_path))
            if change == "hash":
                evidence["sha256"][next(iter(evidence["sha256"]))] = "0" * 64
            else:
                evidence["verified_platforms"] = []
            with patch.object(
                research,
                "read",
                side_effect=lambda path: (
                    evidence if path == ROOT / evidence_path else original_read(path)
                ),
            ):
                with (
                    self.subTest(change=change),
                    self.assertRaisesRegex(ValueError, message),
                ):
                    research.validate(self.inventory)

    def test_new_metadata_requires_quality_fields(self):
        schema = research.read(ROOT / "catalog/schema.json")
        entry = deepcopy(
            next(
                x
                for x in research.read(ROOT / "catalog/scripts.json")["scripts"]
                if "provenance_ref" in x
            )
        )
        for field in [
            "provenance_ref",
            "maintainer",
            "runtime_requirements",
            "exit_codes",
            "test_status",
            "compatibility_notes",
            "usage_example",
        ]:
            broken = deepcopy(entry)
            del broken[field]
            with (
                self.subTest(field=field),
                self.assertRaises(jsonschema.ValidationError),
            ):
                jsonschema.validate({"schema_version": 1, "scripts": [broken]}, schema)

    def test_generated_docs_match_catalog_and_script_readmes(self):
        spec = importlib.util.spec_from_file_location(
            "directory_generator", ROOT / "tools/generate_directory.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for path, content in module.generated_files().items():
            with self.subTest(path=path):
                self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
