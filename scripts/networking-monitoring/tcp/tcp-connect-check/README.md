# Tcp Connect Check

Attempt one TCP connection to a specified host and port and return reachable status and latency.

**Runtime:** go  
**Supported platforms:** linux, macos, windows  
**Dependencies:** go  
**Permissions:** network-read

## Usage

```bash
automation info tcp-connect-check
automation run tcp-connect-check --dry-run
automation run tcp-connect-check -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. 

## Expected output

JSON reachability, host, port and elapsed milliseconds.
