#!/usr/bin/env bash
# py-venv-rebuild.sh — rebuild a Python virtualenv whose interpreter went stale
# (e.g. the base Python was removed/moved, so .venv/bin/python is a dangling link).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
py-venv-rebuild.sh — recreate a virtualenv and reinstall requirements.

Usage:
  py-venv-rebuild.sh [options]

Options:
  --python <bin|version>   Interpreter to build with. A path, or a version like
                           3.12.4 (resolved via pyenv, then pythonX.Y, python3).
  --venv <dir>             Venv directory (default: .venv)
  -r, --requirements <f>   Requirements file (default: requirements.txt if present)
  -y, --yes                Skip the delete confirmation
  -h, --help

Detects a broken venv (interpreter won't run) and rebuilds it from scratch.
EOF
}

py_spec="" venv=".venv" reqs=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) py_spec="$2"; shift 2;;
    --venv) venv="$2"; shift 2;;
    -r|--requirements) reqs="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) usage; die "Unexpected argument: $1";;
  esac
done

[[ -z "$reqs" && -f requirements.txt ]] && reqs="requirements.txt"

# Resolve the interpreter.
resolve_python() {
  local spec="$1"
  if [[ -z "$spec" ]]; then command -v python3 || command -v python; return; fi
  if [[ -x "$spec" ]]; then echo "$spec"; return; fi
  if [[ "$spec" =~ ^[0-9]+\.[0-9]+ ]]; then
    [[ -x "$HOME/.pyenv/versions/$spec/bin/python" ]] && { echo "$HOME/.pyenv/versions/$spec/bin/python"; return; }
    local mm="${spec%.*}"
    command -v "python$mm" 2>/dev/null && return
  fi
  command -v "$spec" 2>/dev/null && return
  command -v python3
}

py="$(resolve_python "$py_spec" || true)"
[[ -n "$py" && -x "$py" ]] || die "Could not resolve a Python interpreter (--python)."

# Is the existing venv broken?
if [[ -d "$venv" ]]; then
  if "$venv/bin/python" --version >/dev/null 2>&1; then
    warn "Existing venv at '$venv' still works."
  else
    warn "Existing venv at '$venv' is broken (interpreter won't run)."
  fi
  confirm "Delete and rebuild '$venv' using $("$py" --version 2>&1)?" || die "Aborted."
  rm -rf "$venv"
fi

info "Creating venv with: $py ($("$py" --version 2>&1))"
"$py" -m venv "$venv"
"$venv/bin/python" -m pip install --quiet --upgrade pip

if [[ -n "$reqs" && -f "$reqs" ]]; then
  info "Installing requirements from $reqs"
  "$venv/bin/pip" install --quiet -r "$reqs"
  ok "Installed dependencies."
else
  warn "No requirements file — created an empty venv."
fi
ok "Venv ready: $venv  (activate with: source $venv/bin/activate)"
