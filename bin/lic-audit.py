#!/usr/bin/env python3
"""lic-audit.py — collect dependency licenses and flag copyleft / unknown.

Polyglot: reads installed Python distribution metadata and Node
node_modules/*/package.json. Flags GPL/AGPL/LGPL and unknown licenses, which are
the ones worth a human look before shipping.
"""
import os
import re
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402

FLAGGED = re.compile(r"\b(A?GPL|LGPL)\b", re.IGNORECASE)


def python_licenses():
    out = []
    try:
        from importlib import metadata
    except ImportError:
        return out
    for dist in metadata.distributions():
        try:
            meta = dist.metadata
        except Exception:
            continue
        name = meta.get("Name") or "?"
        lic = meta.get("License") or ""
        if not lic or lic.strip() in ("", "UNKNOWN"):
            # fall back to a Trove classifier
            classifiers = meta.get_all("Classifier") or []
            for cl in classifiers:
                if cl.startswith("License ::"):
                    lic = cl.split("::")[-1].strip()
                    break
        out.append(("python", name, (lic or "UNKNOWN").splitlines()[0][:40]))
    return out


def node_licenses(root):
    out = []
    nm = os.path.join(root, "node_modules")
    if not os.path.isdir(nm):
        return out
    for entry in os.listdir(nm):
        pkg_dir = os.path.join(nm, entry)
        pj = os.path.join(pkg_dir, "package.json")
        if not os.path.isfile(pj):
            continue
        try:
            data = json.loads(open(pj, encoding="utf-8", errors="ignore").read() or "{}")
        except json.JSONDecodeError:
            continue
        lic = data.get("license")
        if isinstance(lic, dict):
            lic = lic.get("type", "UNKNOWN")
        out.append(("node", data.get("name", entry), str(lic or "UNKNOWN")[:40]))
    return out


def main():
    ap = argparse.ArgumentParser(description="Audit dependency licenses across ecosystems.")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--strict", action="store_true", help="exit non-zero if anything is flagged")
    args = ap.parse_args()

    rows = python_licenses() + node_licenses(args.root)
    if not rows:
        c.ok("No dependency licenses found to audit.")
        return

    flagged = []
    for eco, name, lic in rows:
        if FLAGGED.search(lic) or lic.upper() == "UNKNOWN":
            flagged.append((eco, name, lic))

    c.say(f"Audited {len(rows)} package license(s).")
    if flagged:
        c.warn(f"\n{len(flagged)} flagged (copyleft or unknown):")
        c.print_table(["Ecosystem", "Package", "License"], flagged)
        if args.strict:
            sys.exit(2)
    else:
        c.ok("No copyleft or unknown licenses flagged.")


if __name__ == "__main__":
    main()
