// Compare CIDR allocations offline; no packets are sent and no routes change.
package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/netip"
	"os"
	"strings"
	"unicode/utf8"
)

type networkRow struct {
	Line   int          `json:"line"`
	Prefix netip.Prefix `json:"prefix"`
}
type overlapRow struct {
	Left  int    `json:"left_line"`
	Right int    `json:"right_line"`
	Kind  string `json:"kind"`
}

func readNetworks(reader io.Reader) ([]networkRow, error) {
	rows := make([]networkRow, 0)
	scanner := bufio.NewScanner(reader)
	scanner.Buffer(make([]byte, 4096), 65536)
	line := 0
	for scanner.Scan() {
		line++
		text := strings.TrimSpace(scanner.Text())
		if text == "" || strings.HasPrefix(text, "#") {
			continue
		}
		if len(rows) == 4096 {
			return nil, errors.New("more than 4096 CIDR records")
		}
		prefix, err := netip.ParsePrefix(text)
		if err != nil {
			return nil, fmt.Errorf("invalid CIDR on line %d", line)
		}
		rows = append(rows, networkRow{line, prefix.Masked()})
	}
	if err := scanner.Err(); err != nil {
		return nil, errors.New("cannot read CIDR lines (line limit 64 KiB)")
	}
	return rows, nil
}

func run(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("cidr-overlap-report", flag.ContinueOnError)
	flags.SetOutput(stderr)
	input := flags.String("input", "", "UTF-8 text file with one CIDR per line; # comments allowed")
	maxFindings := flags.Int("max-findings", 1000, "maximum reported pairs (1..10000); all pairs are counted")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0
		}
		return 2
	}
	fail := func(message string) int { fmt.Fprintln(stderr, "cidr-overlap-report: "+message); return 2 }
	if *input == "" || flags.NArg() != 0 || *maxFindings < 1 || *maxFindings > 10000 {
		return fail("require --input, no positional arguments, and max-findings between 1 and 10000")
	}
	info, err := os.Stat(*input)
	if err != nil || !info.Mode().IsRegular() || info.Size() > 2<<20 {
		return fail("require a readable regular file no larger than 2 MiB")
	}
	file, err := os.Open(*input)
	if err != nil {
		return fail("cannot read input")
	}
	defer file.Close()
	// Read one extra byte so a file that grows during inspection cannot evade the cap.
	data, err := io.ReadAll(io.LimitReader(file, (2<<20)+1))
	if err != nil || len(data) > 2<<20 {
		return fail("cannot read input within the 2 MiB limit")
	}
	if !utf8.Valid(data) {
		return fail("input must be UTF-8")
	}
	rows, err := readNetworks(strings.NewReader(string(data)))
	if err != nil {
		return fail(err.Error())
	}
	findings := make([]overlapRow, 0)
	count := 0
	for left, first := range rows {
		for _, second := range rows[left+1:] {
			if !first.Prefix.Overlaps(second.Prefix) {
				continue
			}
			count++
			if len(findings) < *maxFindings {
				kind := "containment"
				if first.Prefix == second.Prefix {
					kind = "duplicate"
				}
				findings = append(findings, overlapRow{first.Line, second.Line, kind})
			}
		}
	}
	report := struct {
		Networks     []networkRow `json:"networks"`
		OverlapCount int          `json:"overlap_count"`
		Overlaps     []overlapRow `json:"overlaps"`
		Truncated    bool         `json:"truncated"`
	}{rows, count, findings, count > len(findings)}
	if err := json.NewEncoder(stdout).Encode(report); err != nil {
		return fail("cannot write report")
	}
	if count > 0 {
		return 1
	}
	return 0
}

func main() { os.Exit(run(os.Args[1:], os.Stdout, os.Stderr)) }
