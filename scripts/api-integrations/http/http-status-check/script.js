#!/usr/bin/env node
"use strict";
const { performance } = require("node:perf_hooks");
async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || !args.length) {
    console.log("Usage: node script.js URL [--timeout-ms INTEGER]");
    process.exit(args.includes("--help") ? 0 : 2);
  }
  let url;
  try {
    url = new URL(args[0]);
    if (!["http:", "https:"].includes(url.protocol)) throw Error("Only HTTP(S) URLs are supported");
  } catch (error) { console.error(error.message); process.exit(2); }
  const idx = args.indexOf("--timeout-ms");
  const timeout = idx < 0 ? 10000 : Number(args[idx + 1]);
  if (!Number.isInteger(timeout) || timeout < 100 || timeout > 60000) {
    console.error("timeout-ms must be between 100 and 60000"); process.exit(2);
  }
  const start = performance.now();
  try {
    const response = await fetch(url.href, { method: "HEAD", redirect: "manual", signal: AbortSignal.timeout(timeout) });
    console.log(JSON.stringify({ url: url.href, status: response.status, ok: response.ok, elapsed_ms: Math.round(performance.now() - start) }, null, 2));
    process.exitCode = response.ok ? 0 : 1;
  } catch (error) { console.error("Request failed:", error.message); process.exitCode = 2; }
}
main();
