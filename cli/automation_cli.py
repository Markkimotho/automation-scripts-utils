#!/usr/bin/env python3
"""Discover and safely launch registered automation scripts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(os.environ.get("AUTOMATION_ROOT", Path(__file__).resolve().parent.parent)).resolve()
CATALOG = ROOT / "catalog" / "scripts.json"
VALID_TYPES = {"string", "integer", "number", "boolean"}

def load_catalog() -> list[dict]:
    with CATALOG.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != 1 or not isinstance(data.get("scripts"), list):
        raise ValueError("Unsupported catalog format")
    return data["scripts"]

def select(scripts: list[dict], args: argparse.Namespace, phrase: str = "") -> list[dict]:
    matched = []
    for entry in scripts:
        if getattr(args, "category", None) and entry["category"] != args.category:
            continue
        if getattr(args, "language", None) and entry["language"] != args.language:
            continue
        if getattr(args, "platform", None) and args.platform not in entry["platforms"]:
            continue
        if getattr(args, "permission", None) and args.permission not in entry["permissions"]:
            continue
        if getattr(args, "tag", None) and args.tag not in entry["tags"]:
            continue
        haystack = " ".join(str(entry.get(k, "")) for k in ("id", "title", "description", "category", "topic", "tags")).lower()
        if phrase and not all(word in haystack for word in phrase.lower().split()):
            continue
        matched.append(entry)
    return matched

def print_list(entries: list[dict], as_json: bool) -> None:
    if as_json:
        print(json.dumps(entries, indent=2))
        return
    if not entries:
        print("No scripts matched.")
        return
    for e in entries:
        print(f"{e['id']:<27} {e['language']:<8} {e['category']:<24} {e['description'][:90]}")
    print(f"\n{len(entries)} script(s)")

def find_script(scripts: list[dict], identifier: str) -> dict:
    matches = [e for e in scripts if e["id"] == identifier]
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous script id: {identifier}")
    return matches[0]

def parse_params(entry: dict, supplied: list[str]) -> list[str]:
    specs = {p["name"]: p for p in entry.get("parameters", [])}
    values = {}
    for pair in supplied:
        if "=" not in pair:
            raise ValueError(f"Expected KEY=VALUE: {pair}")
        key, value = pair.split("=", 1)
        if key not in specs or key in values:
            raise ValueError(f"Unknown or repeated parameter: {key}")
        spec = specs[key]
        kind = spec.get("type", "string")
        if kind not in VALID_TYPES:
            raise ValueError(f"Unsupported parameter type: {kind}")
        if kind == "integer":
            int(value)
        elif kind == "number":
            float(value)
        elif kind == "boolean" and value.lower() not in ("true", "false"):
            raise ValueError(f"{key} must be true or false")
        if "choices" in spec and value not in [str(c) for c in spec["choices"]]:
            raise ValueError(f"{key} must be one of {spec['choices']}")
        values[key] = value
    for name, spec in specs.items():
        if spec.get("required") and name not in values:
            raise ValueError(f"Missing required parameter: {name}")
    result = []
    for name, value in values.items():
        flag = specs[name].get("flag", "--" + name.replace("_", "-"))
        if not re.fullmatch(r"--[a-zA-Z][a-zA-Z0-9-]*", flag):
            raise ValueError(f"Invalid parameter flag: {flag}")
        if specs[name].get("type") == "boolean":
            if value.lower() == "true":
                result.append(flag)
        else:
            result.extend([flag, value])
    return result

def run(entry: dict, args: argparse.Namespace) -> int:
    target = (ROOT / entry["entrypoint"]).resolve()
    if not target.is_file() or not target.is_relative_to(ROOT / "scripts"):
        raise ValueError("Catalog points outside scripts/ or to a missing executable")
    current = {"darwin": "macos", "linux": "linux", "windows": "windows"}.get(platform.system().lower(), "unknown")
    if current not in entry["platforms"] and not args.dry_run:
        raise ValueError(f"{entry['id']} does not declare support for {current}")
    extra = list(args.script_args)
    if extra and extra[0] == "--":
        extra.pop(0)
    if any("\x00" in value for value in extra):
        raise ValueError("NUL is not permitted in arguments")
    language = entry["language"]
    runners = {
        "python": [sys.executable],
        "bash": ["bash"],
        "javascript": ["node"],
        "typescript": ["node", "--experimental-strip-types"],
        "go": ["go", "run"],
        "ruby": ["ruby"],
        "powershell": [shutil.which("pwsh") or shutil.which("powershell") or "pwsh", "-File"],
    }
    if language not in runners:
        raise ValueError(f"No safe executable runner registered for {language}")
    command = runners[language] + [str(target)]
    command.extend(parse_params(entry, args.param))
    command.extend(extra)
    if args.dry_run:
        print("PREVIEW ONLY; nothing executed:\n" + shlex.join(command))
        return 0
    missing = [dep for dep in entry.get("dependencies", []) if not shutil.which(dep)]
    if missing:
        raise ValueError(f"Missing dependencies: {', '.join(missing)}")
    if entry.get("requires_confirmation") or entry.get("destructive") or any(p.endswith("-write") for p in entry.get("permissions", [])):
        if not args.yes:
            if not sys.stdin.isatty():
                raise ValueError("Non-interactive mutation requires explicit --yes")
            choice = input(f"Execute {entry['id']} with its requested permissions? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                print("Cancelled.")
                return 2
    environ = os.environ.copy()
    if args.yes:
        environ["ASSUME_YES"] = "1"
    return subprocess.run(command, env=environ, check=False).returncode

def add_filters(parser: argparse.ArgumentParser) -> None:
    for flag in ("category", "language", "platform", "permission", "tag"):
        parser.add_argument("--" + flag)
    parser.add_argument("--json", action="store_true", help="machine-readable output")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="automation", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="list registered scripts")
    add_filters(listing)
    search = sub.add_parser("search", help="search across script metadata")
    search.add_argument("query", nargs="+")
    add_filters(search)
    info = sub.add_parser("info", help="inspect a script")
    info.add_argument("id")
    execute = sub.add_parser("run", help="execute a registered script")
    execute.add_argument("id")
    execute.add_argument("--dry-run", action="store_true", help="preview the command without executing anything")
    execute.add_argument("--yes", action="store_true", help="explicitly approve changes without prompting")
    execute.add_argument("--param", action="append", default=[], metavar="KEY=VALUE", help="validated named parameter")
    execute.add_argument("script_args", nargs="*", help="script-specific arguments after --")
    args, unknown = parser.parse_known_args(argv)
    if args.command == "run":
        args.script_args.extend(unknown)
    elif unknown:
        parser.error(f"unrecognized arguments: {' '.join(unknown)}")
    try:
        scripts = load_catalog()
        if args.command == "list":
            print_list(select(scripts, args), args.json)
        elif args.command == "search":
            print_list(select(scripts, args, " ".join(args.query)), args.json)
        elif args.command == "info":
            print(json.dumps(find_script(scripts, args.id), indent=2))
        elif args.command == "run":
            return run(find_script(scripts, args.id), args)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"automation: {error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
