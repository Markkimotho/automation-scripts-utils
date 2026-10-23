# Py Venv Rebuild

Rebuild a virtualenv whose interpreter went stale; reinstall requirements.

**Category:** developer-tools / environments  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/developer-tools/environments/py-venv-rebuild/py-venv-rebuild.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
