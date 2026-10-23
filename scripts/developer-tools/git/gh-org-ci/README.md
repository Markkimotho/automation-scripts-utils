# Gh Org Ci

Latest GitHub Actions runs for every repo of an org (or `--repos`), one table, with the URL of each failed run. `--wait` polls until nothing is running; exit code 2 when any shown run failed.

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, gh  
**Permissions:** filesystem-read

## Usage

```bash
bash scripts/developer-tools/git/gh-org-ci/gh-org-ci.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
