#!/usr/bin/env node
'use strict';
// Deliberately omit URLs, headers, cookies, bodies, and query parameters.
const fs = require('node:fs');

function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: har-timing-summary --input capture.har [--slow-ms 1000]\nOffline HAR 1.2 aggregate timing and status report. No URLs or payloads emitted.');
    return 0;
  }
  if (![2, 4].includes(args.length) || args[0] !== '--input' || (args.length === 4 && args[2] !== '--slow-ms')) throw new Error('usage');
  const threshold = args.length === 4 ? Number(args[3]) : 1000;
  if (!Number.isFinite(threshold) || threshold <= 0) throw new Error('threshold');
  const stat = fs.statSync(args[1]);
  if (!stat.isFile() || stat.size > 32 * 1024 * 1024) throw new Error('input limit');
  const har = JSON.parse(fs.readFileSync(args[1], 'utf8'));
  if (!har || !har.log || har.log.version !== '1.2' || !Array.isArray(har.log.entries)) throw new Error('format');
  const entries = har.log.entries;
  if (entries.length > 100000) throw new Error('entry limit');
  const report = {requests: entries.length, failed: 0, slow: 0, summed_request_ms: 0,
    max_request_ms: 0, known_body_bytes: 0, unknown_body_sizes: 0, status_counts: {}, timing_ms: {}};
  for (const entry of entries) {
    if (!entry || !Number.isFinite(entry.time) || entry.time < 0 || !entry.response ||
        !Number.isInteger(entry.response.status) || entry.response.status < 0 || entry.response.status > 599 ||
        !Number.isSafeInteger(entry.response.bodySize) || entry.response.bodySize < -1 ||
        !entry.timings || typeof entry.timings !== 'object' || Array.isArray(entry.timings)) throw new Error('entry');
    const {status, bodySize} = entry.response;
    if (status === 0 || status >= 400) report.failed++;
    if (entry.time >= threshold) report.slow++;
    report.summed_request_ms += entry.time;
    report.max_request_ms = Math.max(report.max_request_ms, entry.time);
    report.status_counts[status] = (report.status_counts[status] || 0) + 1;
    if (bodySize === -1) report.unknown_body_sizes++;
    else report.known_body_bytes += bodySize;
    for (const key of ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']) {
      const value = entry.timings[key];
      if (value === undefined || value === -1) continue;
      if (!Number.isFinite(value) || value < 0) throw new Error('timing');
      report.timing_ms[key] = (report.timing_ms[key] || 0) + value;
    }
  }
  if (!Number.isFinite(report.summed_request_ms) || !Number.isSafeInteger(report.known_body_bytes) ||
      Object.values(report.timing_ms).some(value => !Number.isFinite(value))) throw new Error('overflow');
  report.mean_request_ms = entries.length ? report.summed_request_ms / entries.length : 0;
  console.log(JSON.stringify(report, null, 2));
  return 0;
}

try { process.exitCode = main(process.argv.slice(2)); }
catch { console.error('har-timing-summary: expected HAR 1.2 with valid timings, status and body sizes; limit 32 MiB / 100000 entries'); process.exitCode = 2; }
