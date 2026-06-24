#!/usr/bin/env python3
"""gh-pr-status.py — one table of open PRs with CI / review / mergeable state."""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import common as c  # noqa: E402


def rollup_state(rollup):
    """Reduce a statusCheckRollup list to PASS / FAIL / PENDING / -."""
    if not rollup:
        return "-"
    states = []
    for item in rollup:
        # CheckRun uses 'conclusion'/'status'; StatusContext uses 'state'.
        s = (item.get("conclusion") or item.get("state") or item.get("status") or "").upper()
        states.append(s)
    if any(s in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED") for s in states):
        return "FAIL"
    if any(s in ("IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "") for s in states):
        return "PENDING"
    return "PASS"


def main():
    ap = argparse.ArgumentParser(
        description="Show open PRs with CI, review, and mergeable state in one table."
    )
    ap.add_argument("-r", "--repo", help="owner/name (default: current repo)")
    ap.add_argument("-a", "--author", help="filter by author, e.g. @me")
    args = ap.parse_args()

    if not c.have("gh"):
        c.die("gh not found. Install the GitHub CLI: https://cli.github.com")
    rc, _, _ = c.run(["gh", "auth", "status"])
    if rc != 0:
        c.die("gh is not authenticated. Run: gh auth login")

    cmd = [
        "gh", "pr", "list", "--state", "open", "--limit", "100",
        "--json", "number,title,headRefName,isDraft,mergeable,reviewDecision,statusCheckRollup,author",
    ]
    if args.repo:
        cmd += ["--repo", args.repo]
    if args.author:
        cmd += ["--author", args.author]

    rc, out, err = c.run(cmd)
    if rc != 0:
        c.die(err.strip() or "gh pr list failed")

    prs = json.loads(out or "[]")
    if not prs:
        c.ok("No open PRs.")
        return

    rows = []
    for p in prs:
        mergeable = "draft" if p.get("isDraft") else (p.get("mergeable") or "?").lower()
        review = (p.get("reviewDecision") or "-").lower().replace("_", " ")
        rows.append((
            f"#{p['number']}",
            c.trunc(p.get("title", ""), 42),
            c.trunc(p.get("headRefName", ""), 24),
            (p.get("author") or {}).get("login", "-"),
            mergeable,
            review,
            rollup_state(p.get("statusCheckRollup")),
        ))
    c.print_table(["PR", "Title", "Branch", "Author", "Mergeable", "Review", "CI"], rows)


if __name__ == "__main__":
    main()
