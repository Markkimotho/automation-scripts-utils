// Verify SHA-256 manifests using a traversal-resistant root, without changing files.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

type manifestRow struct {
	Path   string
	Bytes  int64
	SHA256 string
}
type findingRow struct {
	Path   string `json:"path"`
	Reason string `json:"reason"`
}

func readManifest(data []byte) ([]manifestRow, error) {
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	token, err := decoder.Token()
	if err != nil || token != json.Delim('[') {
		return nil, errors.New("manifest must be a JSON array")
	}
	rows := make([]manifestRow, 0)
	seen := make(map[string]bool)
	for decoder.More() {
		if len(rows) == 10000 {
			return nil, errors.New("more than 10000 manifest entries")
		}
		token, err = decoder.Token()
		if err != nil || token != json.Delim('{') {
			return nil, errors.New("manifest entries must be objects")
		}
		var row manifestRow
		fields := make(map[string]bool)
		for decoder.More() {
			token, err = decoder.Token()
			key, ok := token.(string)
			if err != nil || !ok || fields[key] {
				return nil, errors.New("duplicate or invalid manifest fields")
			}
			fields[key] = true
			switch key {
			case "path":
				err = decoder.Decode(&row.Path)
			case "sha256":
				err = decoder.Decode(&row.SHA256)
			case "bytes":
				var size *int64
				err = decoder.Decode(&size)
				if size == nil {
					return nil, errors.New("bytes must be an integer")
				}
				row.Bytes = *size
			default:
				return nil, errors.New("unknown manifest field")
			}
			if err != nil {
				return nil, errors.New("invalid manifest field type")
			}
		}
		if _, err = decoder.Token(); err != nil {
			return nil, errors.New("invalid manifest object")
		}
		if !fields["path"] || !fields["bytes"] || !fields["sha256"] || row.Bytes < 0 ||
			row.Path == "." || !fs.ValidPath(row.Path) || !filepath.IsLocal(filepath.FromSlash(row.Path)) || strings.ContainsAny(row.Path, "\\:\x00") {
			return nil, errors.New("require safe relative paths, nonnegative byte counts and SHA-256 values")
		}
		if seen[row.Path] {
			return nil, errors.New("duplicate manifest path")
		}
		seen[row.Path] = true
		digest, err := hex.DecodeString(row.SHA256)
		if err != nil || len(digest) != sha256.Size {
			return nil, errors.New("invalid SHA-256 hex digest")
		}
		row.SHA256 = strings.ToLower(row.SHA256)
		rows = append(rows, row)
	}
	if _, err = decoder.Token(); err != nil {
		return nil, errors.New("unterminated manifest")
	}
	if _, err = decoder.Token(); err != io.EOF {
		return nil, errors.New("trailing manifest data")
	}
	return rows, nil
}

func verify(root *os.Root, rows []manifestRow, maxBytes int64) (int, []findingRow, error) {
	verified := 0
	findings := make([]findingRow, 0)
	for _, row := range rows {
		name := filepath.FromSlash(row.Path)
		info, err := root.Stat(name)
		if err != nil || !info.Mode().IsRegular() {
			findings = append(findings, findingRow{row.Path, "missing-unreadable-or-unsafe"})
			continue
		}
		if info.Size() > maxBytes {
			return 0, nil, errors.New("total hashing byte limit exceeded")
		}
		file, err := root.Open(name)
		if err != nil {
			findings = append(findings, findingRow{row.Path, "missing-unreadable-or-unsafe"})
			continue
		}
		current, err := file.Stat()
		if err != nil || !current.Mode().IsRegular() {
			file.Close()
			findings = append(findings, findingRow{row.Path, "missing-unreadable-or-unsafe"})
			continue
		}
		hash := sha256.New()
		count, readErr := io.Copy(hash, io.LimitReader(file, maxBytes+1))
		closeErr := file.Close()
		if readErr != nil || closeErr != nil {
			return 0, nil, errors.New("cannot finish hashing input")
		}
		if count > maxBytes {
			return 0, nil, errors.New("total hashing byte limit exceeded")
		}
		maxBytes -= count
		if count != row.Bytes || hex.EncodeToString(hash.Sum(nil)) != row.SHA256 {
			findings = append(findings, findingRow{row.Path, "size-or-checksum-mismatch"})
		} else {
			verified++
		}
	}
	return verified, findings, nil
}

func run(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("checksum-manifest-verify", flag.ContinueOnError)
	flags.SetOutput(stderr)
	manifest := flags.String("manifest", "", "JSON path/bytes/sha256 array; maximum 8 MiB / 10000 entries")
	rootPath := flags.String("root", "", "directory containing files to verify (Go >=1.24)")
	maxBytes := flags.Int64("max-bytes", 2<<30, "total bytes to hash (1..1099511627776)")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0
		}
		return 2
	}
	fail := func(message string) int { fmt.Fprintln(stderr, "checksum-manifest-verify: "+message); return 2 }
	if *manifest == "" || *rootPath == "" || flags.NArg() != 0 || *maxBytes < 1 || *maxBytes > 1<<40 {
		return fail("require --manifest, --root, no positional arguments and max-bytes between 1 and 1099511627776")
	}
	info, err := os.Stat(*manifest)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 8<<20 {
		return fail("require a readable regular manifest no larger than 8 MiB")
	}
	file, err := os.Open(*manifest)
	if err != nil {
		return fail("cannot read manifest")
	}
	data, readErr := io.ReadAll(io.LimitReader(file, (8<<20)+1))
	closeErr := file.Close()
	if readErr != nil || closeErr != nil || len(data) > 8<<20 {
		return fail("cannot read manifest within the 8 MiB limit")
	}
	rows, err := readManifest(data)
	if err != nil {
		return fail(err.Error())
	}
	root, err := os.OpenRoot(*rootPath)
	if err != nil {
		return fail("cannot open root directory")
	}
	defer root.Close()
	verified, findings, err := verify(root, rows, *maxBytes)
	if err != nil {
		return fail(err.Error())
	}
	report := struct {
		Verified int          `json:"verified"`
		Findings []findingRow `json:"findings"`
	}{verified, findings}
	if err := json.NewEncoder(stdout).Encode(report); err != nil {
		return fail("cannot write report")
	}
	if len(findings) > 0 {
		return 1
	}
	return 0
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }
