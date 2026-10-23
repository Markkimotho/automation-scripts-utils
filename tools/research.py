#!/usr/bin/env python3
"""Validate, resume, or import discovery records; never fetch or execute remote code."""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research/candidates.json"
SCHEMA = ROOT / "research/schema.json"
ACCEPTED = {"accepted", "published"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def local_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Missing or unsafe evidence path: " + name)
    return path


def validate(data, root=ROOT):
    jsonschema.validate(data, read(root / "research/schema.json"))
    catalog = read(root / "catalog/scripts.json")
    jsonschema.validate(catalog, read(root / "catalog/schema.json"))
    ids, sources, verified_evidence = set(), set(), set()
    for candidate in data["candidates"]:
        identifier = candidate["id"]
        if identifier in ids or candidate["source_url"] in sources:
            raise ValueError(
                "Duplicate candidate identifier or source URL: " + identifier
            )
        ids.add(identifier)
        sources.add(candidate["source_url"])
        if candidate["reuse"] in ("copied", "modified") and not (
            candidate["license"]
            and candidate["license_url"]
            and candidate["source_revision"]
        ):
            raise ValueError(
                "Code reuse requires verified license and pinned revision: "
                + identifier
            )
        if candidate["status"] in ACCEPTED:
            if not candidate["license_review"] or not candidate["security_review"]:
                raise ValueError("Acceptance requires review: " + identifier)
            evidence = read(local_file(root, candidate["test_evidence"]))
            if evidence["result"] != "passed" or identifier not in evidence["scripts"]:
                raise ValueError("Missing passing evidence: " + identifier)
            if candidate["test_evidence"] not in verified_evidence:
                for name, expected in evidence["sha256"].items():
                    actual = hashlib.sha256(
                        local_file(root, name).read_bytes()
                    ).hexdigest()
                    if actual != expected:
                        raise ValueError("Evidence is stale for " + name)
                verified_evidence.add(candidate["test_evidence"])
            entry = next(
                (entry for entry in catalog["scripts"] if entry["id"] == identifier),
                None,
            )
            if not entry or entry.get("provenance_ref") != identifier:
                raise ValueError("Missing catalog provenance reference: " + identifier)
            if not set(entry["platforms"]) <= set(evidence["verified_platforms"]):
                raise ValueError("Untested platform advertised: " + identifier)
            for name in [
                entry["entrypoint"],
                str(Path(entry["entrypoint"]).parent / "metadata.yaml"),
                str(Path(entry["entrypoint"]).parent / "README.md"),
                candidate["test_file"],
            ]:
                actual = hashlib.sha256(local_file(root, name).read_bytes()).hexdigest()
                if evidence["sha256"].get(name) != actual:
                    raise ValueError("Evidence is stale for " + name)
    # New registrations may not bypass discovery acceptance by omitting the inventory record.
    for entry in catalog["scripts"]:
        if "provenance_ref" in entry:
            candidate = next(
                (c for c in data["candidates"] if c["id"] == entry["provenance_ref"]),
                None,
            )
            if not candidate or candidate["status"] not in ACCEPTED:
                raise ValueError("Catalog entry is not accepted: " + entry["id"])


def save(data, path=INVENTORY):
    # Atomic replacement avoids losing resumable state on interruption.
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def ingest(data, incoming):
    """Import new discoveries; never overwrite existing reviews or promote statuses."""
    known_ids = {c["id"]: c["source_url"] for c in data["candidates"]}
    known_urls = {c["source_url"] for c in data["candidates"]}
    additions = []
    for candidate in incoming["candidates"]:
        if candidate["id"] in known_ids:
            if known_ids[candidate["id"]] != candidate["source_url"]:
                raise ValueError("Identifier collision: " + candidate["id"])
            continue
        if candidate["source_url"] in known_urls:
            continue
        if candidate["status"] != "discovered":
            raise ValueError("Imports must begin as discovered")
        additions.append(candidate)
        known_ids[candidate["id"]] = candidate["source_url"]
        known_urls.add(candidate["source_url"])
    data["candidates"].extend(additions)
    return len(additions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("pending")
    importing = sub.add_parser("ingest")
    importing.add_argument("file", type=Path)
    retry = sub.add_parser("retry")
    retry.add_argument("source")
    retry.add_argument(
        "--after",
        required=True,
        type=int,
        help="seconds until this source may be retried",
    )
    args = parser.parse_args()
    try:
        data = read(INVENTORY)
        if args.command == "ingest":
            incoming = read(args.file)
            jsonschema.validate(incoming, read(SCHEMA))
            count = ingest(data, incoming)
            validate(data)
            save(data)
            print(f"Imported {count} new discoveries; existing reviews preserved.")
        elif args.command == "retry":
            if not 0 <= args.after <= 2_592_000:
                raise ValueError("retry delay must be between 0 and 30 days")
            state = data["source_state"].setdefault(args.source, {"attempts": 0})
            state["attempts"] += 1
            state["next_retry_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=args.after)
            ).isoformat()
            validate(data)
            save(data)
        elif args.command == "pending":
            print(
                json.dumps(
                    {
                        "candidates": [
                            c
                            for c in data["candidates"]
                            if c["status"] not in ACCEPTED | {"rejected"}
                        ],
                        "source_state": data["source_state"],
                    },
                    indent=2,
                )
            )
        else:
            validate(data)
            print(
                f"Validated {len(data['candidates'])} candidates and their acceptance evidence."
            )
        return 0
    except (OSError, ValueError, KeyError, jsonschema.ValidationError) as error:
        print("research: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
