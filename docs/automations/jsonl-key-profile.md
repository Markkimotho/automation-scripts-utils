# JSON Lines Key Profile

Stream JSON Lines to find invalid object records and missing top-level keys without printing record values.

Detect schema drift and malformed records in event streams or dataset exports before ingestion.

## Requirements and input

Python >=3.10 (standard library only). No third-party packages. Verified on macOS; Linux and Windows verification is pending.

UTF-8 JSON Lines; one object per nonblank physical line. A final newline is optional.

## Run

```bash
automation run jsonl-key-profile -- --input ./events.jsonl
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required JSON Lines file. |
| `--max-line-bytes N` | Includes newline; default 1048576, maximum 16777216. |
| `--max-records N` | Maximum physical lines including blanks; default 1000000. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"lines": 2, "records": 2, "blank_lines": 0, "invalid_count": 0, "invalid_lines": [], "truncated": false, "keys": {"id": {"present": 2, "missing": 0}}}
```

## Safety and limitations

Streams with a bounded line buffer. Reports key names and line numbers, never values. Key names may themselves be sensitive. Reaching a resource limit emits no partial success report.

- Counts top-level keys only; null values count as present.
- Rejects duplicate object keys at any depth, non-object records, malformed UTF-8, NaN and Infinity constants.
- At most 10000 distinct keys and 1000 invalid line numbers are retained. Blank lines are counted separately.

## Exit codes and troubleshooting

Exit 1 identifies invalid records. Exit 2 identifies unreadable input or exceeded limits. Fix the indicated records or deliberately adjust limits.

- `0`: Report completed without policy findings or differences.
- `1`: Findings, invalid records, differences or unhealthy data.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
