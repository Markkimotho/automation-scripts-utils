#!/usr/bin/env python3
"""Validate catalog schema, exact metadata mirrors, and category targets."""
from pathlib import Path
import json
import sys

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / "catalog/scripts.json").read_text(encoding="utf-8"))
schema = json.loads((ROOT / "catalog/schema.json").read_text(encoding="utf-8"))
jsonschema.validate(instance=catalog, schema=schema)
categories = yaml.safe_load((ROOT / "catalog/categories.yaml").read_text(encoding="utf-8"))["categories"]
targets = {category["id"]: category["target"] for category in categories}
assert len(targets) == 16 and sum(targets.values()) == 1200, "Roadmap must have the expected 16 categories and 1,200 targets"
ids = set()
for entry in catalog["scripts"]:
    identifier = entry["id"]
    assert identifier not in ids, f"Duplicate ID: {identifier}"
    ids.add(identifier)
    assert entry["category"] in targets, f"Unknown category for {identifier}"
    impl = ROOT / entry["entrypoint"]
    assert impl.is_file() and impl.resolve().is_relative_to((ROOT / "scripts").resolve()), f"Missing or invalid entrypoint: {identifier}"
    meta_path = impl.parent / "metadata.yaml"
    metadata = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    for key, value in entry.items():
        assert metadata.get(key) == value, f"Metadata mismatch {identifier}:{key} - {metadata.get(key)!r} != {value!r}"
    assert (impl.parent / "README.md").is_file(), f"Missing README for {identifier}"
print(f"Catalog validated: {len(ids)} real scripts across {len(targets)} categories; 1,200 roadmap targets.")
