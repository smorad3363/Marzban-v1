# V1 Continuation State

## Current State: v1.1.8 released

- Release task: Dashboard Owner/Admin V2 + `v1.1.8` publication.
- Pull request `#39` was squash-merged into `main`.
- Reviewed PR head: `d901376ec73c65da9d1aeed73b382ebf440f5630`.
- Release/main commit: `87f4cb431f96632a0b8aa23932a625d342280fd0`.
- Immutable release tag `v1.1.8` resolves to `87f4cb431f96632a0b8aa23932a625d342280fd0`.
- Immutable prior tag `v1.1.7` remains unchanged at `c0775a624b7081f794b492e4596bbc484aa6be02`.
- GitHub Release `Marzban v1.1.8` is published.
- The temporary feature branch `feat/dashboard-owner-admin-v2` is no longer present after merge.

## Completed Product Work

- Credential autofill is suppressed throughout authenticated UI and Chakra portals; Login retains `username` / `current-password` autofill.
- Owner/Admin Dashboard V2 uses `/api/dashboard/overview` with backend-enforced role/scope.
- Real traffic history comes from existing `NodeUserUsage`; no additional Xray reset-counter poller exists.
- Attention, top consumers, recent users, current activity, status distribution, Owner Node summary, and Owner Admin summary are real database aggregates.
- Admin sees no Owner-only Node/Admin summary and receives no billing-mode distribution from Dashboard overview.
- Admin credit UI remains generic and does not disclose accounting-model basis.
- Users remains the dedicated management surface.
- `host_update_impact` unrelated behavior was restored to the original `main` baseline during self-review.
- UTC timestamp parsing, current-activity semantics, status legend, legacy Admin counting, and `aria-live="polite"` regression were corrected before merge.
- Release surfaces are `1.1.8` / `v1.1.8`, including `VERSION`, `app/__init__.py`, `scripts/marzban.sh`, `docker-compose.yml`, `RELEASES.md`, and `docs/RELEASE_NOTES_v1.1.8.md`.
- Canonical Release workflow verifies Stage 1 UI and authenticated-autofill contracts and committed dashboard parity.
- All one-time release-preparation helpers were removed before merge.

## Final Verification

Final PR head `d901376ec73c65da9d1aeed73b382ebf440f5630`:

- `CI Checkpoints` run 225: SUCCESS.
- `Dashboard UI Contracts` run 140: SUCCESS.
- `Branch Hygiene` run 79: SUCCESS.
- Required MySQL 8.0 and MySQL 26.7.0 backend, migration/partial-DDL, Stage 8-11, backup/restore, rollback, installer/compose/runtime, dashboard parity, and Panel-to-Node mTLS gates were reported green on the final candidate.

Release commit/tag `87f4cb431f96632a0b8aa23932a625d342280fd0`:

- Release workflow run 94 (`34390109398`): SUCCESS.
- Immutable source/tag, main ancestry, version surfaces, and release notes verification: SUCCESS.
- Stage 1 dashboard contract and authenticated-autofill contract: SUCCESS.
- Production dashboard build and committed parity: SUCCESS.
- Multi-architecture image build/publish for `linux/amd64` and `linux/arm64`: SUCCESS.
- Anonymous/runtime published-image verification: SUCCESS, including source revision, dashboard runtime content, CLI/node runtime content, MySQL `26.7.0`, and `latest` revision matching the release source.
- GitHub Release creation: SUCCESS.

## Non-regression Invariants

- Preserve Node Operations V2 and the single authoritative reset-counter collector.
- Preserve safe Admin retirement/delete behavior.
- Preserve Plan permissions and Access Group semantics.
- Preserve Owner unrestricted behavior and Admin backend scope/billing confidentiality.
- Preserve installer and Panel-to-Node mTLS architecture.
- Never move or recreate published tags, especially `v1.1.7` and `v1.1.8`.

## Recovery Rule

`v1.1.8` is complete. Do not repeat the Dashboard V2 release work and do not move/recreate `v1.1.8`.

For the next task, start from the actual current `main`, read this state file, identify the new requested scope, and follow the repository engineering contract with the smallest correct change. If future work advances `main`, treat `87f4cb431f96632a0b8aa23932a625d342280fd0` as the immutable `v1.1.8` release source rather than assuming the latest `main` is the release commit.
