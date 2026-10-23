# Git Conflict Helper

Rule-based guide to merge/rebase conflicts. See [Resolving conflicts](conflicts.md).

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, git  
**Permissions:** filesystem-read

## Usage

```bash
bash scripts/developer-tools/git/git-conflict-helper/git-conflict-helper.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
