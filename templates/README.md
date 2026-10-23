# Automation contribution templates

Templates are **examples**, not registered scripts. Copy a language skeleton into `scripts/<category>/<topic>/<id>/`, implement useful behavior, add metadata and tests, and register the actual executable in `catalog/scripts.json`. The catalog must never count placeholder templates.

Supported executable languages: Python, Bash, PowerShell, JavaScript, TypeScript, Go and Ruby. Declarative workflow examples cover SQL, YAML, Terraform and Ansible. Never embed credentials. Add script-specific dependencies and a safe default.
