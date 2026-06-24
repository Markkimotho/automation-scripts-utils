#!/usr/bin/env python3
"""deps-outdated.py — outdated packages across pip / npm / cargo / go, one table.

Polyglot: detects the manifests present and runs each ecosystem's native
"outdated" query, normalizing the output into a single table. Ecosystems whose
toolchain isn't installed are skipped with a note rather than failing.
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def pip_outdated(root):
    if not c.have("pip") and not c.have("pip3"):
        return None, "pip not installed"
    pip = "pip" if c.have("pip") else "pip3"
    rc, out, _ = c.run([pip, "list", "--outdated", "--format", "json"], cwd=root)
    if rc != 0:
        return None, "pip list failed"
    rows = []
    for p in json.loads(out or "[]"):
        rows.append(("python", p.get("name"), p.get("version"), p.get("latest_version")))
    return rows, None


def npm_outdated(root):
    if not c.have("npm"):
        return None, "npm not installed"
    # npm outdated exits non-zero when there are outdated packages; parse regardless.
    rc, out, _ = c.run(["npm", "outdated", "--json"], cwd=root)
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return [], None
    rows = []
    for name, info in data.items():
        rows.append(("node", name, info.get("current", "?"), info.get("latest", "?")))
    return rows, None


def go_outdated(root):
    if not c.have("go"):
        return None, "go not installed"
    rc, out, _ = c.run(["go", "list", "-u", "-m", "-f",
                        "{{if and .Update (not .Indirect)}}{{.Path}} {{.Version}} {{.Update.Version}}{{end}}",
                        "all"], cwd=root)
    if rc != 0:
        return [], None
    rows = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            rows.append(("go", parts[0], parts[1], parts[2]))
    return rows, None


def cargo_outdated(root):
    if not c.have("cargo"):
        return None, "cargo not installed"
    rc, out, _ = c.run(["cargo", "outdated", "--format", "json"], cwd=root)
    if rc != 0:
        return None, "cargo-outdated not installed (cargo install cargo-outdated)"
    rows = []
    try:
        for d in json.loads(out or "{}").get("dependencies", []):
            if d.get("project") != d.get("latest"):
                rows.append(("rust", d.get("name"), d.get("project"), d.get("latest")))
    except json.JSONDecodeError:
        return [], None
    return rows, None


CHECKS = {
    "python": pip_outdated,
    "node": npm_outdated,
    "go": go_outdated,
    "rust": cargo_outdated,
}


def main():
    ap = argparse.ArgumentParser(description="List outdated dependencies across ecosystems.")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    args = ap.parse_args()

    found = c.detect_manifests(args.root)
    if not found:
        c.ok("No recognized manifests found — nothing to check.")
        return

    all_rows = []
    for eco in found:
        check = CHECKS.get(eco)
        if not check:
            continue
        rows, skip = check(args.root)
        if skip:
            c.warn(f"{eco}: skipped ({skip})")
            continue
        all_rows.extend(rows or [])

    if not all_rows:
        c.ok("Everything up to date (for the ecosystems checked).")
        return
    c.print_table(["Ecosystem", "Package", "Current", "Latest"], all_rows)


if __name__ == "__main__":
    main()
