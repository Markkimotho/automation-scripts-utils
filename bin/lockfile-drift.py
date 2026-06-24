#!/usr/bin/env python3
"""lockfile-drift.py — flag manifests whose lockfile is missing or stale.

Polyglot: checks every ecosystem present in the repo (npm, pip/poetry, cargo,
go, bundler). "Drift" means the lockfile is absent, or older than its manifest
(so it may not reflect the current dependencies).
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Report manifest/lockfile drift across ecosystems.")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    args = ap.parse_args()

    found = c.detect_manifests(args.root)
    if not found:
        c.ok("No recognized manifests found — nothing to check.")
        return

    drift = 0
    checked = 0
    for eco, manifests in found.items():
        for man in manifests:
            candidates = c.LOCKFILES.get(man, [])
            if not candidates:
                continue  # no lockfile concept (e.g. requirements.txt)
            checked += 1
            man_path = os.path.join(args.root, man)
            existing = [lf for lf in candidates if os.path.isfile(os.path.join(args.root, lf))]
            if not existing:
                c.err(f"  ✗ {man} ({eco}): no lockfile (expected one of {', '.join(candidates)})")
                drift += 1
                continue
            lock = existing[0]
            lock_path = os.path.join(args.root, lock)
            if os.path.getmtime(man_path) > os.path.getmtime(lock_path):
                c.warn(f"  ~ {man} ({eco}): {lock} is older than the manifest — may be stale")
                drift += 1
            else:
                c.ok(f"  ✓ {man} ({eco}): {lock} up to date")

    if checked == 0:
        c.ok("No lockfile-bearing manifests to check.")
        return
    if drift:
        c.die(f"{drift} drift issue(s) found.", code=2)
    c.ok("All lockfiles consistent.")


if __name__ == "__main__":
    main()
