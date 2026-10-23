"""common.py — shared helpers for the Python automation scripts.

Import from a script in bin/:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
    import common as c
"""
import os
import sys
import shutil
import subprocess

_TTY = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code):
    return code if _TTY else ""


RED, GRN, YEL, BLU, DIM, RST = (_c(f"\033[{n}m") for n in ("31", "32", "33", "34", "2", "0"))


def say(m=""):
    print(m)


def info(m):
    print(f"{BLU}{m}{RST}")


def ok(m):
    print(f"{GRN}{m}{RST}")


def warn(m):
    print(f"{YEL}{m}{RST}", file=sys.stderr)


def err(m):
    print(f"{RED}{m}{RST}", file=sys.stderr)


def die(m, code=1):
    err(m)
    sys.exit(code)


def have(cmd):
    """True if an executable is on PATH."""
    return shutil.which(cmd) is not None


def confirm(prompt="Proceed?"):
    """Return True on yes. Honors ASSUME_YES=1; refuses on a non-TTY otherwise."""
    if os.environ.get("ASSUME_YES") == "1":
        return True
    if not sys.stdin.isatty():
        warn(f"Not a TTY and ASSUME_YES != 1 — refusing: {prompt}")
        return False
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def run(args, cwd=None, check=False):
    """Run a command; return (returncode, stdout, stderr)."""
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        die(f"command failed: {' '.join(args)}\n{p.stderr.strip()}")
    return p.returncode, p.stdout, p.stderr


def repo_root(start="."):
    rc, out, _ = run(["git", "-C", start, "rev-parse", "--show-toplevel"])
    return out.strip() if rc == 0 else os.path.abspath(start)


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def print_table(headers, rows):
    """Print a simple left-aligned text table."""
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for r in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(str(r[i])))

    def fmt(r):
        return "  ".join(str(r[i]).ljust(widths[i]) for i in range(cols))

    print(fmt(headers))
    print("  ".join("-" * widths[i] for i in range(cols)))
    for r in rows:
        print(fmt(r))


# ── Manifest detection for the polyglot (cross-language) tools ──────────────
# These tools are written in Python but operate on any ecosystem's files.
MANIFESTS = {
    "python": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"],
    "node":   ["package.json"],
    "go":     ["go.mod"],
    "rust":   ["Cargo.toml"],
    "ruby":   ["Gemfile"],
    "maven":  ["pom.xml"],
}

# manifest -> candidate lockfiles (None = no separate lockfile concept)
LOCKFILES = {
    "requirements.txt": [],
    "pyproject.toml": ["poetry.lock", "uv.lock", "pdm.lock"],
    "Pipfile": ["Pipfile.lock"],
    "package.json": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
    "go.mod": ["go.sum"],
    "Cargo.toml": ["Cargo.lock"],
    "Gemfile": ["Gemfile.lock"],
}


def detect_manifests(root="."):
    """Return {ecosystem: [manifest filenames present]} for the given dir."""
    found = {}
    for eco, names in MANIFESTS.items():
        present = [n for n in names if os.path.isfile(os.path.join(root, n))]
        if present:
            found[eco] = present
    return found
