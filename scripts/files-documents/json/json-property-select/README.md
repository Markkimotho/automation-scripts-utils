# Json Property Select

Select a named top-level property from a JSON object using Node.js TypeScript stripping.

**Runtime:** typescript  
**Supported platforms:** linux, macos, windows  
**Dependencies:** node  
**Permissions:** filesystem-read

## Usage

```bash
automation info json-property-select
automation run json-property-select --dry-run
automation run json-property-select -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. Requires Node.js 22.6+ with type stripping support.

## Expected output

JSON value of the selected property.
