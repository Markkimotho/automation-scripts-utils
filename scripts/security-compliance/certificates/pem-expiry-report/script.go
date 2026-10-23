// Inspect certificate dates locally; this does not establish certificate trust.
package main

import (
	"bytes"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"time"
)

type certificateRow struct {
	Index            int    `json:"index"`
	SHA256           string `json:"sha256"`
	NotBefore        string `json:"not_before"`
	NotAfter         string `json:"not_after"`
	RemainingSeconds int64  `json:"remaining_seconds"`
	Status           string `json:"status"`
}

func inspectPEM(data []byte, now time.Time, warnDays int) ([]certificateRow, error) {
	rows := make([]certificateRow, 0)
	for data = bytes.TrimSpace(data); len(data) > 0; data = bytes.TrimSpace(data) {
		if len(rows) == 512 || !bytes.HasPrefix(data, []byte("-----BEGIN CERTIFICATE-----")) {
			return nil, errors.New("expected at most 512 certificate-only PEM blocks")
		}
		endMarker := []byte("-----END CERTIFICATE-----")
		end := bytes.Index(data, endMarker)
		if end < 0 {
			return nil, errors.New("unterminated certificate PEM")
		}
		end += len(endMarker)
		if bytes.Count(data[:end], []byte("-----BEGIN ")) != 1 {
			return nil, errors.New("nested or malformed certificate PEM")
		}
		block, rest := pem.Decode(data[:end])
		if block == nil || block.Type != "CERTIFICATE" || len(block.Headers) != 0 || len(rest) != 0 {
			return nil, errors.New("malformed certificate PEM")
		}
		cert, err := x509.ParseCertificate(block.Bytes)
		if err != nil {
			return nil, errors.New("invalid X.509 certificate")
		}
		status := "valid"
		switch {
		case now.Before(cert.NotBefore):
			status = "not-yet-valid"
		case !now.Before(cert.NotAfter):
			status = "expired"
		case !cert.NotAfter.After(now.Add(time.Duration(warnDays) * 24 * time.Hour)):
			status = "expiring"
		}
		digest := sha256.Sum256(cert.Raw)
		rows = append(rows, certificateRow{len(rows) + 1, hex.EncodeToString(digest[:]),
			cert.NotBefore.UTC().Format(time.RFC3339), cert.NotAfter.UTC().Format(time.RFC3339),
			cert.NotAfter.Unix() - now.Unix(), status})
		data = data[end:]
	}
	if len(rows) == 0 {
		return nil, errors.New("no certificates")
	}
	return rows, nil
}

func run(args []string, stdout, stderr io.Writer, clock func() time.Time) int {
	flags := flag.NewFlagSet("pem-expiry-report", flag.ContinueOnError)
	flags.SetOutput(stderr)
	input := flags.String("input", "", "local certificate-only PEM bundle (maximum 8 MiB)")
	asOf := flags.String("as-of", "", "RFC3339 observation time; default is current UTC time")
	warnDays := flags.Int("warn-days", 30, "expiry warning window in days (0..36500)")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0
		}
		return 2
	}
	fail := func(message string) int { fmt.Fprintln(stderr, "pem-expiry-report: "+message); return 2 }
	if *input == "" || flags.NArg() != 0 || *warnDays < 0 || *warnDays > 36500 {
		return fail("require --input, no positional arguments, and warn-days between 0 and 36500")
	}
	now := clock().UTC()
	if *asOf != "" {
		var err error
		now, err = time.Parse(time.RFC3339, *asOf)
		if err != nil {
			return fail("as-of must be RFC3339")
		}
		now = now.UTC()
	}
	info, err := os.Stat(*input)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 8<<20 {
		return fail("require a readable regular PEM file no larger than 8 MiB")
	}
	file, err := os.Open(*input)
	if err != nil {
		return fail("cannot read input")
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, (8<<20)+1))
	if err != nil || len(data) > 8<<20 {
		return fail("cannot read input within the 8 MiB limit")
	}
	rows, err := inspectPEM(data, now, *warnDays)
	if err != nil {
		return fail(err.Error())
	}
	findings := 0
	for _, row := range rows {
		if row.Status != "valid" {
			findings++
		}
	}
	report := struct {
		AsOf         string           `json:"as_of"`
		Certificates []certificateRow `json:"certificates"`
		Findings     int              `json:"findings"`
	}{now.Format(time.RFC3339), rows, findings}
	if err := json.NewEncoder(stdout).Encode(report); err != nil {
		return fail("cannot write report")
	}
	if findings > 0 {
		return 1
	}
	return 0
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr, time.Now)) }
