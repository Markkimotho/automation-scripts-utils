#!/usr/bin/env python3
"""gh-release.py — bump version, build a changelog from merged PRs, tag, and release.

Computes the next semver tag from the latest existing tag, drafts release notes
from the PRs/commits since that tag, then (with confirmation) creates and pushes
the tag and a GitHub release.
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def latest_tag():
    rc, out, _ = c.run(["git", "describe", "--tags", "--abbrev=0"])
    return out.strip() if rc == 0 and out.strip() else ""


def parse_semver(tag):
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", tag or "")
    if not m:
        return None
    return [int(m.group(1)), int(m.group(2)), int(m.group(3))]


def bump(parts, which):
    major, minor, patch = parts
    if which == "major":
        return [major + 1, 0, 0]
    if which == "minor":
        return [major, minor + 1, 0]
    return [major, minor, patch + 1]


def changelog_since(tag):
    """Build a changelog from commit subjects since the given tag."""
    rng = f"{tag}..HEAD" if tag else "HEAD"
    rc, out, _ = c.run(["git", "log", rng, "--pretty=format:- %s (%h)"])
    return out.strip().splitlines() if rc == 0 and out.strip() else []


def main():
    ap = argparse.ArgumentParser(description="Cut a versioned GitHub release.")
    ap.add_argument("part", nargs="?", choices=["major", "minor", "patch"], default="patch",
                    help="which semver part to bump (default: patch)")
    ap.add_argument("--set", dest="set_version", help="set an explicit version instead of bumping")
    ap.add_argument("-n", "--dry-run", action="store_true", help="print the plan, change nothing")
    args = ap.parse_args()

    rc, _, _ = c.run(["git", "rev-parse", "--is-inside-work-tree"])
    if rc != 0:
        c.die("Not inside a git repository.")
    if not c.have("gh"):
        c.die("gh not found. Install the GitHub CLI: https://cli.github.com")

    prev = latest_tag()
    if args.set_version:
        nextv = args.set_version.lstrip("v")
        if not parse_semver(nextv):
            c.die(f"--set must be semver (X.Y.Z), got: {args.set_version}")
    else:
        parts = parse_semver(prev) or [0, 0, 0]
        nextv = ".".join(str(x) for x in bump(parts, args.part))
    tag = f"v{nextv}"

    notes = changelog_since(prev)
    c.info(f"Previous tag: {prev or '(none)'}")
    c.info(f"Next tag:     {tag}")
    c.say("\nChangelog:")
    if notes:
        for ln in notes:
            c.say(f"  {ln}")
    else:
        c.say("  (no commits since last tag)")

    if args.dry_run:
        c.say("\n(dry run — no tag or release created)")
        return

    if not c.confirm(f"\nCreate and push tag {tag} and a GitHub release?"):
        c.die("Aborted.")

    c.run(["git", "tag", "-a", tag, "-m", tag], check=True)
    c.run(["git", "push", "origin", tag], check=True)
    body = "\n".join(notes) if notes else tag
    rc, out, err = c.run(["gh", "release", "create", tag, "--title", tag, "--notes", body])
    if rc != 0:
        c.die(err.strip() or "gh release create failed")
    c.ok(f"Released {tag}.")
    if out.strip():
        c.say(out.strip())


if __name__ == "__main__":
    main()
