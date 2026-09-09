# V1 Continuation State

## Active Task: v1.1.8 Dashboard Owner/Admin V2 — RELEASE COMPLETE

- Original implementation branch: `feat/dashboard-owner-admin-v2` (merged as PR `#39`; branch no longer exists after merge cleanup).
- Continuation/checkpoint branch: `ops/publish-v1.1.8`.
- Release/main commit: `87f4cb431f96632a0b8aa23932a625d342280fd0`.
- Stable release tag: `v1.1.8` -> `87f4cb431f96632a0b8aa23932a625d342280fd0`; never move/recreate it.
- Immutable prior release: `v1.1.7` -> `c0775a624b7081f794b492e4596bbc484aa6be02`; never move/recreate it.
- GitHub Release: `https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.8`.

## Completed Product Work

- Credential autofill is suppressed throughout authenticated UI and Chakra portals; Login retains `username` / `current-password` autofill.
- Owner/Admin Dashboard V2 uses `/api/dashboard/overview` with backend-enforced role/scope.
- Real traffic history comes from existing `NodeUserUsage`; no additional Xray reset-counter poller exists.
- Attention, top consumers, recent users, current activity, status distribution, Owner Node summary, and Owner Admin summary are real database aggregates.
- Admin sees no Owner-only Node/Admin summary and receives no billing-mode distribution from Dashboard overview.
- Admin credit UI remains generic and does not disclose accounting-model basis.
- Users remains the dedicated management surface.
- `host_update_impact` unrelated behavior was restored to the `main` baseline during self-review.
- UTC timestamp parsing, current-activity semantics, status legend, and legacy Admin counting were corrected during final self-review.
- Canonical Release workflow verifies both Stage 1 UI and authenticated-autofill contracts.
- All one-time preparation/publisher helpers are absent from `main`; the one-time publisher workflow was removed from `ops/publish-v1.1.8` after successful publication.

## Verification Completed

- Final PR head: `d901376ec73c65da9d1aeed73b382ebf440f5630`.
- PR CI Checkpoints run `34388100313`: SUCCESS across MySQL 8.0 and MySQL 26.7.0, backend regression, migrations/partial-DDL, Stage 8-11, backup/restore, v4.8.0 rollback, installer/runtime contracts, Dashboard parity, and Panel-to-Node mTLS.
- Final PR Dashboard UI Contracts run `34388100386`: SUCCESS.
- PR `#39` squash-merged to `main` as `87f4cb431f96632a0b8aa23932a625d342280fd0`.
- Post-merge CI Checkpoints run `34389875731`: SUCCESS.
- Post-merge Dashboard UI Contracts run `34389875690`: SUCCESS.
- One-time exact-tag publisher run `34390091051`: SUCCESS; created `v1.1.8` only after verifying exact protected-main source and then dispatched canonical Release.
- Canonical Release run `34390109398` (run 94): SUCCESS.
  - checked out `v1.1.8` and resolved HEAD to `87f4cb431f96632a0b8aa23932a625d342280fd0`;
  - verified main ancestry, version surfaces, release notes, Stage 1/authenticated-autofill contracts, dashboard build/parity;
  - published `ghcr.io/smorad3363/marzban-v1:sha-87f4cb431f96`, `:v1.1.8`, and `:latest` for `linux/amd64` and `linux/arm64`;
  - OCI index digest: `sha256:c2842211eaf58239b4e0cf0ef1384880e3c99cbf5ed78fc15e4a8f156f7332af`;
  - anonymous/runtime verification succeeded, including release SHA label, VERSION, MySQL/mysqldump 26.7.0, dashboard build, CLI, Node Runtime, and `latest` revision;
  - GitHub Release `v1.1.8` created successfully.

## Non-regression Invariants

- Preserve Node Operations V2, one authoritative reset-counter collector, safe Admin retirement, Plan permissions, Access Group semantics, Owner unrestricted behavior, and Panel-to-Node mTLS.
- Admin must not learn billing/accounting model basis; backend scope must continue enforcing Admin isolation.
- `v1.1.7` and `v1.1.8` are immutable published tags and must never be moved/recreated.

## Last Work File

`docs/CODEX/STATE.md`

## Last Work Section

Release-complete checkpoint for immutable `v1.1.8` publication and cleanup.

## NEXT EXACT TASK

No unfinished v1.1.8 task remains. On the next user request, first verify `main`, `v1.1.8`, `v1.1.7`, and the latest release state, then begin only the newly requested work. Do not modify or recreate either published tag.

## Recovery Rule

When work resumes, fetch this file first, review `Last Work File`, verify `main` and immutable release refs, then continue from `NEXT EXACT TASK`. If a future task changes product code, use a new isolated branch/PR and preserve all listed non-regression invariants.
