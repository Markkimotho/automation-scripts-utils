#!/usr/bin/env python3
"""Read local EML headers; never connects to a mail server."""
import argparse
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    args = ap.parse_args()
    if not args.directory.is_dir():
        ap.error("directory does not exist")
    results = []
    for path in sorted(args.directory.glob("*.eml")):
        if path.is_symlink():
            continue
        try:
            with path.open("rb") as f:
                message = BytesParser(policy=policy.default, headersonly=True).parse(f)
            results.append({"file": path.name, "from": str(message.get("From", "")), "to": str(message.get("To", "")), "subject": str(message.get("Subject", "")), "date": str(message.get("Date", ""))})
        except OSError as error:
            ap.exit(2, f"Failed to read {path}: {error}\n")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
