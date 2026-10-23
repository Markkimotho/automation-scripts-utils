# Automation library architecture

Automation entries live under `scripts/<domain>/<topic>/<script-id>/` with `README.md`, `metadata.yaml`, and a runnable implementation. Shared reusable code belongs under `packages/`; verification under `quality/tests/`; CLI under `tools/cli/`.

## Migration policy

Existing `bin/` commands remain usable until all callers, documentation, tests, and workflows have been updated. Move scripts by domain, preserve their executable names, and update relative imports and shell sourcing. Keep a compatibility shim only when necessary, with a documented deprecation window.

## Domain map

- `developer-tools/git/`: Git and GitHub automation
- `developer-tools/environments/`: project bootstrapping and virtual environments
- `developer-tools/dependencies/`: polyglot dependency checks
- `data-engineering/conversion/`: data conversion
- `system-administration/maintenance/`: housekeeping and process utilities
- `security-compliance/scanning/`: secret and vulnerability checks
- `backup-recovery/snapshots/`: snapshots

Never auto-execute scripts during catalog discovery. Destructive scripts require explicit confirmation and should provide dry-run support.
