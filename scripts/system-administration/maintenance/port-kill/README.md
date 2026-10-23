# Port Kill

Kill the process **listening** on a TCP port (not a client connected to it).

**Category:** system-administration / maintenance  
**Language:** bash  
**Platforms:** linux, macos  
**Dependencies:** bash, lsof  
**Permissions:** filesystem-write

## Usage

```bash
bash scripts/system-administration/maintenance/port-kill/port-kill.sh --help
```

See [the script reference](../../../../docs/reference.md) for arguments and examples. Review the script's effect before running it; this utility may change files, infrastructure, or repository state.

## Expected output

Command output; see --help and script reference.

## Testing

Run `bash tests/run_tests.sh` from the repository root. Network-dependent operations require separate, explicit integration verification.
