#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const file = process.argv[2];
if (file === "--help" || !file) {
  console.log("Usage: node script.js FILE");
  process.exit(file === "--help" ? 0 : 2);
}
const stat = fs.statSync(file);
if (!stat.isFile()) throw Error("Expected a regular file");
console.log(JSON.stringify({ file, bytes: stat.size }));
