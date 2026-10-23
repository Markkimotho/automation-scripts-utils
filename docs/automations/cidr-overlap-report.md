# CIDR Overlap Report

Find duplicate and nested IPv4 or IPv6 CIDR allocations offline, preserving input line numbers and normalizing host bits.

Check address plans, VPN allocations or firewall inventories before provisioning overlapping subnets.

## Requirements and input

Go >=1.24 with no third-party packages. Use a maintained Go release. Verified locally on macOS with Go 1.26.4; other platforms are not yet declared supported.

A UTF-8 text file up to 2 MiB with one IPv4 or IPv6 CIDR per line. Blank lines and whole-line # comments are ignored. Up to 4096 network records and 64 KiB per line are accepted; inline comments and zone identifiers are invalid.

The library CLI compiles a temporary executable before running it. Go needs writable temporary storage and a build cache; the automation itself reads files without modifying them.

## Run

```bash
automation run cidr-overlap-report -- --input ./networks.txt
```

To preview without compiling or reading input, add the library-level `--dry-run` before `--`. Script-specific options follow `--` or use declared `--param KEY=VALUE` options.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required network list. |
| `--max-findings N` | Maximum emitted pairs, default 1000; range 1..10000. All overlapping pairs are still counted. |
| `--help` | Show usage without opening input files. |

## Example output

For input lines 10.0.0.0/8 and 10.1.0.0/16:

```json
{"networks":[{"line":1,"prefix":"10.0.0.0/8"},{"line":2,"prefix":"10.1.0.0/16"}],"overlap_count":1,"overlaps":[{"left_line":1,"right_line":2,"kind":"containment"}],"truncated":false}
```

## Safety and limitations

Reads only the supplied file. It sends no packets, resolves no names and changes no routes or firewall rules. Reports include network allocations, which may be sensitive.

- IPv4 and IPv6 are separate address families; IPv4-mapped IPv6 prefixes remain IPv6.
- Host bits are masked before comparison, so differently written allocations can become duplicates.
- All pairs are compared; the 4096-record limit bounds the quadratic work. Output pairs retain input order.
- Empty/comment-only input is a valid empty allocation list.

## Exit codes and troubleshooting

Check the reported invalid line number. Use explicit CIDR notation rather than hostnames, inline comments or interface zones. Split larger allocation inventories deliberately if the record limit is exceeded.

- `0`: Inspection completed without findings.
- `1`: Validity, overlap or file-integrity findings.
- `2`: Invalid input, unreadable input, resource limit or compilation/execution error.
