# Gh Rename Org

Rename an organization. Checks you own it and the new name is free, opens the settings page (github.com has no rename API), waits until GitHub serves the new name, repoints remotes under `--scan-dir`, and lists files still naming the old org.

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, gh  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/developer-tools/git/gh-rename-org/gh-rename-org.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
