package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func manifest(t *testing.T, root, name, content string) (string, []byte) {
	t.Helper()
	sum := sha256.Sum256([]byte(content))
	data, err := json.Marshal([]map[string]interface{}{{"path": name, "bytes": len(content), "sha256": hex.EncodeToString(sum[:])}})
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, "manifest.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return path, data
}

func TestValidManifestAndUnchangedInputs(t *testing.T) {
	root := t.TempDir()
	os.WriteFile(filepath.Join(root, "file ü.txt"), []byte("hello"), 0600)
	path, before := manifest(t, root, "file ü.txt", "hello")
	var out, stderr bytes.Buffer
	if code := run([]string{"--root", root, "--manifest", path}, &out, &stderr); code != 0 || !strings.Contains(out.String(), `"verified":1`) {
		t.Fatalf("code=%d %s %s", code, &out, &stderr)
	}
	after, _ := os.ReadFile(path)
	if !bytes.Equal(before, after) {
		t.Fatal("manifest changed")
	}
	file, _ := os.ReadFile(filepath.Join(root, "file ü.txt"))
	if string(file) != "hello" {
		t.Fatal("file changed")
	}
}

func TestMissingChangedAndDirectoryFindings(t *testing.T) {
	for _, kind := range []string{"missing", "changed", "directory"} {
		t.Run(kind, func(t *testing.T) {
			root := t.TempDir()
			path, _ := manifest(t, root, "item", "expected")
			if kind == "changed" {
				os.WriteFile(filepath.Join(root, "item"), []byte("tampered"), 0600)
			}
			if kind == "directory" {
				os.Mkdir(filepath.Join(root, "item"), 0700)
			}
			var out bytes.Buffer
			if code := run([]string{"--root", root, "--manifest", path}, &out, &bytes.Buffer{}); code != 1 || !strings.Contains(out.String(), `"verified":0`) {
				t.Fatal(code, &out)
			}
		})
	}
}

func TestUnsafeManifestPathsAndDuplicateFields(t *testing.T) {
	digest := strings.Repeat("0", 64)
	for _, path := range []string{"../outside", "/absolute", "C:/private", "a\\b", "a/../b", "a//b", "", "."} {
		data, _ := json.Marshal([]map[string]interface{}{{"path": path, "bytes": 0, "sha256": digest}})
		if _, err := readManifest(data); err == nil {
			t.Fatalf("accepted unsafe path %q", path)
		}
	}
	for _, data := range []string{`null`, `{}`, `[{}]`, `[null]`, `[] {}`, `[{"path":"a","path":"b","bytes":0,"sha256":"` + digest + `"}]`,
		`[{"path":"a","bytes":null,"sha256":"` + digest + `"}]`, `[{"path":"a","bytes":-1,"sha256":"` + digest + `"}]`,
		`[{"path":"a","bytes":0,"sha256":"bad"}]`, `[{"path":"a","bytes":0,"sha256":"` + digest + `","extra":1}]`} {
		if _, err := readManifest([]byte(data)); err == nil {
			t.Fatalf("accepted malformed manifest %s", data)
		}
	}
}

func TestDuplicatePathsRejected(t *testing.T) {
	_, data := manifest(t, t.TempDir(), "a", "")
	data = append(append(data[:len(data)-1], ','), data[1:]...)
	if _, err := readManifest(data); err == nil {
		t.Fatal("accepted duplicate path")
	}
}

func TestRootConfinesSymlinkTargets(t *testing.T) {
	root, other := t.TempDir(), t.TempDir()
	os.WriteFile(filepath.Join(other, "secret"), []byte("SECRET"), 0600)
	if err := os.Symlink(other, filepath.Join(root, "escape")); err != nil {
		t.Skip("symlink creation unavailable: ", err)
	}
	path, _ := manifest(t, root, "escape/secret", "SECRET")
	var out bytes.Buffer
	if code := run([]string{"--root", root, "--manifest", path}, &out, &bytes.Buffer{}); code != 1 || strings.Contains(out.String(), "SECRET") {
		t.Fatalf("escape was not refused: code=%d %s", code, &out)
	}
}

func TestInternalRelativeSymlinksAreAllowed(t *testing.T) {
	root := t.TempDir()
	os.WriteFile(filepath.Join(root, "inside"), []byte("hello"), 0600)
	if err := os.Symlink("inside", filepath.Join(root, "alias")); err != nil {
		t.Skip("symlink creation unavailable: ", err)
	}
	path, _ := manifest(t, root, "alias", "hello")
	if code := run([]string{"--root", root, "--manifest", path}, &bytes.Buffer{}, &bytes.Buffer{}); code != 0 {
		t.Fatal(code)
	}
}

func TestTotalReadBudgetAndEmptyManifest(t *testing.T) {
	root := t.TempDir()
	os.WriteFile(filepath.Join(root, "a"), []byte("hello"), 0600)
	path, _ := manifest(t, root, "a", "hello")
	var out bytes.Buffer
	if code := run([]string{"--root", root, "--manifest", path, "--max-bytes", "4"}, &out, &bytes.Buffer{}); code != 2 || out.Len() != 0 {
		t.Fatal(code, &out)
	}
	os.WriteFile(path, []byte("[]"), 0600)
	if code := run([]string{"--root", root, "--manifest", path}, &out, &bytes.Buffer{}); code != 0 {
		t.Fatal(code)
	}
}

func TestInvalidArgumentsAndHelp(t *testing.T) {
	for _, args := range [][]string{nil, {"--root", "missing", "--manifest", "missing"}, {"--root", "a", "--manifest", "b", "--max-bytes", "0"}, {"--root", "a", "--manifest", "b", "extra"}} {
		var out bytes.Buffer
		if code := run(args, &out, &bytes.Buffer{}); code != 2 || out.Len() != 0 {
			t.Fatal(code, &out)
		}
	}
	if code := run([]string{"--help"}, &bytes.Buffer{}, &bytes.Buffer{}); code != 0 {
		t.Fatal(code)
	}
}

func TestManifestEntryLimit(t *testing.T) {
	var data strings.Builder
	data.WriteString("[")
	for index := 0; index < 10001; index++ {
		if index > 0 {
			data.WriteString(",")
		}
		fmt.Fprintf(&data, `{"path":"file-%d","bytes":0,"sha256":"%s"}`, index, strings.Repeat("0", 64))
	}
	data.WriteString("]")
	if _, err := readManifest([]byte(data.String())); err == nil || !strings.Contains(err.Error(), "10000") {
		t.Fatalf("entry limit not enforced: %v", err)
	}
}

func TestBudgetIsSharedAcrossFiles(t *testing.T) {
	root := t.TempDir()
	os.WriteFile(filepath.Join(root, "a"), []byte("abc"), 0600)
	os.WriteFile(filepath.Join(root, "b"), []byte("abc"), 0600)
	_, data := manifest(t, root, "a", "abc")
	rows, err := readManifest(data)
	if err != nil {
		t.Fatal(err)
	}
	second := rows[0]
	second.Path = "b"
	rows = append(rows, second)
	opened, err := os.OpenRoot(root)
	if err != nil {
		t.Fatal(err)
	}
	defer opened.Close()
	if _, _, err := verify(opened, rows, 5); err == nil {
		t.Fatal("aggregate hashing limit bypassed")
	}
}
