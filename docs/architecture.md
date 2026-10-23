# How it works

Install the `automation` command once, then discover and run automations from any working directory.

```bash
automation search "json"
automation info json-batch-validate
automation run json-batch-validate --dry-run
```

Each script declares its purpose, supported platforms, required tools and permissions. See [Installation](install.md), [Script directory](scripts.md) and [Safety](safety.md).
