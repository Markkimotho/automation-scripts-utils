# Git Sync

Catch up: fetch, fast-forward base, prune, rebase current branch. Refuses a dirty tree.

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, git  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/developer-tools/git/git-sync/git-sync.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
