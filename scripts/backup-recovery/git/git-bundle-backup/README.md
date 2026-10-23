# Git Bundle Backup

Preview or create a verified bundle of committed Git history and refs, refusing shallow repositories and existing output files.

Create a portable backup of committed repository history for offline storage or transfer.

## Requirements and inputs

Bash >=3.2, Git >=2.15 and Python >=3.10; standard OS tools. Verified locally on macOS; other platforms are not yet declared supported.

A trusted local Git repository with a committed HEAD and complete local history; a new output path in an existing parent directory.

## Run

```bash
automation run git-bundle-backup --yes -- --repository . --output ../project.bundle
```

The example previews the operation. To create files, append `--apply` after the script options. Keep `--yes` to explicitly approve the script’s write permissions. Library-level `--dry-run` before `--` previews the command without executing the script.

## Options

| Option | Meaning |
| --- | --- |
| `--repository DIR` | Required Git working tree or bare repository with committed HEAD. |
| `--output FILE` | Required new archive filename. |
| `--apply` | Create, verify and publish the bundle. |
| `--dry-run` | Explicit preview; mutually exclusive with --apply. |
| `--help` | Show usage without opening inputs. |

## Example output

Illustrative output; paths, sizes and hashes depend on input.

```text
Created verified bundle: /backups/project.bundle
```

## Safety and limitations

Default is preview. Add --apply to create a private archive; the CLI requires --yes. The repository is not changed, no remote is contacted and staging is cleaned up. Restore deliberately with git clone /path/to/project.bundle /path/to/new-directory.

- Bundles contain refs and reachable committed objects, not uncommitted working files, index state, configuration, hooks or general filesystem metadata.
- Shallow repositories are refused. Partial clones must already contain needed objects; transports and lazy fetching are disabled during the operation.
- Verification uses git bundle verify; a full restore is not performed by the tool. Integration tests restore fixture bundles.
- Publication uses Python os.link rather than ln directory semantics; the destination cannot be replaced or redirected into an existing directory.
- Requires a stable, trusted repository and output parent. Large histories need adequate disk space and may take time.

## Exit codes and troubleshooting

Exit 1 means Git creation/verification failed. Exit 2 means invalid arguments, missing dependencies, incomplete repository, collision or publication failure. Check local object completeness and choose a fresh output filename.

- `0`: Preview or operation completed without report findings.
- `1`: Differences/findings, or Git backup execution failure.
- `2`: Invalid or unreadable input, unsupported behavior, limits, collisions or I/O failure.
