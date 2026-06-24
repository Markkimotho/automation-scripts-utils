#!/usr/bin/env python3
"""secret-scan.py — scan for likely secrets before they get committed.

Defaults to staged files (so it pairs with a pre-commit hook); pass paths to
scan specific files, or --all to scan every tracked file. Exits non-zero when
anything matches, so it can gate a commit.
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402

PATTERNS = [
    ("AWS access key id",   re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block",   re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("GitHub token",        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token",         re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key",      re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Generic secret assign", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def staged_files(root):
    rc, out, _ = c.run(["git", "-C", root, "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    return [os.path.join(root, f) for f in out.split()] if rc == 0 else []


def tracked_files(root):
    rc, out, _ = c.run(["git", "-C", root, "ls-files"])
    return [os.path.join(root, f) for f in out.split()] if rc == 0 else []


def scan_file(path):
    findings = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for n, line in enumerate(f, 1):
                for label, pat in PATTERNS:
                    if pat.search(line):
                        findings.append((path, n, label))
    except OSError:
        pass
    return findings


def main():
    ap = argparse.ArgumentParser(description="Scan files for likely secrets.")
    ap.add_argument("paths", nargs="*", help="files to scan (default: staged files)")
    ap.add_argument("--root", default=".", help="repo root (default: .)")
    ap.add_argument("--all", action="store_true", help="scan all tracked files")
    args = ap.parse_args()

    if args.paths:
        files = args.paths
    elif args.all:
        files = tracked_files(args.root)
    else:
        files = staged_files(args.root)

    if not files:
        c.ok("Nothing to scan.")
        return

    findings = []
    for path in files:
        if any(part in SKIP_DIRS for part in path.split(os.sep)):
            continue
        if os.path.isfile(path):
            findings.extend(scan_file(path))

    if not findings:
        c.ok(f"No secrets found in {len(files)} file(s).")
        return

    c.err(f"Potential secrets found ({len(findings)}):")
    for path, line, label in findings:
        c.say(f"  {path}:{line}  {label}")
    sys.exit(2)


if __name__ == "__main__":
    main()
