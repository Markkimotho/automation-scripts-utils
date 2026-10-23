# OpenAPI Operation Inventory

Inventory OpenAPI JSON operations, flag missing or duplicate IDs and report declared anonymous access without fetching references.

Build API endpoint inventories and review documentation-level authentication declarations before deployment or integration.

## Requirements and inputs

Node.js >=18; built-in modules only. Verified locally on macOS; other platforms are not yet declared supported.

OpenAPI 3.0.x or 3.1.x JSON with a paths object; UTF-8, maximum 8 MiB and 10000 operations.

## Run

```bash
automation run openapi-operation-inventory -- --input ./openapi.json
```

Output is JSON on stdout. Library-level `--dry-run` before `--` previews the command without reading files.

## Options

| Option | Meaning |
| --- | --- |
| `--input PATH` | Required local OpenAPI JSON document. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```json
{"operations":[{"path":"/health","method":"get","operation_id":"health","deprecated":false,"anonymous_allowed_by_spec":true}],"findings":[],"unresolved_path_refs":[]}
```

## Safety and limitations

No network access, endpoint calls, schema execution or generated code. Reads bounded local JSON and emits operation metadata. Route names and operation IDs may still be sensitive.

- Not a complete OpenAPI validator. YAML, OpenAPI 2.0/3.2, callbacks and webhooks are outside this tool’s contract.
- No local or remote $ref is resolved. Path-item references are listed and cause exit 1, so an incomplete inventory is visible.
- The anonymous flag follows root/operation security declarations, including empty alternatives; it does not prove a live endpoint permits access.
- Includes standard HTTP operation fields only. Vendor extensions and descriptions are ignored; no request/response examples are printed.
- Node JSON parsing uses the last occurrence of duplicate JSON object keys; use a full schema/parser validation workflow when validating source specifications.

## Exit codes and troubleshooting

Exit 1 means missing/duplicate operation IDs or unresolved path items. Exit 2 means malformed/unsupported input, invalid inspected fields or limits. Fix the specification or use a full OpenAPI validator for schema validation.

- `0`: Preview or operation completed without report findings.
- `1`: Differences/findings, or Git backup execution failure.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
