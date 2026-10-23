#!/usr/bin/env node
'use strict';
// Offline metadata policy check. Never installs packages or executes lifecycle hooks.
const fs = require('node:fs');

function object(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function strongIntegrity(value) {
  if (typeof value !== 'string') return false;
  return value.split(/\s+/).some(token => {
    const match = /^(sha256|sha384|sha512)-([A-Za-z0-9+/]+={0,2})$/.exec(token);
    if (!match) return false;
    const decoded = Buffer.from(match[2], 'base64');
    return decoded.length === Number(match[1].slice(3)) / 8 && decoded.toString('base64') === match[2];
  });
}

function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: npm-lock-audit --lockfile package-lock.json\nChecks npm v2/v3 lock metadata; no network, downloads, or package execution.');
    return 0;
  }
  if (args.length !== 2 || args[0] !== '--lockfile') throw new Error('usage');
  const stat = fs.statSync(args[1]);
  if (!stat.isFile() || stat.size > 32 * 1024 * 1024) throw new Error('input limit');
  const lock = JSON.parse(fs.readFileSync(args[1], 'utf8'));
  if (!object(lock) || ![2, 3].includes(lock.lockfileVersion) || !object(lock.packages)) throw new Error('format');
  const entries = Object.entries(lock.packages).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
  if (entries.length > 100000) throw new Error('entry limit');
  const findings = [];
  let checked = 0, skipped = 0;
  for (const [path, entry] of entries) {
    if (!object(entry)) throw new Error('invalid package');
    if (path === '' || entry.link === true || entry.inBundle === true) { skipped++; continue; }
    checked++;
    const reasons = [];
    if (!strongIntegrity(entry.integrity)) reasons.push('missing-or-weak-integrity');
    let url;
    try { url = new URL(entry.resolved); } catch { /* reported without leaking the URL */ }
    if (!url || url.protocol !== 'https:') reasons.push('non-https-or-missing-source');
    if (url && (url.username || url.password)) reasons.push('embedded-credentials');
    if (entry.hasInstallScript === true) reasons.push('lifecycle-script');
    if (reasons.length) findings.push({path, reasons});
  }
  console.log(JSON.stringify({checked, skipped, findings}, null, 2));
  return findings.length ? 1 : 0;
}

try { process.exitCode = main(process.argv.slice(2)); }
catch { console.error('npm-lock-audit: expected readable npm v2/v3 lockfile <= 32 MiB and <= 100000 entries'); process.exitCode = 2; }
