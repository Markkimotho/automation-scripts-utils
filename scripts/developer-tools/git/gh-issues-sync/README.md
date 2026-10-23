# Gh Issues Sync

Create issues from a JSON list of `{title, body, labels}`. Missing labels are created first (priority `P1`-`P3`, `area:*` and type labels get consistent colors); an issue whose title already exists, open or closed, is skipped, so re-runs never duplicate. Preview by default (exit 2 when there is something to create).

**Category:** developer-tools / git  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3, gh  
**Permissions:** filesystem-write

## Usage

```bash
python3 scripts/developer-tools/git/gh-issues-sync/gh-issues-sync.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
