# Data Convert

Convert between CSV, JSON, and YAML (YAML needs PyYAML).

**Category:** data-engineering / conversion  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3  
**Permissions:** filesystem-read

## Usage

```bash
python3 scripts/data-engineering/conversion/data-convert/data-convert.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
