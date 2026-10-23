package main

import (
	"bytes"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func cidrInput(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "networks.txt")
	if err := os.WriteFile(path, []byte(content), 0600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestNormalizationAndLineNumbers(t *testing.T) {
	rows, err := readNetworks(strings.NewReader("# comment\n\n10.0.0.4/24\n 2001:db8::1/32 \n"))
	if err != nil || len(rows) != 2 || rows[0].Line != 3 || rows[0].Prefix.String() != "10.0.0.0/24" || rows[1].Prefix.String() != "2001:db8::/32" {
		t.Fatalf("%+v %v", rows, err)
	}
}

func TestOverlapCountsTruncationAndFamilies(t *testing.T) {
	path := cidrInput(t, "10.0.0.0/8\n10.1.0.0/16\n10.1.0.1/16\n2001:db8::/32\n::ffff:10.1.0.0/112\n")
	var out, stderr bytes.Buffer
	code := run([]string{"--input", path, "--max-findings", "1"}, &out, &stderr)
	var report struct {
		OverlapCount int          `json:"overlap_count"`
		Truncated    bool         `json:"truncated"`
		Overlaps     []overlapRow `json:"overlaps"`
	}
	if err := json.Unmarshal(out.Bytes(), &report); err != nil {
		t.Fatal(err, &stderr)
	}
	if code != 1 || report.OverlapCount != 3 || !report.Truncated || len(report.Overlaps) != 1 {
		t.Fatalf("code=%d %+v", code, report)
	}
}

func TestDuplicateClassificationAndAdjacentNetworks(t *testing.T) {
	path := cidrInput(t, "192.0.2.1/24\n192.0.2.0/24\n192.0.3.0/24\n")
	var out bytes.Buffer
	if code := run([]string{"--input", path}, &out, &bytes.Buffer{}); code != 1 || !strings.Contains(out.String(), `"kind":"duplicate"`) {
		t.Fatal(code, &out)
	}
	path = cidrInput(t, "0.0.0.0/1\n128.0.0.0/1\n::/0\n")
	if code := run([]string{"--input", path}, &bytes.Buffer{}, &bytes.Buffer{}); code != 0 {
		t.Fatal(code)
	}
}

func TestEmptyInputIsValid(t *testing.T) {
	var out bytes.Buffer
	if code := run([]string{"--input", cidrInput(t, "# nothing\n")}, &out, &bytes.Buffer{}); code != 0 || !strings.Contains(out.String(), `"networks":[]`) {
		t.Fatal(code, &out)
	}
}

func TestInvalidPrefixesAndResourceLimits(t *testing.T) {
	for _, text := range []string{"host.example/24\n", "10.0.0.1/33\n", "fe80::1%zone/64\n", "10.0.0.1/24 # inline\n", strings.Repeat("a", 65537), strings.Repeat("10.0.0.0/8\n", 4097)} {
		if _, err := readNetworks(strings.NewReader(text)); err == nil {
			t.Fatalf("accepted invalid input of %d bytes", len(text))
		}
	}
}

func TestInvalidArgumentsHaveNoPartialReport(t *testing.T) {
	for _, args := range [][]string{nil, {"--input", "missing"}, {"--input", cidrInput(t, "10.0.0.0/8\nbad\n")}, {"--input", "unused", "--max-findings", "0"}, {"--input", "unused", "--max-findings", "10001"}, {"--input", "unused", "extra"}} {
		var out bytes.Buffer
		if code := run(args, &out, &bytes.Buffer{}); code != 2 || out.Len() != 0 {
			t.Fatalf("code=%d output=%s", code, &out)
		}
	}
}

func TestHelpAndInputImmutability(t *testing.T) {
	if code := run([]string{"--help"}, &bytes.Buffer{}, &bytes.Buffer{}); code != 0 {
		t.Fatal(code)
	}
	path := cidrInput(t, "192.0.2.0/24\n")
	before, _ := os.ReadFile(path)
	run([]string{"--input", path}, &bytes.Buffer{}, &bytes.Buffer{})
	after, _ := os.ReadFile(path)
	if !bytes.Equal(before, after) {
		t.Fatal("input changed")
	}
}

func TestOversizeFileRejected(t *testing.T) {
	path := cidrInput(t, strings.Repeat(" ", (2<<20)+1))
	if code := run([]string{"--input", path}, &bytes.Buffer{}, &bytes.Buffer{}); code != 2 {
		t.Fatal(code)
	}
}

func BenchmarkBoundedCIDR(b *testing.B) {
	path := filepath.Join(b.TempDir(), "networks.txt")
	if err := os.WriteFile(path, []byte(strings.Repeat("10.0.0.0/8\n", 4096)), 0600); err != nil {
		b.Fatal(err)
	}
	b.ReportAllocs()
	b.ResetTimer()
	for index := 0; index < b.N; index++ {
		if code := run([]string{"--input", path}, io.Discard, io.Discard); code != 1 {
			b.Fatal(code)
		}
	}
}
