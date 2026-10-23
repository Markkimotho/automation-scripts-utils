# Terraform Workspaces

List local Terraform workspaces for the selected project directory without changing state.

**Runtime:** bash  
**Supported platforms:** linux, macos  
**Dependencies:** bash, terraform  
**Permissions:** filesystem-read

## Usage

```bash
automation info terraform-workspaces
automation run terraform-workspaces --dry-run
automation run terraform-workspaces -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. 

## Expected output

Terraform workspace list.
