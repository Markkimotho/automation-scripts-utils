#!/usr/bin/env node
'use strict';
// An offline operation inventory, not a full OpenAPI validator or live auth probe.
const fs = require('node:fs');
const {TextDecoder} = require('node:util');
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const methods = ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'];
function security(value) {
  if (!Array.isArray(value) || value.some(item => !object(item) || Object.values(item).some(scopes => !Array.isArray(scopes) || scopes.some(scope => typeof scope !== 'string')))) throw new Error('invalid security requirement');
  return value.length === 0 || value.some(item => Object.keys(item).length === 0);
}
function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: openapi-operation-inventory --input openapi.json\nOpenAPI 3.0/3.1 JSON only; no reference fetching or requests.'); return 0;
  }
  if (args.length !== 2 || args[0] !== '--input') throw new Error('usage');
  const info = fs.statSync(args[1]);
  if (!info.isFile() || info.size > 8 * 1024 * 1024) throw new Error('input limit');
  const descriptor = fs.openSync(args[1], 'r');
  const buffer = Buffer.alloc(8 * 1024 * 1024 + 1);
  let used = 0;
  try {
    if (!fs.fstatSync(descriptor).isFile()) throw new Error('not a regular file');
    while (used < buffer.length) {
      const count = fs.readSync(descriptor, buffer, used, buffer.length - used, null);
      if (!count) break;
      used += count;
    }
  } finally {fs.closeSync(descriptor);}
  if (used > 8 * 1024 * 1024) throw new Error('input grew');
  const data = buffer.subarray(0, used);
  const document = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(data));
  if (!object(document) || typeof document.openapi !== 'string' || !/^3\.[01]\.\d+$/.test(document.openapi) || !object(document.paths)) throw new Error('unsupported OpenAPI format');
  const inherited = Object.hasOwn(document, 'security') ? security(document.security) : true;
  const operations = [], findings = [], ids = new Set(), unresolved = [];
  for (const path of Object.keys(document.paths).sort()) {
    if (path.startsWith('x-')) continue;
    const item = document.paths[path];
    if (!path.startsWith('/') || !object(item)) throw new Error('invalid path item');
    if (Object.hasOwn(item, '$ref')) {
      if (typeof item.$ref !== 'string') throw new Error('invalid path reference');
      unresolved.push(path);
    }
    for (const method of methods) {
      if (!Object.hasOwn(item, method)) continue;
      const operation = item[method];
      if (!object(operation) || (Object.hasOwn(operation, 'deprecated') && typeof operation.deprecated !== 'boolean')) throw new Error('invalid operation');
      if (operations.length === 10000) throw new Error('operation limit');
      const id = operation.operationId;
      if (id !== undefined && (typeof id !== 'string' || !id.trim())) throw new Error('invalid operation id');
      if (!id) findings.push({path, method, reason:'missing-operation-id'});
      else if (ids.has(id)) findings.push({path, method, reason:'duplicate-operation-id'});
      if (id) ids.add(id);
      const anonymous = Object.hasOwn(operation, 'security') ? security(operation.security) : inherited;
      operations.push({path, method, operation_id:id ?? null, deprecated:operation.deprecated === true, anonymous_allowed_by_spec:anonymous});
    }
  }
  console.log(JSON.stringify({operations, findings, unresolved_path_refs:unresolved}, null, 2));
  return findings.length || unresolved.length ? 1 : 0;
}
try {process.exitCode = main(process.argv.slice(2));}
catch {console.error('openapi-operation-inventory: expected readable OpenAPI 3.0/3.1 JSON, <=8 MiB and <=10000 operations; no partial report emitted');process.exitCode=2;}
