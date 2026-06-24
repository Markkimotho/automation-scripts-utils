#!/usr/bin/env python3
"""version-bump.py — bump the version string in whatever manifest(s) a repo uses.

Handles pyproject.toml, package.json, Cargo.toml, and setup.py. Polyglot: a repo
with several manifests is bumped consistently in one run. Only the first
`version` field in each file is touched (the project's own version), so
dependency version pins are left alone.
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402

# manifest -> regex with a single capture group around the version value
PATTERNS = {
    "pyproject.toml": re.compile(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']'),
    "Cargo.toml":     re.compile(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']'),
    "package.json":   re.compile(r'"version"\s*:\s*"([^"]+)"'),
    "setup.py":       re.compile(r'version\s*=\s*["\']([^"\']+)["\']'),
}

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(.*)$")


def bump(version, part):
    m = SEMVER.match(version)
    if not m:
        return None
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    ap = argparse.ArgumentParser(description="Bump the project version across manifests.")
    ap.add_argument("part", nargs="?", choices=["major", "minor", "patch"], default="patch")
    ap.add_argument("--set", dest="set_version", help="set an explicit version instead of bumping")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("-n", "--dry-run", action="store_true", help="show changes, write nothing")
    args = ap.parse_args()

    touched = 0
    for name, pat in PATTERNS.items():
        path = os.path.join(args.root, name)
        if not os.path.isfile(path):
            continue
        text = open(path).read()
        m = pat.search(text)
        if not m:
            continue
        current = m.group(1)
        if args.set_version:
            new = args.set_version.lstrip("v")
        else:
            new = bump(current, args.part)
            if new is None:
                c.warn(f"{name}: version '{current}' isn't semver — skipped.")
                continue
        if new == current:
            c.say(f"{name}: already {current}")
            continue

        # Replace only the matched version value, preserving surrounding text.
        s, e = m.span(1)
        updated = text[:s] + new + text[e:]
        c.info(f"{name}: {current} -> {new}")
        touched += 1
        if not args.dry_run:
            open(path, "w").write(updated)

    if touched == 0:
        c.warn("No bumpable version found in any manifest.")
        sys.exit(1)
    c.ok(("(dry run) " if args.dry_run else "") + f"Updated {touched} manifest(s).")


if __name__ == "__main__":
    main()
