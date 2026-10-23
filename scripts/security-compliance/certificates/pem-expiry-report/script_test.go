package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"math/big"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

var observed = time.Date(2030, 1, 1, 0, 0, 0, 0, time.UTC)

func fixtureCertificate(t *testing.T, before, after time.Time) []byte {
	t.Helper()
	// Deterministic test-only private key; never used outside generated fixtures.
	key := ed25519.NewKeyFromSeed(make([]byte, ed25519.SeedSize))
	template := &x509.Certificate{SerialNumber: big.NewInt(1), NotBefore: before, NotAfter: after}
	der, err := x509.CreateCertificate(rand.Reader, template, template, key.Public(), key)
	if err != nil {
		t.Fatal(err)
	}
	return pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
}

func TestCertificateStatusesAndBoundaries(t *testing.T) {
	for _, test := range []struct {
		name          string
		before, after time.Time
		status        string
	}{
		{"valid", observed.Add(-time.Hour), observed.Add(31 * 24 * time.Hour), "valid"},
		{"warning-boundary", observed, observed.Add(30 * 24 * time.Hour), "expiring"},
		{"expiry-boundary", observed.Add(-time.Hour), observed, "expired"},
		{"expired", observed.Add(-2 * time.Hour), observed.Add(-time.Hour), "expired"},
		{"future", observed.Add(time.Hour), observed.Add(60 * 24 * time.Hour), "not-yet-valid"},
	} {
		t.Run(test.name, func(t *testing.T) {
			data := fixtureCertificate(t, test.before, test.after)
			rows, err := inspectPEM(data, observed, 30)
			if err != nil || len(rows) != 1 || rows[0].Status != test.status {
				t.Fatalf("rows=%+v err=%v", rows, err)
			}
			block, _ := pem.Decode(data)
			sum := sha256.Sum256(block.Bytes)
			if rows[0].SHA256 != hex.EncodeToString(sum[:]) {
				t.Fatal("incorrect certificate fingerprint")
			}
		})
	}
}

func TestBundleAndWhitespace(t *testing.T) {
	data := fixtureCertificate(t, observed, observed.Add(60*24*time.Hour))
	rows, err := inspectPEM(append(append([]byte(" \n"), data...), data...), observed, 0)
	if err != nil || len(rows) != 2 || rows[1].Index != 2 {
		t.Fatalf("rows=%+v err=%v", rows, err)
	}
}

func TestStrictPEMRejectsIgnoredContent(t *testing.T) {
	valid := fixtureCertificate(t, observed, observed.Add(time.Hour))
	for _, data := range [][]byte{
		nil, []byte("garbage"), append([]byte("garbage\n"), valid...), append(valid, []byte("trailing")...),
		[]byte("-----BEGIN PRIVATE KEY-----\nU0VDUkVU\n-----END PRIVATE KEY-----"),
		[]byte("-----BEGIN CERTIFICATE-----\nbad\n-----END CERTIFICATE-----"),
		pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: []byte("not DER")}),
		append([]byte("-----BEGIN CERTIFICATE-----\nbad\n"), valid...),
		bytes.Repeat(valid, 513),
	} {
		if _, err := inspectPEM(data, observed, 30); err == nil {
			t.Fatalf("accepted malformed PEM (%d bytes)", len(data))
		}
	}
}

func TestCommandReadOnlyAndFixedObservation(t *testing.T) {
	data := fixtureCertificate(t, observed, observed.Add(100*24*time.Hour))
	path := filepath.Join(t.TempDir(), "cert ü.pem")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	var stdout, stderr bytes.Buffer
	code := run([]string{"--input", path, "--as-of", "2030-01-01T03:00:00+03:00"}, &stdout, &stderr, time.Now)
	if code != 0 || !strings.Contains(stdout.String(), `"as_of":"2030-01-01T00:00:00Z"`) {
		t.Fatalf("code=%d output=%s error=%s", code, &stdout, &stderr)
	}
	var report map[string]interface{}
	if err := json.Unmarshal(stdout.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if !bytes.Equal(data, after) {
		t.Fatal("input changed")
	}
}

func TestFindingExitCode(t *testing.T) {
	path := filepath.Join(t.TempDir(), "expired.pem")
	os.WriteFile(path, fixtureCertificate(t, observed.Add(-2*time.Hour), observed), 0600)
	var stdout, stderr bytes.Buffer
	if code := run([]string{"--input", path}, &stdout, &stderr, func() time.Time { return observed }); code != 1 {
		t.Fatalf("code=%d %s", code, &stderr)
	}
}

func TestInvalidArgumentsAndPrivacy(t *testing.T) {
	path := filepath.Join(t.TempDir(), "private.pem")
	os.WriteFile(path, []byte("SECRET-PRIVATE-CONTENT"), 0600)
	for _, args := range [][]string{nil, {"--input", "missing"}, {"--input", path}, {"--input", path, "--warn-days", "-1"},
		{"--input", path, "--warn-days", "36501"}, {"--input", path, "--as-of", "bad"}, {"--input", path, "extra"}} {
		var stdout, stderr bytes.Buffer
		if code := run(args, &stdout, &stderr, time.Now); code != 2 || stdout.Len() != 0 || strings.Contains(stderr.String(), "SECRET") {
			t.Fatalf("args=%v output=%s err=%s", args, &stdout, &stderr)
		}
	}
}

func TestHelpDoesNotReadInput(t *testing.T) {
	if code := run([]string{"--help"}, &bytes.Buffer{}, &bytes.Buffer{}, time.Now); code != 0 {
		t.Fatal(code)
	}
}

func TestOversizedInput(t *testing.T) {
	path := filepath.Join(t.TempDir(), "large.pem")
	file, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := file.Truncate((8 << 20) + 1); err != nil {
		t.Fatal(err)
	}
	file.Close()
	var out bytes.Buffer
	if code := run([]string{"--input", path}, &out, &bytes.Buffer{}, time.Now); code != 2 || out.Len() != 0 {
		t.Fatal(code)
	}
}
