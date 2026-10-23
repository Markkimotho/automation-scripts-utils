import { statSync } from "node:fs";
const file: string | undefined = process.argv[2];
if (file === "--help" || !file) {
  console.log("Usage: node --experimental-strip-types script.ts FILE");
  process.exit(file === "--help" ? 0 : 2);
}
console.log(JSON.stringify({ file, bytes: statSync(file).size }));
