# Automation catalog roadmap

## Phase 1 — foundation and migration

Audit all existing executables, migrate `bin/` into `scripts/<domain>/<topic>/<id>/`, move `lib/` to `packages/common/`, keep offline regression tests, create metadata, CLI, CI quality checks, and MkDocs documentation.

## Phase 2 — first 200 verified scripts

Prioritize Bash, PowerShell, Python, JavaScript/TypeScript for operating systems, files, Git, databases, APIs, and cloud tools. Each proposed addition must solve a concrete task and include a verification path.

## Phase 3 — 600 verified scripts

Add business productivity, browser automation, AI/ML operations, security and compliance, networking and integrations. Require real use-case demonstrations and mock external services in tests.

## Phase 4 — 1,200 verified scripts

Complete breadth across all 16 categories. Expand language and operating-system CI matrices, curated community contribution issues, documentation examples, and published browsable index.

Target counts by category are defined in `catalog/categories.yaml`; the number of **implemented** automations comes only from `catalog/scripts.json`. Never add placeholders or empty stubs to inflate totals.

## Scaling towards 5,000–10,000

Maintain unique, stable script IDs and validated metadata; build search indices from the catalog and separate fixtures from production credentials. Adopt versioned schema changes, automated compatibility tests, per-domain maintainership and deprecation processes.
