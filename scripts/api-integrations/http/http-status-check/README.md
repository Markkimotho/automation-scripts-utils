# Http Status Check

Check HTTP response status and elapsed time for one URL with a configurable timeout.

**Runtime:** javascript  
**Supported platforms:** linux, macos, windows  
**Dependencies:** node  
**Permissions:** network-read

## Usage

```bash
automation info http-status-check
automation run http-status-check --dry-run
automation run http-status-check -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. 

## Expected output

JSON response status and latency.
