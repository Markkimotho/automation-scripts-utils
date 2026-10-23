# PostgreSQL Backup with Restore Verification

Create a custom-format database archive, restore it into a private disposable PostgreSQL instance, and publish the archive only after that restore succeeds. Use this to check a backup with a real restore rather than only listing archive metadata.

## Requirements and inputs

Python >=3.10, a maintained PostgreSQL >=15 installation with matching-major `postgres`, `initdb`, `pg_isready`, `psql`, `pg_dump` and `pg_restore` tools, and a non-root POSIX account. Put the tools on PATH for the library CLI; `--pg-bin` can select a particular matching installation. Locally verified on macOS/PostgreSQL 15.17; Linux qualification runs in CI. Windows and root execution are refused.

Supply a trusted source database, explicit username/host, and a new archive filename in an existing trusted directory. Database/user names must be simple ASCII identifiers (up to 63 characters); connection URIs and embedded passwords are rejected.

Provide credentials through `PGPASSFILE` (preferred, appropriately private) or `PGPASSWORD`. Without an explicit passfile the tool uses the null device, so it does not search a default password file. Selected TLS certificate settings are forwarded to the source client; endpoint/service environment overrides are discarded. Credentials are never forwarded to the verification cluster or printed.

## Run

Preview without connecting to a server or creating files:

```bash
automation run postgres-verified-backup --yes -- --database appdb --username backup_reader --host db.example.org --output ./appdb.dump
```

Append `--apply` to perform the backup and private restore. Library-level `--dry-run` before `--` previews only the launch command.

The source role needs read access to all dumped objects. Configure a read-only backup role rather than granting extra privileges automatically. Source connections request read-only transactions; row-level security or inaccessible objects can make the dump fail.

## Options

| Option | Meaning |
| --- | --- |
| `--database NAME` | Required source database name. |
| `--username NAME` | Required source login role. |
| `--host HOST` | Required hostname, IP address or absolute Unix socket directory without whitespace. |
| `--output PATH` | Required new archive; existing files, directories and symlinks are refused. |
| `--port N` | Source port, default 5432; range 1..65535. |
| `--pg-bin DIR` | Directory with the complete matching PostgreSQL toolchain. |
| `--sslmode MODE` | Default verify-full; also verify-ca, require, disable or prefer. Unix-socket connections ignore TLS mode. |
| `--timeout SECONDS` | Total working deadline, default 120; finite and greater than 0, at most 600. Cleanup can take additional time. |
| `--max-bytes N` | Uncompressed archive-byte budget, default 1073741824; maximum 1099511627776. |
| `--apply` | Create and verify the archive. |
| `--dry-run` | Explicit preview; mutually exclusive with --apply. |
| `--help` | Show usage without connecting. |

## Example output

Illustrative values:

```json
{"apply":true,"output":"/backups/appdb.dump","bytes":2048,"restore_verified":true,"verified_tables":1,"postgres_major":15}
```

## Safety and restore scope

- Default is preview. Writing requires `--apply`, plus `--yes` through the library CLI. Existing outputs are never replaced.
- The temporary verification instance uses a private 0700 directory under /tmp and Unix sockets only, with TCP listening disabled. It does not connect to or modify an existing destination database. It is stopped and removed after verification, including handled failures.
- Restore clients log in as a new non-superuser with no role/database creation privileges. Source authentication settings are removed from that environment. A private administrative role is used only to create the disposable database and verifier account.
- Only restore trusted source schemas. This is not a general sandbox for hostile SQL, a PostgreSQL security certification, or a guarantee that every application invariant is preserved. Extensions/custom objects needing elevated privileges or unavailable packages may deliberately fail verification.
- Backs up one database's schema and data; ownership/ACLs are omitted for portability. Cluster-wide roles, tablespaces and external dependencies are not backed up. Future restores still need a compatible toolchain and required extensions.
- The archive is streamed with a byte budget, written privately (0600 on POSIX), and published using a same-filesystem hard link after verification. Hard-link support and enough space for the dump and restored database are required.
- Restore resources use conservative memory settings; the archive budget does not cap total restored database/index size. Work on bounded trusted databases with adequate local disk space. Filesystem I/O and cleanup may exceed the working deadline.
- PostgreSQL diagnostics are suppressed because they can contain private data. Failures report the phase and leave no published success archive; inspect runtime/version, access, extension and resource requirements independently.

## Exit codes and troubleshooting

- `0`: preview or completed verified archive.
- `2`: invalid input, missing/incompatible toolchain, unavailable source, failed restore, limits, permissions or collision.

Use a fresh output filename. A source newer than pg_dump, inaccessible tables/RLS, missing extensions, insufficient privileges, disk limits or an unsupported output filesystem can prevent acceptance. The tool never repairs a source database, deletes an existing backup, or grants source privileges.
