#!/usr/bin/env python3
"""gh-issues-sync.py — create GitHub issues (and their labels) from a JSON file.

The file is a list of {"title": str, "body": str, "labels": [str, ...]}.
Idempotent: an issue whose title already exists in the repo (open or closed,
compared case-insensitively) is skipped, so re-running never duplicates.
Missing labels are created first with a color chosen by prefix:
  P1/P2/P3 priorities, area:* areas, and known type labels.

Preview by default; --apply writes. Creates are spaced out (--delay) to stay
under GitHub's secondary rate limits for content creation.
"""
import argparse
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402

TYPE_COLORS = {
    "bug": "d73a4a", "security": "b60205", "enhancement": "a2eeef",
    "performance": "fbca04", "reliability": "0e8a16", "observability": "5319e7",
    "testing": "bfd4f2", "refactor": "c5def5", "docs": "0075ca", "dx": "7057ff",
    "ux": "d4c5f9", "accessibility": "006b75",
}
PRIORITY_COLORS = {"P1": "b60205", "P2": "d93f0b", "P3": "fbca04"}
AREA_COLOR = "1d76db"
DEFAULT_COLOR = "ededed"


def label_color(name):
    if name in PRIORITY_COLORS:
        return PRIORITY_COLORS[name]
    if name.startswith("area:"):
        return AREA_COLOR
    return TYPE_COLORS.get(name, DEFAULT_COLOR)


def validate(issues):
    """Return a list of problems; empty means the file is usable."""
    problems, seen = [], set()
    if not isinstance(issues, list):
        return ["top level must be a JSON list"]
    for i, issue in enumerate(issues):
        where = f"item {i}"
        if not isinstance(issue, dict):
            problems.append(f"{where}: not an object")
            continue
        title = (issue.get("title") or "").strip()
        if not title:
            problems.append(f"{where}: missing title")
        elif title.lower() in seen:
            problems.append(f"{where}: duplicate title {title!r}")
        seen.add(title.lower())
        if not (issue.get("body") or "").strip():
            problems.append(f"{where}: missing body")
        labels = issue.get("labels", [])
        if not isinstance(labels, list) or not all(isinstance(x, str) and x for x in labels):
            problems.append(f"{where}: labels must be a list of non-empty strings")
    return problems


def gh_json(args, runner):
    code, out, err = runner(["gh", *args])
    if code != 0:
        c.die(f"gh {' '.join(args[:3])} failed: {err.strip()}")
    return json.loads(out or "[]")


def plan(issues, existing_titles, existing_labels):
    """Pure: which labels to create and which issues to create or skip."""
    have = {t.strip().lower() for t in existing_titles}
    to_create = [i for i in issues if i["title"].strip().lower() not in have]
    skipped = [i for i in issues if i["title"].strip().lower() in have]
    wanted = sorted({lab for i in to_create for lab in i.get("labels", [])})
    new_labels = [lab for lab in wanted if lab not in set(existing_labels)]
    return new_labels, to_create, skipped


def main(argv=None, runner=c.run, sleep=time.sleep):
    ap = argparse.ArgumentParser(description="Create GitHub issues and labels from a JSON file.")
    ap.add_argument("file", help="JSON list of {title, body, labels}")
    ap.add_argument("-R", "--repo", required=True, help="owner/name")
    ap.add_argument("--apply", action="store_true", help="create labels and issues (default: preview)")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between issue creates (default 2)")
    args = ap.parse_args(argv)

    try:
        with open(args.file) as fh:
            issues = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        c.die(f"cannot read {args.file}: {exc}")
    problems = validate(issues)
    if problems:
        for p in problems:
            c.err(p)
        c.die(f"{len(problems)} problem(s) in {args.file}")

    titles = [i["title"] for i in gh_json(
        ["issue", "list", "-R", args.repo, "--state", "all", "--limit", "5000", "--json", "title"], runner)]
    labels = [lab["name"] for lab in gh_json(
        ["label", "list", "-R", args.repo, "--limit", "1000", "--json", "name"], runner)]
    new_labels, to_create, skipped = plan(issues, titles, labels)

    c.info(f"{args.repo}: {len(to_create)} to create, {len(skipped)} already exist, "
           f"{len(new_labels)} new labels")
    for lab in new_labels:
        c.say(f"  label  {lab}")
    for issue in to_create:
        c.say(f"  issue  {issue['title']}  [{', '.join(issue.get('labels', []))}]")
    if not args.apply:
        c.say("Preview only. Re-run with --apply to create them.")
        return 2 if to_create or new_labels else 0
    if (to_create or new_labels) and not c.confirm(f"Create these in {args.repo}?"):
        c.die("Aborted.")

    for lab in new_labels:
        code, _, err = runner(["gh", "label", "create", lab, "-R", args.repo,
                               "--color", label_color(lab), "--force"])
        if code != 0:
            c.die(f"label {lab}: {err.strip()}")

    created, failed = 0, 0
    for n, issue in enumerate(to_create):
        if n:
            sleep(args.delay)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as body:
            body.write(issue["body"])
        cmd = ["gh", "issue", "create", "-R", args.repo, "--title", issue["title"],
               "--body-file", body.name]
        for lab in issue.get("labels", []):
            cmd += ["--label", lab]
        code, out, err = runner(cmd)
        os.unlink(body.name)
        if code == 0:
            created += 1
            c.ok(f"  {out.strip()}")
        else:
            failed += 1
            c.err(f"  failed: {issue['title']}: {err.strip()}")
    c.info(f"{args.repo}: created {created}, failed {failed}, skipped {len(skipped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
