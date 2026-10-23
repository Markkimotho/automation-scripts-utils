#!/usr/bin/env python3
"""Preview or extract MIME attachments into new files without executing content."""

import argparse
from email import errors, policy
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def attachments(data):
    # Bound MIME structure before the parser can allocate its message tree.
    for count, _ in enumerate(re.finditer(rb"(?m)^--", data), 1):
        if count > 2000:
            raise ValueError("more than 2000 boundary-like lines")
    message = BytesParser(policy=policy.default.clone(raise_on_defect=True)).parsebytes(
        data
    )
    found, total = [], 0
    for index, part in enumerate(message.walk()):
        if index >= 1000:
            raise ValueError("more than 1000 MIME parts")
        if part.is_multipart():
            if (
                part.get_content_disposition() == "attachment"
                or part.get_filename() is not None
            ):
                raise ValueError(
                    "embedded-message or multipart attachments are unsupported"
                )
            continue
        if (
            part.get_content_disposition() != "attachment"
            and part.get_filename() is None
        ):
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            raise ValueError("attachment cannot be decoded")
        total += len(payload)
        if total > 16 << 20:
            raise ValueError("decoded attachments exceed 16 MiB")
        original = (
            (part.get_filename() or "attachment.bin").replace("\\", "/").split("/")[-1]
        )
        safe = (
            re.sub(r"[^A-Za-z0-9._-]", "_", original).strip("._")[:80]
            or "attachment.bin"
        )
        name = f"attachment-{len(found) + 1:04d}-{safe}"
        found.append(
            (
                name,
                payload,
                {
                    "name": name,
                    "bytes": len(payload),
                    "content_type": part.get_content_type(),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                },
            )
        )
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    completed = []
    try:
        if not args.input.is_file() or args.input.stat().st_size > 16 << 20:
            raise ValueError("require regular EML input <=16 MiB")
        with args.input.open("rb") as stream:
            data = stream.read((16 << 20) + 1)
        if len(data) > 16 << 20:
            raise ValueError("input grew beyond limit")
        planned = attachments(data)
        output = args.output.expanduser().absolute()
        output = output.parent.resolve(strict=True) / output.name
        if output.is_symlink() or (output.exists() and not output.is_dir()):
            raise ValueError("output must be a directory, not a symlink")
        if any(os.path.lexists(output / name) for name, _, _ in planned):
            raise ValueError("planned output already exists")
        if args.apply and planned:
            output.mkdir(mode=0o700, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=".eml-extract-", dir=output
            ) as directory:
                for name, payload, _ in planned:
                    staged = Path(directory) / name
                    with staged.open("xb") as stream:
                        os.chmod(staged, 0o600)
                        stream.write(payload)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.link(staged, output / name)
                    completed.append(name)
        print(
            json.dumps({"apply": args.apply, "files": [row for _, _, row in planned]})
        )
        return 0
    except (
        OSError,
        ValueError,
        RecursionError,
        errors.MessageError,
        errors.MessageDefect,
    ):
        print(
            "eml-attachment-extract: invalid/unreadable EML, unsafe/existing output, resource limit or I/O failure; completed files: "
            + json.dumps(completed),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
