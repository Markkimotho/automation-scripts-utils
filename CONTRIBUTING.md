# Contributing automation scripts

Contributions should solve a practical, repeatable problem. **Do not submit scripts whose only purpose is increasing the catalog count.**

1. Choose an existing domain from `catalog/categories.yaml` and create `scripts/<domain>/<topic>/<unique-id>/`.
2. Add the executable in Python, Bash, PowerShell, JavaScript, TypeScript, Go or Ruby (or SQL, YAML, Terraform or Ansible as appropriate). Use a script-specific dependency manifest rather than requiring global installs.
3. Add `metadata.yaml` following `templates/metadata.yaml`, plus a README showing purpose, prerequisites, inputs, output, copyable usage examples, portability and safety implications.
4. Register a truthful entry with the same ID and entrypoint in `catalog/scripts.json`. Keep tags accurate; do not advertise permissions or dry-run support the implementation does not have.
5. Add deterministic tests. Mock remote services; do not contact cloud accounts, live web services or production databases in default CI.
6. Run `bash tests/run_tests.sh` and `python3 -m unittest discover -s tests -p 'test_*.py'`. If the toolchain is installed, validate other languages with their standard tooling.
7. Submit focused PRs. Describe use cases, security behavior, testing evidence, and platform support.

New discoveries and accepted additions must follow [the discovery and evidence workflow](research/README.md). Add a provenance record, independently review licensing and security, record passing test evidence, and declare only verified platforms. Regenerate the public directory with `python tools/generate_directory.py`; `--check` detects stale output. CI validates new acceptance records separately from the legacy catalog.

## Minimum quality bar

- Functionality is substantive and matches the description.
- No hardcoded secrets or credentials and no unauthorized data collection.
- Safe defaults: non-destructive preview if feasible; otherwise prompt before changes.
- Parameters validated, subprocess calls avoid shell interpolation, input paths handled safely.
- Tests cover common and error paths; network calls are mocked.
- Documentation and catalog metadata both exist and match implementation.
- License compatibility and attribution are explicit.
