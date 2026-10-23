# Email Attachment Extraction

Preview or extract decoded MIME attachments from one local email into sanitized, unique, non-overwriting files.

Save attachments from local .eml exports without opening an inbox or manually downloading individual files.

## Requirements and inputs

Python >=3.10; standard library only. Verified locally on macOS; other platforms are not yet declared supported.

One regular EML file up to 16 MiB. Non-multipart parts with a filename or attachment disposition are selected. Output must be a new or existing non-symlink directory in a trusted existing parent.

## Run

```bash
automation run eml-attachment-extract --yes -- --input ./message.eml --output ./attachments
```

The example previews the operation. To create files, append `--apply` after the script options. Keep `--yes` to explicitly approve the script’s write permissions. Library-level `--dry-run` before `--` previews the command without executing the script.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required local .eml file. |
| `--output DIR` | Required extraction directory; preview does not create it. |
| `--apply` | Create new output files. |
| `--dry-run` | Explicit preview; mutually exclusive with --apply. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```json
{"apply":false,"files":[{"name":"attachment-0001-report.pdf","bytes":123,"content_type":"application/pdf","sha256":"<64 hexadecimal characters>"}]}
```

## Safety and limitations

Preview is the default. --apply writes new files and the library CLI requires --yes. No email bodies or attachment bytes are printed, and content is never executed or opened. Extracted files remain untrusted; filename/type/hash are metadata, not a security verdict.

- Filenames use deterministic numbered prefixes and sanitized basenames. Original directory components cannot select extraction paths; existing final files and symlinks are refused.
- Rejects multipart/embedded-message attachments, malformed MIME/transfer encodings, more than 1000 parts, more than 2000 boundary-like lines, or decoded data above 16 MiB.
- The boundary-line preflight is deliberately conservative and can reject text containing many lines beginning with --.
- No attachments is a successful empty plan and creates no directory. No decryption or remote resource retrieval is performed.
- Uses private staging and hard-link publication. Requires hard-link support and a trusted, stable output directory; hostile concurrent directory replacement is outside the contract.
- On a later publication failure, already completed files are retained and named on stderr; incomplete staging files are removed. Inspect those files before retrying.

## Exit codes and troubleshooting

Exit 2 covers invalid MIME, unsupported parts, collisions, unsafe output, permissions, limits or I/O failures. Existing files are not overwritten. If stderr lists completed files after a partial batch, preserve or inspect them deliberately before retrying.

- `0`: Preview or operation completed without report findings.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
