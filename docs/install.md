# Install Automation Scripts & Utils

Python 3.10+ is required. Install directly from GitHub; no repository checkout is necessary.

## pipx (recommended)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install git+https://github.com/Markkimotho/automation-scripts-utils.git
automation list
```

Restart your terminal if the command is not found.

## Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install git+https://github.com/Markkimotho/automation-scripts-utils.git
automation list
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## Upgrade

```bash
pipx upgrade automation-scripts-utils
```

## Optional requirements

The CLI has no third-party runtime dependencies. Individual scripts may require Bash, Node.js, Go, Ruby, PowerShell or Python packages. For example, install Boto3 for the S3 audit with `pipx inject automation-scripts-utils boto3` and configure your AWS credentials.

**Note:** This project is installable from GitHub, but has not yet been published on PyPI.
