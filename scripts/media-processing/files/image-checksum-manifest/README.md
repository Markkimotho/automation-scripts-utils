# Image Checksum Manifest

Recursively create a SHA-256 checksum manifest of image files for later integrity comparison.

**Runtime:** ruby  
**Supported platforms:** linux, macos, windows  
**Dependencies:** ruby  
**Permissions:** filesystem-read

## Usage

```bash
automation info image-checksum-manifest
automation run image-checksum-manifest --dry-run
automation run image-checksum-manifest -- --help
```

For additional arguments, see `--help`. The script does not require cloud credentials by default. 

## Expected output

JSON image paths, sizes and SHA-256 hashes.
