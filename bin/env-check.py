#!/usr/bin/env python3
"""env-check.py — diff a .env against its .env.example and report key drift.

Language-agnostic: it only cares about KEY=value lines, so it works for any
project that uses a dotenv file.
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def parse_keys(path):
    keys = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k = line.split("=", 1)[0].strip()
            if k.startswith("export "):
                k = k[len("export "):].strip()
            if k:
                keys.add(k)
    return keys


def main():
    ap = argparse.ArgumentParser(description="Report keys missing from (or extra in) your .env.")
    ap.add_argument("--env", default=".env", help="actual env file (default: .env)")
    ap.add_argument("--example", default=".env.example", help="template (default: .env.example)")
    ap.add_argument("--strict", action="store_true", help="also fail on undocumented (extra) keys")
    args = ap.parse_args()

    if not os.path.isfile(args.example):
        c.die(f"Template not found: {args.example}")
    example = parse_keys(args.example)
    env = parse_keys(args.env) if os.path.isfile(args.env) else set()
    if not os.path.isfile(args.env):
        c.warn(f"{args.env} not found — treating as empty.")

    missing = sorted(example - env)   # documented but unset
    extra = sorted(env - example)     # set but undocumented

    if missing:
        c.err(f"Missing {len(missing)} key(s) present in {args.example} but not {args.env}:")
        for k in missing:
            c.say(f"  - {k}")
    if extra:
        c.warn(f"Undocumented {len(extra)} key(s) in {args.env} but not {args.example}:")
        for k in extra:
            c.say(f"  + {k}")

    if not missing and not extra:
        c.ok(f"{args.env} matches {args.example} ({len(example)} keys).")

    fail = bool(missing) or (args.strict and bool(extra))
    sys.exit(2 if fail else 0)


if __name__ == "__main__":
    main()
