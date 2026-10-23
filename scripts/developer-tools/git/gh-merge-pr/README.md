# Gh Merge Pr

Merge a PR safely: polls mergeability, refuses `CONFLICTING`, confirms first.

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, gh  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/developer-tools/git/gh-merge-pr/gh-merge-pr.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
