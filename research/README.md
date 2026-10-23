# Discovery and acceptance records

This is maintainer evidence, separate from the product manual. `candidates.json` records selected discoveries and decisions; search-result noise is not counted as a candidate. Null licenses, revisions and maintenance dates mean **unverified**, not permission to reuse. All six implementations in the October 2026 batch were independently written from API/format references; no upstream source, tests or prose were copied. The repository MIT license applies to the new implementations. Reference documentation retains its own license.

## Resume discovery

```bash
python tools/research.py pending
python tools/research.py validate
python tools/research.py ingest /path/to/new-discoveries.json
python tools/research.py retry gitlab --after 3600
```

Install `requirements-quality.txt` in a contributor environment first. Imports use the same schema as `candidates.json`, with `schema_version`, `candidates` and `source_state`. New imports must be `discovered`; existing identifiers and exact source URLs are deduplicated, existing reviews are preserved, and identifier collisions are rejected. Writes use atomic file replacement. Use one maintainer writer at a time; concurrent imports are not supported.

The retry command persists a source's attempt count and next retry time (e.g. a provider's Retry-After delay). `pending` shows those deadlines for the next researcher. No automatic crawler or API scheduler is provided: researchers must respect those deadlines and provider limits before making requests. Searches across GitHub, GitLab, Codeberg and official documentation were attempted in this batch; GitLab/Codeberg searches yielded no selected candidate. This is a scoped batch, not exhaustive coverage of all languages or categories.

## Evaluate and promote

1. Check the existing catalog and inventory for functional duplicates and source aliases; exact URL deduplication is only a first pass.
2. Move a candidate to `reviewed` after checking usefulness, input/output, permissions, dependencies, license and security. Reject unclear or unsuitable reuse. Independently implemented functionality may refer to documentation with an unknown license provided no protected expression is copied.
3. Record `adapted` only when a working local implementation is ready; `tested` only after meaningful checks pass. Code reuse (`copied` or `modified`) additionally requires a verified license, license URL, pinned source revision and preserved notices. Reuse compatibility remains a human review responsibility.
4. Save machine-readable evidence with exact commands, runtime versions, OS, results, limitations and SHA-256 hashes of implementations, metadata, README and functional tests. Run static, behavioral, packaging and documentation checks. The current batch uses only standard-library code and no third-party script dependencies; no dependency advisory database scan was performed.
5. Register an `accepted` script with its `provenance_ref`, required quality metadata and platforms no broader than the evidence. `tools/research.py validate` rejects missing reviews, unaccepted registrations, unsafe evidence paths, stale hashes, missing passing results and unverified platform claims.
6. Generate the public manual with `python tools/generate_directory.py`; CI checks for drift. Commit focused changes and open a PR with evidence. Only mark `published` after merge and successful release/deployment, recording the corresponding URLs. Local acceptance is not publication.

Legacy scripts are preserved under their existing metadata contract; the new evidence gate applies to entries with `provenance_ref`. This batch does not retroactively certify the original catalog. Review legacy compatibility and security claims incrementally.

The subsequent Go batch resumes `pem-expiry-report` and adds CIDR overlap reporting and checksum verification. Its local evidence is `evidence/2026-10-23-go-batch.json`, including native Go tests, vet and race checks. `tests/test_go_offline_automations.py` exercises the real CLI using a temporary test catalog to test every CI operating system before expanding product platform declarations. Standalone Go scripts are compiled into a temporary executable so findings and invalid-input exit codes remain distinct.

The web-discovery batch records eight public reference captures in `sources/2026-10-23-web-discovery.json` (URLs, retrieval times, byte counts and SHA-256 digests; no copied page bodies). Six independently written tools cover SQLite/Git backups, TOML drift, OpenAPI inventories, CSV formula risks and email attachment extraction. `evidence/2026-10-23-web-batch.json` contains acceptance evidence; `tools/verify_web_installation.py` exercises installed tools using disposable fixtures. PostgreSQL restore verification and iCalendar recurrence handling remain reviewed opportunities, not available scripts.

The PostgreSQL follow-up resumes the restore-verification candidate. Its independent implementation, PostgreSQL 15 reference captures, real database fixtures and package checks are recorded in `evidence/2026-10-23-postgres.json`. Source and verifier clusters in tests are owned temporary Unix-socket instances; no existing service or production credential is used. Verification restores use a non-superuser login. iCalendar recurrence handling and Windows event-log export remain unaccepted opportunities.

## Evidence maintenance

`evidence/2026-10-23-local-batch.json` identifies the tested sources by hash, includes environment and command results, and records known limits. Supporting text logs are under `evidence/logs/`. Updating any hashed file invalidates acceptance until relevant checks are rerun and the evidence regenerated. Hashes link evidence to local files; they are not an external signature or proof of independent review.
