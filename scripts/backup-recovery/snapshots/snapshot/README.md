# Snapshot

Timestamped `tar.gz` of a directory before a risky operation.

**Category:** backup-recovery / snapshots  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash  
**Permissions:** filesystem-read

## Usage

```bash
bash scripts/backup-recovery/snapshots/snapshot/snapshot.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
