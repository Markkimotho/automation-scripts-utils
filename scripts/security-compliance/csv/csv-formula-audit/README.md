# CSV Formula Risk Audit

Locate formula-like CSV cell prefixes before spreadsheet import, reporting coordinates without exposing cell values.

Review untrusted CSV exports before opening them in spreadsheet applications.

## Requirements and inputs

Ruby >=2.6 with csv, json and optparse libraries. Verified locally on macOS; other platforms are not yet declared supported.

Comma-delimited UTF-8 CSV, optional BOM; maximum 16 MiB, 100000 records and 1000000 cells. Headers are scanned as ordinary cells.

## Run

```bash
automation run csv-formula-audit -- --input ./export.csv
```

Output is JSON on stdout. Library-level `--dry-run` before `--` previews the command without reading files.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required CSV export. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```json
{"rows":2,"cells":4,"finding_count":1,"findings":[{"row":2,"column":2,"reason":"formula-like-prefix"}],"truncated":false}
```

## Safety and limitations

Never executes formulas, starts a spreadsheet, rewrites data or prints cell contents. Fix exports at their source using an application-appropriate policy; this tool does not sanitize them.

- A heuristic risk audit, not a guarantee of safe spreadsheet import or a malware verdict. Different applications and locales interpret data differently.
- Flags leading =, +, -, @ after whitespace/Unicode compatibility normalization, and leading tab/CR/LF. Negative numeric values can be legitimate false positives.
- Quoted CSV fields are parsed before inspection; quoted line breaks and delimiters are supported. Other delimiters are not detected automatically.
- At most 1000 coordinates are emitted, but all findings within resource limits are counted. Row numbers identify CSV records, not physical lines.

## Exit codes and troubleshooting

Exit 1 means potentially risky prefixes. Exit 2 means malformed/unreadable UTF-8 CSV, missing runtime libraries or exceeded limits. Inspect flagged records in a safe text-oriented viewer.

- `0`: Preview or operation completed without report findings.
- `1`: Differences/findings, or Git backup execution failure.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
