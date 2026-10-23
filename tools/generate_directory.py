#!/usr/bin/env python3
"""Generate the public script directory and detailed pages from catalog metadata."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def generated_files(root=ROOT):
    entries = json.loads((root / "catalog/scripts.json").read_text(encoding="utf-8"))[
        "scripts"
    ]
    files = {}
    lines = [
        "# Script directory",
        "",
        "Browse available automations. [Install](install.md) the command and use `automation info SCRIPT-ID` to inspect permissions and requirements.",
        "",
    ]
    for category in sorted({entry["category"] for entry in entries}):
        lines.extend(["## " + category.replace("-", " ").title(), ""])
        for entry in sorted(
            (x for x in entries if x["category"] == category), key=lambda x: x["id"]
        ):
            identifier = entry["id"]
            lines.extend(
                [
                    f"### `{identifier}`",
                    "",
                    entry["description"],
                    "",
                    f"**Language:** {entry['language']} · **Platforms:** {', '.join(entry['platforms'])} · **Permissions:** {', '.join(entry['permissions'])}",
                    "",
                ]
            )
            if "usage_example" in entry:
                lines.extend(
                    [
                        "```bash",
                        entry["usage_example"],
                        "```",
                        "",
                        f"[Usage, options and troubleshooting](automations/{identifier}.md)",
                        "",
                    ]
                )
                readme = (root / entry["entrypoint"]).parent / "README.md"
                files[root / "docs/automations" / (identifier + ".md")] = (
                    readme.read_text(encoding="utf-8")
                )
            else:
                lines.extend(
                    [
                        "```bash",
                        f"automation info {identifier}",
                        f"automation run {identifier} --dry-run",
                        f"automation run {identifier} -- --help",
                        "```",
                        "",
                    ]
                )
    files[root / "docs/scripts.md"] = "\n".join(lines)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if generated files need updating"
    )
    args = parser.parse_args()
    stale = []
    for path, content in generated_files().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        print(
            "Regenerate documentation: python tools/generate_directory.py\n"
            + "\n".join(stale),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
