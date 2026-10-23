# Gh Release

Bump version, build a changelog from commits since the last tag, tag, and release.

**Category:** developer-tools / git  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3, gh  
**Permissions:** filesystem-write

## Usage

```bash
python3 scripts/developer-tools/git/gh-release/gh-release.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
