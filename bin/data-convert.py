#!/usr/bin/env python3
"""data-convert.py — convert between CSV and JSON (and YAML if PyYAML is present).

The deterministic-space chore that should never be done by hand: reshape tabular
or structured data from one format to another.
"""
import os
import io
import sys
import csv
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def _yaml():
    try:
        import yaml  # noqa
        return yaml
    except ImportError:
        return None


def infer_format(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    return {"yml": "yaml"}.get(ext, ext)


def load(text, fmt):
    if fmt == "json":
        return json.loads(text)
    if fmt == "csv":
        return list(csv.DictReader(io.StringIO(text)))
    if fmt == "yaml":
        y = _yaml()
        if not y:
            c.die("YAML needs PyYAML: pip install pyyaml")
        return y.safe_load(text)
    c.die(f"Unsupported input format: {fmt}")


def dump(data, fmt):
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    if fmt == "csv":
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            c.die("CSV output needs a list of objects.")
        cols = []
        for row in data:
            for k in row:
                if k not in cols:
                    cols.append(k)
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=cols)
        w.writeheader()
        w.writerows(data)
        return out.getvalue()
    if fmt == "yaml":
        y = _yaml()
        if not y:
            c.die("YAML needs PyYAML: pip install pyyaml")
        return y.safe_dump(data, sort_keys=False)
    c.die(f"Unsupported output format: {fmt}")


def main():
    ap = argparse.ArgumentParser(description="Convert between CSV, JSON, and YAML.")
    ap.add_argument("input", help="input file (or - for stdin)")
    ap.add_argument("-t", "--to", required=True, choices=["csv", "json", "yaml"],
                    help="target format")
    ap.add_argument("-f", "--from", dest="from_fmt", choices=["csv", "json", "yaml"],
                    help="source format (default: infer from extension)")
    ap.add_argument("-o", "--out", help="output file (default: stdout)")
    args = ap.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
        src = args.from_fmt or "json"
    else:
        if not os.path.isfile(args.input):
            c.die(f"Input not found: {args.input}")
        text = open(args.input, encoding="utf-8").read()
        src = args.from_fmt or infer_format(args.input)

    result = dump(load(text, src), args.to)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(result)
        c.ok(f"Wrote {args.out}")
    else:
        sys.stdout.write(result if result.endswith("\n") else result + "\n")


if __name__ == "__main__":
    main()
