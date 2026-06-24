#!/usr/bin/env bash
# port-kill.sh — kill the process LISTENING on one or more TCP ports.
#
# By default it only targets listeners. This avoids a classic mistake: matching
# a process that merely holds an OUTBOUND connection to that port (e.g. a proxy
# connected to a backend) and killing the wrong thing.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

usage() {
  cat <<'EOF'
port-kill.sh — kill the process listening on TCP port(s).

Usage:
  port-kill.sh <port> [port...] [options]

Options:
  --all        Match ANY socket on the port (listeners + connections), not just listeners.
  -9, --force  Use SIGKILL instead of SIGTERM.
  -y, --yes    Skip confirmation.
  -h, --help

Examples:
  port-kill.sh 8080 8090        # free up two listener ports
  port-kill.sh 6380 --force -y
EOF
}

ports=() listen_only=1 sig=TERM
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) listen_only=0; shift;;
    -9|--force) sig=KILL; shift;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *) ports+=("$1"); shift;;
  esac
done

[[ "${#ports[@]}" -gt 0 ]] || { usage; die "At least one port required."; }
require_cmd lsof

all_pids=()
for port in "${ports[@]}"; do
  pids=()
  if [[ "$listen_only" == "1" ]]; then
    while IFS= read -r _p; do [[ -n "$_p" ]] && pids+=("$_p"); done \
      < <(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | sort -u)
  else
    while IFS= read -r _p; do [[ -n "$_p" ]] && pids+=("$_p"); done \
      < <(lsof -nP -iTCP:"$port" -t 2>/dev/null | sort -u)
  fi
  if [[ "${#pids[@]}" -eq 0 ]]; then
    say "port $port: nothing to kill"
    continue
  fi
  for pid in "${pids[@]}"; do
    cmd="$(ps -p "$pid" -o comm= 2>/dev/null || echo '?')"
    say "port $port: pid $pid ($cmd)"
    all_pids+=("$pid")
  done
done

[[ "${#all_pids[@]}" -gt 0 ]] || { ok "No matching processes."; exit 0; }

# de-dup
uniq_pids=()
while IFS= read -r _p; do [[ -n "$_p" ]] && uniq_pids+=("$_p"); done \
  < <(printf '%s\n' "${all_pids[@]}" | sort -u)
confirm "Send SIG$sig to ${#uniq_pids[@]} process(es)?" || die "Aborted."
kill "-$sig" "${uniq_pids[@]}" 2>/dev/null || true
ok "Sent SIG$sig to: ${uniq_pids[*]}"
