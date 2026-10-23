# CSV Key Reconciliation

Compare exact keys in two CSV exports, reporting missing records and duplicate identifiers without comparing other values.

Reconcile customer exports, migration results or inventory snapshots using one identifier column.

## Requirements and input

Ruby >=2.6 with csv, json, optparse and set standard libraries. No third-party packages. Verified on macOS; Linux and Windows verification is pending.

Two comma-delimited UTF-8 CSV files with unique nonempty headers, consistent row widths and a common named key column. UTF-8 BOM and quoted multiline fields are supported.

## Run

```bash
automation run csv-key-reconcile -- --left ./before.csv --right ./after.csv --key id
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--left PATH` | Required first CSV. |
| `--right PATH` | Required second CSV. |
| `--key COLUMN` | Required exact header name shared by both files. |
| `--max-rows N` | Maximum data rows per file; default 100000, range 1..1000000. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"left_rows": 1, "right_rows": 1, "common": 0, "only_left": ["old-id"], "only_right": ["new-id"], "duplicate_left": [], "duplicate_right": []}
```

## Safety and limitations

Reads both files and writes only to stdout. Output contains key values, which can be personal or confidential; handle the report accordingly. Does not merge or alter exports.

- Exact string comparison preserves case and surrounding whitespace; no numeric normalization or value comparison.
- Files are limited to 32 MiB each; memory grows with unique key count.
- Header-only CSVs are valid empty datasets; zero-byte files are invalid.

## Exit codes and troubleshooting

Exit 1 means keys differ or duplicates exist. Exit 2 means missing columns, malformed CSV, invalid UTF-8, unreadable files or exceeded limits.

- `0`: Report completed without policy findings or differences.
- `1`: Findings, invalid records, differences or unhealthy data.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
