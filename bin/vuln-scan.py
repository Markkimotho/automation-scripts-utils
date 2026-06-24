#!/usr/bin/env python3
"""vuln-scan.py — run each ecosystem's audit tool and normalize the findings.

Polyglot: pip-audit / npm audit / cargo audit / govulncheck, whichever apply.
Missing tools are skipped with a note. Exits non-zero if any vulnerability is
reported (so it can gate CI); use --warn-only to always exit 0.
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def pip_audit(root):
    if not c.have("pip-audit"):
        return None, "pip-audit not installed (pip install pip-audit)"
    rc, out, _ = c.run(["pip-audit", "-f", "json"], cwd=root)
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return [], None
    rows = []
    deps = data.get("dependencies", data) if isinstance(data, dict) else data
    for dep in (deps or []):
        for v in dep.get("vulns", []):
            rows.append(("python", dep.get("name", "?"), v.get("id", "?"),
                         ",".join(v.get("fix_versions", []) or []) or "-"))
    return rows, None


def npm_audit(root):
    if not c.have("npm"):
        return None, "npm not installed"
    rc, out, _ = c.run(["npm", "audit", "--json"], cwd=root)
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return [], None
    rows = []
    for name, info in (data.get("vulnerabilities") or {}).items():
        sev = info.get("severity", "?")
        rows.append(("node", name, sev, "fix available" if info.get("fixAvailable") else "-"))
    return rows, None


def cargo_audit(root):
    if not c.have("cargo-audit") and not c.have("cargo"):
        return None, "cargo-audit not installed (cargo install cargo-audit)"
    rc, out, _ = c.run(["cargo", "audit", "--json"], cwd=root)
    if rc != 0 and not out:
        return None, "cargo-audit not installed (cargo install cargo-audit)"
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return [], None
    rows = []
    for v in (data.get("vulnerabilities", {}) or {}).get("list", []):
        adv = v.get("advisory", {})
        rows.append(("rust", v.get("package", {}).get("name", "?"), adv.get("id", "?"),
                     ",".join(adv.get("patched_versions", []) or []) or "-"))
    return rows, None


def go_vuln(root):
    if not c.have("govulncheck"):
        return None, "govulncheck not installed (go install golang.org/x/vuln/cmd/govulncheck@latest)"
    rc, out, _ = c.run(["govulncheck", "-json", "./..."], cwd=root)
    rows = []
    for line in out.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        finding = obj.get("finding") or {}
        if finding.get("osv"):
            rows.append(("go", finding.get("trace", [{}])[0].get("module", "?"),
                         finding.get("osv", "?"), "-"))
    return rows, None


CHECKS = {"python": pip_audit, "node": npm_audit, "rust": cargo_audit, "go": go_vuln}


def main():
    ap = argparse.ArgumentParser(description="Scan dependencies for known vulnerabilities.")
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--warn-only", action="store_true", help="always exit 0 (report only)")
    args = ap.parse_args()

    found = c.detect_manifests(args.root)
    if not found:
        c.ok("No recognized manifests found — nothing to scan.")
        return

    rows = []
    for eco in found:
        check = CHECKS.get(eco)
        if not check:
            continue
        r, skip = check(args.root)
        if skip:
            c.warn(f"{eco}: skipped ({skip})")
            continue
        rows.extend(r or [])

    if not rows:
        c.ok("No known vulnerabilities found (for the ecosystems scanned).")
        return
    c.print_table(["Ecosystem", "Package", "Advisory", "Fix"], rows)
    c.err(f"\n{len(rows)} vulnerability finding(s).")
    sys.exit(0 if args.warn_only else 2)


if __name__ == "__main__":
    main()
