# Secret Scan

Scan staged files (or given paths) for likely secrets; exits non-zero on a hit.

**Category:** security-compliance / scanning  
**Language:** python  
**Platforms:** linux, macos, windows  
**Dependencies:** python3  
**Permissions:** filesystem-read

## Usage

```bash
python3 scripts/security-compliance/scanning/secret-scan/secret-scan.py --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility is categorized as non-destructive, but may query local or remote information.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
