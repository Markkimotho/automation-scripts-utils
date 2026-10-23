# Gh Pr Status

One table of every open PR with CI / review / mergeable state.

**Category:** developer-tools / git  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3, gh  
**Permissions:** filesystem-read

## Usage

```bash
python3 scripts/developer-tools/git/gh-pr-status/gh-pr-status.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
