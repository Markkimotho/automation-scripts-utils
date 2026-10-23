# Security policy

Please report security vulnerabilities privately using GitHub's Security advisories for this repository if available. Do **not** publish working exploitation details or credentials in issues or pull requests.

## Safety expectations

Automation can change files, Git history, cloud resources, accounts and machines. Review each script and its declared permissions before running it. Treat catalog metadata as documentation, not as a sandbox. The CLI previews commands when `--dry-run` is set; executing a script can have real-world effects.

Never commit API keys, passwords, tokens, private SSH keys or `.env` contents. Prefer environment variables, platform-native identity or secret managers. Keep all destructive and externally mutating operations behind explicit confirmation. No stealthy monitoring, evasion or credential collection.

No script is guaranteed safe simply because CI passes. Users remain responsible for verifying the intended target and backups in their own environment.
