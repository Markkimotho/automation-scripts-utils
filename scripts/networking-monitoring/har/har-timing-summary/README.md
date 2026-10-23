# HAR Timing Summary

Summarize offline HAR request timing, failures, status counts and body sizes while omitting URLs and payloads.

Inspect browser network captures for slow requests or failing responses before sharing aggregate diagnostics.

## Requirements and input

Node.js >=18 (built-in modules only). No third-party packages. Verified on macOS; Linux and Windows verification is pending.

HAR 1.2 JSON with log.entries; entries need finite nonnegative time, response status/bodySize and a timings object. At most 32 MiB and 100000 entries.

## Run

```bash
automation run har-timing-summary -- --input ./capture.har --slow-ms 1000
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required HAR 1.2 file. |
| `--slow-ms N` | Finite positive slow threshold in milliseconds; default 1000. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"requests": 0, "failed": 0, "slow": 0, "summed_request_ms": 0, "max_request_ms": 0, "known_body_bytes": 0, "unknown_body_sizes": 0, "status_counts": {}, "timing_ms": {}, "mean_request_ms": 0}
```

## Safety and limitations

Reads locally without network access. Report and errors omit URLs, headers, cookies, query parameters and response bodies. Original HAR files often contain secrets; this tool does not redact the original file.

- An aggregate reader, not full HAR schema validation; optional/missing timing components are ignored.
- Summed durations include overlapping requests and are not page-load wall time; SSL timing overlaps connect timing.
- Failure counts use status 0 or >=400; redirects are not classified as failures. Unknown body sizes (-1) are counted separately.

## Exit codes and troubleshooting

Exit 2 identifies unsupported HAR versions, malformed input, invalid timing/status/body-size data, nonpositive thresholds or exceeded limits. Response failures in a valid capture still return exit 0.

- `0`: Valid capture summarized, including any failed HTTP requests.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
