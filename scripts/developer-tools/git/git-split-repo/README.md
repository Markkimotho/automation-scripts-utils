# Git Split Repo

Extract files or directories into a new repo, keeping their commit history (via `git-filter-repo`). Paths can be moved, including to the root; the source repo is never modified. `--publish` creates the GitHub repo and pushes.

**Category:** developer-tools / git  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, git  
**Permissions:** filesystem-read

## Usage

```bash
bash scripts/developer-tools/git/git-split-repo/git-split-repo.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
