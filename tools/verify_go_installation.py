#!/usr/bin/env python3
"""Verify installed offline Go audits from a disposable working directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("automation", type=Path)
    args = parser.parse_args()
    executable = str(args.automation.resolve(strict=True))
    environment = os.environ.copy()
    for name in ("AUTOMATION_ROOT", "PYTHONPATH"):
        environment.pop(name, None)
    environment.update(GOTOOLCHAIN="local", GOWORK="off", GOPROXY="off")
    checks = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        fixture = (
            ROOT
            / "scripts/security-compliance/certificates/pem-expiry-report/testdata/valid.pem"
        )
        (root / "cert.pem").write_bytes(fixture.read_bytes())
        (root / "networks.txt").write_text("192.0.2.0/24\n", encoding="utf-8")
        (root / "image.png").write_bytes(b"verified")
        manifest = [
            {
                "path": "image.png",
                "bytes": 8,
                "sha256": hashlib.sha256(b"verified").hexdigest(),
            }
        ]
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        def run(*arguments, code=0):
            result = subprocess.run(
                [executable, *arguments],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
            if result.returncode != code:
                raise RuntimeError(
                    f"Expected {code}, got {result.returncode}: {result.stderr}"
                )
            checks.append({"arguments": list(arguments), "expected_exit": code})
            return result.stdout

        catalog = json.loads(run("list", "--json"))
        generated = json.loads(run("run", "image-checksum-manifest", "--", "."))
        if generated != manifest:
            raise ValueError(
                "Existing Ruby manifest is incompatible with verifier inputs"
            )
        (root / "manifest.json").write_text(json.dumps(generated), encoding="utf-8")
        for identifier in (
            "pem-expiry-report",
            "cidr-overlap-report",
            "checksum-manifest-verify",
        ):
            info = json.loads(run("info", identifier))
            if info["provenance_ref"] != identifier:
                raise ValueError("Installed provenance mismatch")
        result = json.loads(
            run(
                "run",
                "pem-expiry-report",
                "--",
                "--input",
                "cert.pem",
                "--as-of",
                "2030-01-01T00:00:00Z",
            )
        )
        if result["findings"] != 0 or len(result["certificates"]) != 1:
            raise ValueError("Incorrect certificate report")
        run(
            "run",
            "pem-expiry-report",
            "--",
            "--input",
            "cert.pem",
            "--as-of",
            "2032-01-01T00:00:00Z",
            code=1,
        )
        (root / "cert.pem").write_text("invalid", encoding="utf-8")
        run("run", "pem-expiry-report", "--", "--input", "cert.pem", code=2)
        run("run", "cidr-overlap-report", "--param", "input=networks.txt")
        (root / "networks.txt").write_text(
            "10.0.0.0/8\n10.1.0.0/16\n", encoding="utf-8"
        )
        run("run", "cidr-overlap-report", "--", "--input", "networks.txt", code=1)
        (root / "networks.txt").write_text("invalid", encoding="utf-8")
        run("run", "cidr-overlap-report", "--", "--input", "networks.txt", code=2)
        arguments = (
            "run",
            "checksum-manifest-verify",
            "--param",
            "root=.",
            "--param",
            "manifest=manifest.json",
        )
        result = json.loads(run(*arguments))
        if result != {"verified": 1, "findings": []}:
            raise ValueError("Incorrect checksum report")
        (root / "image.png").write_bytes(b"tampered")
        run(*arguments, code=1)
        (root / "manifest.json").write_text("[] trailing", encoding="utf-8")
        run(*arguments, code=2)
        preview = run(
            "run", "pem-expiry-report", "--dry-run", "--param", "input=cert.pem"
        )
        if (
            "go build" not in preview
            or "share/automation-scripts-utils" not in preview.replace("\\", "/")
        ):
            raise ValueError("Preview does not use installed sources")
    print(
        json.dumps(
            {
                "result": "passed",
                "catalog_entries": len(catalog),
                "checks": checks,
                "note": "Installed tools executed outside checkout, preserving exit codes 0, 1 and 2.",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
