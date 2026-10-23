# Automation Scripts & Utils

**Discover useful automations. Install once. Run from anywhere.**

Automation Scripts & Utils is a multi-language command-line library for files, Git, cloud infrastructure, data, systems, security, networking, business and personal productivity.

[Documentation](https://markkimotho.github.io/automation-scripts-utils/) · [Browse scripts](https://markkimotho.github.io/automation-scripts-utils/scripts/) · [Issues](https://github.com/Markkimotho/automation-scripts-utils/issues)

## Install

Requires Python 3.10+. The recommended method is [pipx](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/Markkimotho/automation-scripts-utils.git
automation list
```

Alternatively, from a Python virtual environment:

```bash
python -m pip install git+https://github.com/Markkimotho/automation-scripts-utils.git
automation list
```

Install directly from GitHub; **the package is not yet published on PyPI**. Individual scripts may need additional runtimes or packages.

## Find and run scripts

```bash
automation search "git conflict"
automation list --category files-documents
automation list --language python --platform linux
automation info git-conflict-helper
automation run git-conflict-helper --dry-run
automation run git-conflict-helper -- --help
```

The CLI preview `--dry-run` prints a command without executing it. Scripts with write permissions request confirmation before execution. Use `--yes` only to explicitly approve an operation.

## Available tasks

| Domain | Examples |
| --- | --- |
| Files and documents | Folder inventory, JSON validation, file organization |
| Git and developer tools | Conflict guidance, branch cleanup, GitHub operations |
| Data and AI | CSV profiling, dataset utilities |
| Cloud and infrastructure | AWS S3 audit, Terraform workspaces |
| System administration | Windows service status, system cleanup |
| Networking | HTTP and TCP checks |
| Business and messaging | Invoice due reports, email header inspection |
| Backup and security | Incremental file copying, permission auditing |
| Web and media | Page link export, image checksum manifests |

Python, Bash, PowerShell, JavaScript, TypeScript, Go and Ruby are supported, depending on the script.

## Documentation

- [Installation](https://markkimotho.github.io/automation-scripts-utils/install/)
- [Script catalog](https://markkimotho.github.io/automation-scripts-utils/scripts/)
- [CLI reference](https://markkimotho.github.io/automation-scripts-utils/cli/)
- [Permissions and safety](https://markkimotho.github.io/automation-scripts-utils/safety/)
- [Dependencies](https://markkimotho.github.io/automation-scripts-utils/prerequisites/)

The library continues growing with **no fixed maximum script count**.

## License

[MIT](LICENSE).
