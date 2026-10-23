# Version Bump

Bump the project version in whatever manifest(s) the repo uses, atomically.

**Category:** developer-tools / dependencies  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3  
**Permissions:** filesystem-write

## Usage

```bash
python3 scripts/developer-tools/dependencies/version-bump/version-bump.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
