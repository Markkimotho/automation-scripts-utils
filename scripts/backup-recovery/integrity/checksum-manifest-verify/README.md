# SHA-256 Manifest Verification

Verify local restored or transferred files against SHA-256 JSON manifests while confining file access to a selected directory.

Check backups, transferred assets and archived media against a previously trusted manifest. Accepts the array format produced by image-checksum-manifest.

## Requirements and input

Go >=1.24 with no third-party packages. Use a maintained Go release. Verified locally on macOS with Go 1.26.4; other platforms are not yet declared supported.

An 8 MiB maximum JSON array of at most 10000 unique objects, each with exactly path (relative forward-slash path), bytes (nonnegative integer), and sha256 (64 hexadecimal digits). Duplicate or unknown fields, duplicate paths, absolute paths, dot/parent traversal, backslashes and colon-qualified paths are rejected.

The library CLI compiles a temporary executable before running it. Go needs writable temporary storage and a build cache; the automation itself reads files without modifying them.

## Run

```bash
automation run checksum-manifest-verify -- --root ./restored --manifest ./manifest.json
```

To preview without compiling or reading input, add the library-level `--dry-run` before `--`. Script-specific options follow `--` or use declared `--param KEY=VALUE` options.

## Options

| Option | Meaning |
| --- | --- |
| `--manifest PATH` | Required JSON manifest. |
| `--root PATH` | Required directory containing the files to check. |
| `--max-bytes N` | Total hashing budget, default 2147483648 (2 GiB); range 1..1099511627776. |
| `--help` | Show usage without opening input files. |

## Example output

A matching one-file manifest produces:

```json
{"verified":1,"findings":[]}
```

## Safety and limitations

Opens files for reading through os.OpenRoot. The selected root itself may be a symlink and must be trusted. Files, manifests and backups are not modified or removed. Missing/nonregular/unsafe files produce findings; other read failures abort without reporting success.

- Requires Go 1.24 or newer for the traversal-resistant os.Root API. Use a currently maintained Go release.
- Relative symlinks resolving inside the selected root are allowed; symlinks escaping the root are refused. Absolute symlinks may be refused even if they point into the root.
- Use a stable directory tree. This does not defend against hostile mount changes, hard links, or special-file replacement races by another local process.
- Files absent from the manifest are ignored. Empty arrays are valid. This checks integrity relative to a trusted manifest, not authenticity or malware.
- A total hashing-budget failure returns exit 2 without a partial success report. Hashes are streamed rather than loading file contents into memory.

## Exit codes and troubleshooting

Use the same root-relative paths as the original manifest. Investigate changed or missing files before restoring or replacing data. Increase --max-bytes only for a known inventory; keep the manifest trusted separately.

- `0`: Inspection completed without findings.
- `1`: Validity, overlap or file-integrity findings.
- `2`: Invalid input, unreadable input, resource limit or compilation/execution error.
