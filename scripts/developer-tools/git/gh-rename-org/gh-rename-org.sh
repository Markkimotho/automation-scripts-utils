#!/usr/bin/env bash
# gh-rename-org.sh — rename a GitHub organization safely and repoint local clones.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../../packages/common/common.sh
source "$SCRIPT_DIR/../../../../packages/common/common.sh"

usage() {
  cat <<'EOF'
gh-rename-org.sh — rename a GitHub organization safely and repoint local clones.

Usage:
  gh-rename-org.sh <old-org> <new-org> [options]

Options:
  -s, --scan-dir <dir>   Repoint 'origin'-style remotes of git repos under <dir>
                         (depth 3) from <old-org> to <new-org>. Repeatable.
  --remotes-only         Skip all GitHub steps; only repoint local remotes
  --timeout <seconds>    How long to wait for the rename (default: 900)
  -y, --yes              Skip confirmations
  -h, --help

What it does:
  1. Checks you are an owner of <old-org> and that <new-org> is free.
  2. Opens the org settings page. github.com has no API for renaming an
     organization, so you click "Rename organization" there.
  3. Waits until GitHub serves the org under <new-org> (same org id).
  4. Rewrites matching remotes under each --scan-dir.
  5. Lists repos and tracked files that still mention <old-org>
     (fix them with git-replace.sh).

After a rename the old name is free for anyone to register, and then GitHub's
redirects stop. Update every reference instead of relying on them.

Examples:
  gh-rename-org.sh ml-ai-ops kiongahq -s ~/kionga -s ~/mlops
  gh-rename-org.sh ml-ai-ops kiongahq --remotes-only -s ~/kionga
EOF
}

old="" new="" remotes_only=0 timeout=900
scan_dirs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--scan-dir) scan_dirs+=("$2"); shift 2;;
    --remotes-only) remotes_only=1; shift;;
    --timeout) timeout="$2"; shift 2;;
    -y|--yes) ASSUME_YES=1; shift;;
    -h|--help) usage; exit 0;;
    -*) usage; die "Unknown option: $1";;
    *)
      if [[ -z "$old" ]]; then old="$1"
      elif [[ -z "$new" ]]; then new="$1"
      else usage; die "Unexpected argument: $1"; fi
      shift;;
  esac
done

[[ -n "$old" && -n "$new" ]] || { usage; die "<old-org> and <new-org> are required."; }
[[ "$new" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,37}[A-Za-z0-9])?$ ]] || die "Invalid GitHub name: $new"
lc() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }
[[ "$(lc "$old")" != "$(lc "$new")" ]] || die "Names are the same (GitHub names are case-insensitive)."

# repoint_remotes <dir> — rewrite remotes of every git repo under <dir>.
repoint_remotes() {
  local root="$1" gitdir repo name url newurl changed=0
  [[ -d "$root" ]] || { warn "Not a directory, skipped: $root"; return 0; }
  while IFS= read -r gitdir; do
    repo="$(dirname "$gitdir")"
    while IFS= read -r name; do
      [[ -n "$name" ]] || continue
      url="$(git -C "$repo" remote get-url "$name")"
      newurl="$(printf '%s' "$url" | OLD="$old" NEW="$new" perl -pe 's{(github\.com[:/])\Q$ENV{OLD}\E/}{$1$ENV{NEW}/}i')"
      if [[ "$newurl" != "$url" ]]; then
        git -C "$repo" remote set-url "$name" "$newurl"
        ok "  $repo [$name] -> $newurl"
        changed=$((changed+1))
      fi
    done < <(git -C "$repo" remote)
  done < <(find "$root" -maxdepth 3 -name .git \( -type d -o -type f \) 2>/dev/null)
  say "  $changed remote(s) updated under $root"
}

# gh_field <endpoint> <jq> — print a field, or nothing if the call fails.
# gh prints the error body to stdout on a 404, so the exit status decides.
gh_field() {
  local out
  out="$(gh api "$1" -q "$2" 2>/dev/null)" || return 0
  printf '%s' "$out"
}

if [[ "$remotes_only" == "0" ]]; then
  gh_authed
  old_id="$(gh_field "orgs/$old" .id)"
  new_id="$(gh_field "users/$new" .id)"

  if [[ -n "$new_id" && "$new_id" == "$old_id" ]]; then
    ok "Already renamed: $old and $new are the same org."
  elif [[ -n "$new_id" ]]; then
    new_type="$(gh_field "users/$new" .type)"
    die "'$new' is already taken by another $new_type (id $new_id). Pick another name."
  else
    [[ -n "$old_id" ]] || die "Organization not found: $old"
    role="$(gh_field "user/memberships/orgs/$old" .role)"
    [[ "$role" == "admin" ]] || die "You must be an owner of $old (your role: ${role:-none})."
    repos="$(gh repo list "$old" --limit 1000 --json name -q '.[].name' | wc -l | tr -d ' ')"
    info "Rename organization $old -> $new ($repos repos, org id $old_id)"
    say  "  Repo links and git remotes redirect; ghcr packages move to the new name."
    say  "  The org page, API calls and github.io Pages under '$old' stop working."
    confirm "Open the settings page to rename it now?" || die "Aborted."
    settings="https://github.com/organizations/$old/settings/profile"
    say "Open: $settings"
    say "Then: Danger zone -> Rename organization -> enter '$new'."
    if [[ -t 0 ]] && command -v open >/dev/null 2>&1; then open "$settings"; fi

    info "Waiting up to ${timeout}s for GitHub to serve '$new'..."
    waited=0
    until [[ "$(gh_field "orgs/$new" .id)" == "$old_id" ]]; do
      (( waited < timeout )) || die "Timed out. Re-run this script once the rename is done."
      sleep "${GH_RENAME_ORG_POLL:-10}"; waited=$((waited+${GH_RENAME_ORG_POLL:-10}))
    done
    ok "GitHub now serves the org as $new."
  fi
fi

if [[ ${#scan_dirs[@]} -gt 0 ]]; then
  info "Repointing remotes from $old to $new"
  for d in "${scan_dirs[@]}"; do repoint_remotes "$d"; done

  info "Tracked files that still mention '$old':"
  for d in "${scan_dirs[@]}"; do
    [[ -d "$d" ]] || continue
    while IFS= read -r gitdir; do
      repo="$(dirname "$gitdir")"
      n="$( { git -C "$repo" grep -I -F -i -c -e "$old" 2>/dev/null || true; } | awk -F: '{s+=$NF} END{print s+0}')"
      [[ "$n" == "0" ]] || say "  $n  $repo   (git-replace.sh $old $new -C $repo)"
    done < <(find "$d" -maxdepth 3 -name .git \( -type d -o -type f \) 2>/dev/null)
  done
fi
ok "Done."
