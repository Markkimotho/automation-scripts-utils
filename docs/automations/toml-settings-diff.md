# TOML Settings Comparison

Compare parsed TOML settings and report added, removed or changed key paths while omitting configuration values.

Review configuration drift between environments without displaying secret values in logs.

## Requirements and inputs

Python >=3.11 with tomllib; standard library only. Verified locally on macOS; other platforms are not yet declared supported.

Two UTF-8 TOML 1.0 files, each no larger than 2 MiB.

## Run

```bash
automation run toml-settings-diff -- --left ./development.toml --right ./production.toml
```

Output is JSON on stdout. Library-level `--dry-run` before `--` previews the command without reading files.

## Options

| Option | Meaning |
| --- | --- |
| `--left PATH` | Required original/reference configuration. |
| `--right PATH` | Required comparison configuration. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```json
{"changes":[{"path":["database","password"],"change":"changed"}],"count":1}
```

## Safety and limitations

Reads local files only and never imports or executes configuration content. Input files are unchanged. Use the library-level --dry-run to preview the command without parsing.

- Key names and paths are reported and may themselves be sensitive; values and parse-error details are omitted.
- Compares parsed meaning: whitespace, key order, numeric spelling and equivalent timezone instants are ignored.
- Arrays are compared as whole values with type-sensitive elements. NaN values compare consistently; booleans and integers remain distinct.
- At most 10000 changed paths are emitted; excessive nesting or changes fail without a partial report.
- Added/removed tables are reported at the table path. This is a comparator, not a configuration merger or validator for application-specific settings.

## Exit codes and troubleshooting

Exit 1 means differences. Exit 2 means unreadable/invalid input, limits, or Python older than 3.11. Check TOML syntax locally; error messages intentionally omit values.

- `0`: Preview or operation completed without report findings.
- `1`: Differences/findings, or Git backup execution failure.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
