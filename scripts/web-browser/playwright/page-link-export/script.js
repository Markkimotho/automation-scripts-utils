#!/usr/bin/env node
"use strict";
async function main() {
  if (process.argv.includes("--help") || process.argv.length < 3) {
    console.log("Usage: node script.js https://example.com");
    process.exit(process.argv.includes("--help") ? 0 : 2);
  }
  let url;
  try {
    url = new URL(process.argv[2]);
    if (!["https:", "http:"].includes(url.protocol)) throw Error("HTTP(S) required");
  } catch (err) {
    console.error("Invalid URL:", err.message);
    process.exit(2);
  }
  let chromium;
  try { ({ chromium } = require("playwright")); }
  catch (_) { console.error("Install dependencies: npm install && npx playwright install chromium"); process.exit(2); }
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(url.href, { waitUntil: "domcontentloaded", timeout: 20000 });
    const links = await page.locator("a[href]").evaluateAll(elements => elements.map(el => ({
      text: (el.textContent || "").trim().slice(0, 200),
      href: el.href
    })));
    console.log(JSON.stringify({ url: url.href, count: links.length, links }, null, 2));
  } finally { await browser.close(); }
}
main().catch(err => { console.error(err.message); process.exitCode = 1; });
