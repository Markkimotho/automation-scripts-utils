#!/usr/bin/env python3
"""Plan a domain-based migration without modifying files by default."""
from __future__ import annotations
import argparse
from pathlib import Path

GIT = {"gh-", "git-"}
DEPENDENCIES = {"deps-", "lockfile-", "vuln-", "lic-", "version-", "env-"}
ENVIRONMENT = {"dev-", "proj-", "precommit-", "py-"}
DATA = {"data-"}
SECURITY = {"secret-"}
BACKUP = {"snapshot"}
SYSTEM = {"clean-", "port-"}

def destination(name: str) -> Path:
    if name.startswith(tuple(GIT)):
        return Path("scripts/developer-tools/git") / name
    if name.startswith(tuple(DEPENDENCIES)):
        return Path("scripts/developer-tools/dependencies") / name
    if name.startswith(tuple(ENVIRONMENT)):
        return Path("scripts/developer-tools/environments") / name
    if name.startswith(tuple(DATA)):
        return Path("scripts/data-engineering/conversion") / name
    if name.startswith(tuple(SECURITY)):
        return Path("scripts/security-compliance/scanning") / name
    if name.startswith(tuple(BACKUP)):
        return Path("scripts/backup-recovery/snapshots") / name
    if name.startswith(tuple(SYSTEM)):
        return Path("scripts/system-administration/maintenance") / name
    raise ValueError(f"Uncategorized executable: {name}")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    entries = sorted(p for p in (root / "bin").iterdir() if p.is_file())
    failures = 0
    for path in entries:
        try:
            target = destination(path.name)
            print(f"{path.relative_to(root)} -> {target}")
        except ValueError as exc:
            failures += 1
            print(f"REVIEW: {exc}")
    print(f"Inventoried {len(entries)} files; {failures} need classification.")
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
