#!/usr/bin/env python3
"""deps-unused.py — declared dependencies that are never imported.

Heuristic, polyglot (Python + Node). It maps a declared package to its likely
import name and greps the source for it. Useful as a hint, not gospel: dynamic
imports, plugins, and tooling-only deps can show as false positives.
"""
import os
import re
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402

# Package name -> import name where they differ.
PY_ALIASES = {
    "pyyaml": "yaml", "beautifulsoup4": "bs4", "pillow": "PIL",
    "scikit-learn": "sklearn", "python-dateutil": "dateutil",
    "opencv-python": "cv2", "msgpack-python": "msgpack",
    "attrs": "attr", "protobuf": "google",
}


def read_text(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def source_blob(root, exts):
    """Concatenate source files (skipping vendor dirs) for a cheap grep."""
    skip = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
    parts = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if os.path.splitext(fn)[1] in exts:
                parts.append(read_text(os.path.join(dirpath, fn)))
    return "\n".join(parts)


def python_declared(root):
    names = []
    req = os.path.join(root, "requirements.txt")
    if os.path.isfile(req):
        for line in read_text(req).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            names.append(re.split(r"[<>=!~;\[ ]", line, 1)[0].strip())
    # requirements.txt is the reliable declared-dependency source; pyproject
    # dependency parsing without a TOML lib is too noisy to trust here.
    return [n for n in names if n]


def import_name(pkg):
    key = pkg.lower()
    return PY_ALIASES.get(key, key.replace("-", "_"))


def check_python(root):
    declared = python_declared(root)
    if not declared:
        return []
    blob = source_blob(root, {".py"})
    unused = []
    for pkg in declared:
        imp = import_name(pkg)
        if not re.search(rf"(?m)^\s*(import|from)\s+{re.escape(imp)}\b", blob):
            unused.append(pkg)
    return unused


def check_node(root):
    pj = os.path.join(root, "package.json")
    if not os.path.isfile(pj):
        return []
    try:
        data = json.loads(read_text(pj) or "{}")
    except json.JSONDecodeError:
        return []
    deps = list((data.get("dependencies") or {}).keys())
    if not deps:
        return []
    blob = source_blob(root, {".js", ".jsx", ".ts", ".tsx", ".mjs"})
    unused = []
    for pkg in deps:
        if not re.search(rf"""(require\(\s*['"]{re.escape(pkg)}|from\s+['"]{re.escape(pkg)})""", blob):
            unused.append(pkg)
    return unused


def main():
    ap = argparse.ArgumentParser(description="Find declared-but-unimported dependencies.")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--warn-only", action="store_true", help="always exit 0 (report only)")
    args = ap.parse_args()

    total = 0
    for eco, fn in (("python", check_python), ("node", check_node)):
        unused = fn(args.root)
        if unused:
            total += len(unused)
            c.warn(f"{eco}: {len(unused)} possibly-unused dependency(ies):")
            for p in sorted(unused):
                c.say(f"  - {p}")

    if total == 0:
        c.ok("No obviously-unused dependencies found.")
        return
    c.say("\n(Heuristic — verify before removing; dynamic imports can be false positives.)")
    sys.exit(0 if args.warn_only else 2)


if __name__ == "__main__":
    main()
