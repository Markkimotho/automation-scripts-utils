# npm Lockfile Policy Audit

Audit npm v2/v3 lock metadata for strong integrity, HTTPS sources, embedded credentials and lifecycle-script declarations offline.

Review supply-chain metadata before permitting a dependency installation in CI.

## Requirements and input

Node.js >=18 (built-in modules only). No third-party packages. Verified on macOS; Linux and Windows verification is pending.

npm package-lock.json lockfileVersion 2 or 3 with a packages object, at most 32 MiB and 100000 entries.

## Run

```bash
automation run npm-lock-audit -- --lockfile ./package-lock.json
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--lockfile PATH` | Required npm v2/v3 package lockfile. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"checked": 1, "skipped": 1, "findings": [{"path": "node_modules/example", "reasons": ["missing-or-weak-integrity", "non-https-or-missing-source"]}]}
```

## Safety and limitations

Never runs npm, installs dependencies, fetches URLs or executes hooks. Source URLs and embedded URL credentials are omitted from reports and errors. Package paths are included.

- Metadata policy only: does not verify downloaded content, package safety, advisories or manifest consistency.
- Root, link and bundled records are skipped. Git/file sources and SHA-1-only integrity are deliberately flagged.
- Lifecycle-script findings identify declarations, not maliciousness; a missing flag does not prove a package has no scripts.

## Exit codes and troubleshooting

Exit 1 means policy findings, which may include intentionally configured local or Git dependencies. Exit 2 means malformed or unsupported lock data, unreadable files or exceeded limits.

- `0`: Report completed without policy findings or differences.
- `1`: Findings, invalid records, differences or unhealthy data.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
