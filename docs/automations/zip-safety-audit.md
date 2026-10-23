# ZIP Safety Audit

Inspect ZIP member metadata for traversal, symlinks, duplicate paths, encryption and excessive declared expansion.

Inspect downloaded archives before choosing a trusted extraction tool.

## Requirements and input

Python >=3.10 (standard library only). No third-party packages. Verified on macOS; Linux and Windows verification is pending.

One ZIP archive no larger than 64 MiB; contents are never decompressed.

## Run

```bash
automation run zip-safety-audit -- --archive ./download.zip
```

The command produces JSON on stdout. To save it, redirect stdout to a new report file. The library-level `--dry-run` previews the command without reading the input; the script itself is read-only.

## Options

| Option | Meaning |
| --- | --- |
| `--archive PATH` | Required ZIP file. |
| `--max-bytes N` | Maximum declared uncompressed total; default 1073741824. |
| `--max-ratio N` | Maximum per-member expansion ratio; default 100. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative output; whitespace may differ.

```json
{"members": 1, "declared_bytes": 3, "findings": [{"member": 0, "name": "../escape", "reasons": ["unsafe-path", "nonportable-path"]}]}
```

## Safety and limitations

Never extracts or decompresses entries. Flags absolute and parent paths, Windows path hazards, special files, symlinks, encrypted members and suspicious metadata. A report without findings is not an assurance that extraction is safe.

- Metadata-only heuristic: does not verify CRCs, actual compressed streams, malware, recursive archives, or every filesystem collision.
- Case-insensitive duplicate detection can flag harmless names on case-sensitive filesystems.
- Memory is proportional to the ZIP central directory, bounded indirectly by the 64 MiB input limit.

## Exit codes and troubleshooting

Exit 2 means the ZIP cannot be parsed, opened, or fits outside the input limit. Adjust positive limits only when the expected data justifies it.

- `0`: Report completed without policy findings or differences.
- `1`: Findings, invalid records, differences or unhealthy data.
- `2`: Invalid arguments, unreadable input, unsupported format or resource limit.
