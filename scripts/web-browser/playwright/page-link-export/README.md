# Page Link Export

Visit a user-supplied webpage using Playwright and export its visible anchor links as JSON.

**Runtime:** javascript  
**Supported platforms:** linux, macos, windows  
**Dependencies:** node  
**Permissions:** network-read

## Usage

```bash
automation info page-link-export
automation run page-link-export --dry-run
automation run page-link-export -- --help
```

For additional arguments, see `--help`. Install Playwright locally with `npm install` in this script folder and `npx playwright install chromium`. 

## Expected output

JSON list of page links.
