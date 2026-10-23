# PEM Certificate Expiry Report

Report expired, not-yet-valid and soon-expiring certificates in a local PEM bundle without contacting remote services.

Use before deploying certificate bundles or to monitor offline certificate inventories.

## Requirements and input

Go >=1.24 with no third-party packages. Use a maintained Go release. Verified locally on macOS with Go 1.26.4; other platforms are not yet declared supported.

One regular PEM file up to 8 MiB containing at most 512 X.509 CERTIFICATE blocks. Whitespace between blocks is allowed; private keys, other block types, nested markers and leading/trailing text are rejected.

The library CLI compiles a temporary executable before running it. Go needs writable temporary storage and a build cache; the automation itself reads files without modifying them.

## Run

```bash
automation run pem-expiry-report -- --input ./certificates.pem --warn-days 30
```

To preview without compiling or reading input, add the library-level `--dry-run` before `--`. Script-specific options follow `--` or use declared `--param KEY=VALUE` options.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required PEM bundle. |
| `--as-of RFC3339` | Observation time; default is the current UTC time. |
| `--warn-days N` | Warning window, default 30; range 0..36500. |
| `--help` | Show usage without opening input files. |

## Example output

Illustrative report for a certificate valid throughout 2030; the fingerprint depends on the actual certificate:

```json
{"as_of":"2030-01-01T00:00:00Z","certificates":[{"index":1,"sha256":"<64 hexadecimal characters>","not_before":"2029-01-01T00:00:00Z","not_after":"2031-01-01T00:00:00Z","remaining_seconds":31536000,"status":"valid"}],"findings":0}
```

## Safety and limitations

Reads local certificate data only. It does not contact issuers, load private keys, modify trust stores or renew certificates. Process a stable local file; filesystem I/O deadlines are controlled by the operating system.

- Date inspection does not verify certificate trust, signatures, DNS names, key usage or revocation.
- Expiry begins at the exact not_after instant. Dates at or before the warning-window boundary are expiring.
- Reports fingerprints and dates rather than subject names, SANs, certificate bytes or private material.

## Exit codes and troubleshooting

Fix malformed bundles or extract only certificate blocks using a trusted local workflow. Do not pass private-key bundles. Use --as-of for repeatable audits.

- `0`: Inspection completed without findings.
- `1`: Validity, overlap or file-integrity findings.
- `2`: Invalid input, unreadable input, resource limit or compilation/execution error.
