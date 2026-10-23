# Dev Doctor

Report which required tools are present, with install hints. Non-zero if a core tool is missing.

**Category:** developer-tools / environments  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash  
**Permissions:** filesystem-read

## Usage

```bash
bash scripts/developer-tools/environments/dev-doctor/dev-doctor.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
