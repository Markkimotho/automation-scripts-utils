# Windows Services Report

Read Windows service names, display names and statuses, optionally filtered by service name.

**Runtime:** powershell  
**Supported platforms:** windows  
**Dependencies:** pwsh  
**Permissions:** filesystem-read

## Usage

```bash
automation info windows-services-report
automation run windows-services-report --dry-run
automation run windows-services-report -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. 

## Expected output

JSON service status records.
