# Clean Artifacts

Delete build/cache junk (`__pycache__`, `dist`, caches, `.DS_Store`, …). Dry-run by default.

**Category:** system-administration / maintenance  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/system-administration/maintenance/clean-artifacts/clean-artifacts.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
