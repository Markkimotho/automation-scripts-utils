#!/usr/bin/env -S node --experimental-strip-types
import { readFileSync } from "node:fs";

const args: string[] = process.argv.slice(2);
if (args.includes("--help") || args.length !== 2) {
  console.log("Usage: node --experimental-strip-types script.ts FILE KEY");
  process.exit(args.includes("--help") ? 0 : 2);
}
try {
  const data: unknown = JSON.parse(readFileSync(args[0], "utf8"));
  if (typeof data !== "object" || data === null || Array.isArray(data) || !(args[1] in data)) {
    throw new Error("Key missing from JSON object");
  }
  console.log(JSON.stringify((data as Record<string, unknown>)[args[1]], null, 2));
} catch (error: unknown) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 2;
}
