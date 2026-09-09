# V1 Continuation State

## Active Work: Users Management V3 — IN PROGRESS

- Requested task: redesign the dedicated Users management surface to match the supplied premium dark/black-gold reference while preserving all existing business logic, permissions, pagination, billing/account restrictions, Plan/Access Group semantics, bulk operations, device limits, audit, renewal, subscription actions, and responsive behavior.
- Working branch: `feat/users-management-v3`.
- Draft PR: `#41` (`feat: redesign users management surface`).
- Branch base: current `main` at `aeb1f0c90f79dca627bfd78c77082dc9486d8df0` (`docs: checkpoint completed v1.1.8 release (#40)`).
- Immutable released source remains `v1.1.8` at `87f4cb431f96632a0b8aa23932a625d342280fd0`; never move or recreate that tag.
- Initial audit completed against the real current User routes/models, hierarchy scoping, device-limit routes, bulk-job API, audit API, Plan services, Users page, filters, table, dialogs, and dashboard state.
- Confirmed existing backend Online definition used by `/api/system`: `crud.count_online_users(..., 24, ...)`; User status and online activity must remain distinct concepts.
- Confirmed notification configuration already provides centralized attention thresholds via `NOTIFY_DAYS_LEFT` and `NOTIFY_REACHED_USAGE_PERCENT`.
- Confirmed list search is server-side over username/note and hierarchy/inbound scope is enforced in the database query.
- Confirmed expensive Device/Audit details can remain lazy and must not become per-row N+1 requests.

### Recovery / Resume Rule for this task

On any interruption:

1. Read `AGENTS.md`, this file, and `docs/CODEX/V1_SCOPE.md`.
2. Inspect the actual branch head and compare `feat/users-management-v3` against current `main`; never assume the previous chat completed the last edit.
3. Re-open and review the exact file named in `CURRENT FILES` below before changing it again, plus the directly-related route/type/component it depends on.
4. Re-check the last completed checkpoint and its diff/tests before continuing.
5. Continue only from `NEXT EXACT TASK`; do not repeat completed release work and do not discard valid branch changes.

### Current Checkpoint

- Checkpoint `UMV3-00` — branch/bootstrap and architecture audit: COMPLETE.
- Checkpoint `UMV3-01` — scoped summary aggregate + four compact Summary Cards: COMPLETE.
  - Added `/api/users/summary` with real scoped counts for total, 24h-online, near-expiry, and high-usage users.
  - Reused hierarchy/inbound restrictions, the existing 24h Online definition, and centralized notification thresholds.
  - Added focused hierarchy-scoping coverage in `tests/test_user_summary.py`.
  - Added responsive `UserSummaryCards` and integrated it into the dedicated Users page without removing existing operations.
- Checkpoint `UMV3-02` — scoped management list + real advanced filters + bounded current-Plan metadata: COMPLETE.
  - Added `/api/users/management` while preserving the full existing User row payload, pagination, sort semantics, hierarchy scope, inbound scope, usage redaction, and authorization behavior.
  - Added server-side Plan/current-assignment, without-Plan, Trial, Attention, expiry, usage, device-limit, unlimited-traffic, and inactivity filters using only real database state.
  - Current Plan metadata is resolved for the bounded visible page from the latest immutable `UserPlanAssignment`; no per-row Plan requests were introduced.
  - Refactored the toolbar to compact Admin/Plan/Sort controls and smart filter chips while preserving Create User/Create From Plan/account restrictions and debounced search.
  - Added focused `tests/test_user_management_query.py` coverage for hierarchy scope, latest Plan assignment, no-Plan/Trial and attention/smart filters.
- Checkpoint `UMV3-03` — compact Users table + real User Details Drawer: COMPLETE at source/build level.
  - Replaced the legacy 1500px detail-heavy table with compact management columns: User, Status, current Plan, Usage, Expiry, Device, Last Activity, Owner-only Admin, and Operations.
  - Current Plan uses the bounded `plan_meta` map; no per-row Plan request was added.
  - Last Activity uses only the real `online_at` value and does not conflate it with User status.
  - Added `UserDetailsDrawer` with Overview, Subscription, optional Devices, and Activity/Audit tabs.
  - Device and Audit requests are lazy and fire only after the relevant Drawer tab is opened; existing Device modal semantics remain available to Owner.
  - Preserved QR/copy/edit/delete/renew/enable-disable/reset/revoke/audit/device operations and cross-page selection behavior.
  - Traffic warning visuals now use 80% warning and 95% danger.
  - Updated the Stage 1 Users contract to require the compact table/Drawer architecture while preserving horizontal-scroll fallback and all actions.
  - Verification on head `8947a39b2830889707e0b14b17d9668351fcadf5`: Stage 1 UI contracts SUCCESS; authenticated-autofill contract SUCCESS; TypeScript + production dashboard build SUCCESS; MySQL 8.0 backend/migration/Stage 8-11/backup/rollback SUCCESS; MySQL 26.7.0 backend/migration/Stage 8-11/backup/rollback SUCCESS; installer/runtime/Panel-to-Node checks SUCCESS.
  - Dashboard jobs fail only at committed build parity because `app/dashboard/build/**` has intentionally not yet been refreshed. Source/build checks are green. Refresh generated build assets after the final responsive/bulk pass, then require parity green before review/merge.

### CURRENT FILES

Before continuing after interruption, re-open these files and review their current branch versions:

- `app/dashboard/src/components/BulkUserActions.tsx` — NEXT implementation target; preserve all bulk job, selected-user, cleanup, preview, retry, and scope semantics while moving selected-state UX to a sticky bottom action bar.
- `app/dashboard/src/components/UsersTablePro.tsx` — compact table + Drawer integration; preserve cross-page selection and all row actions.
- `app/dashboard/src/components/UserDetailsDrawer.tsx` — completed lazy Drawer; preserve lazy Device/Audit loading.
- `app/dashboard/src/components/FiltersCompact.tsx` — compact toolbar/smart filters; include in responsive/mobile polish only, without changing server filter semantics.
- `app/dashboard/src/pages/Users.tsx` — dedicated Users surface composition.
- `app/dashboard/scripts/test-stage1-ui-contracts.cjs` — current Users management source contract.
- `app/dashboard/build/**` — generated assets are intentionally stale until source UI settles; refresh only after `UMV3-04` source is verified.

### NEXT EXACT TASK

Implement checkpoint `UMV3-04`: finish the bulk UX and responsive pass. When one or more visible/cross-page users are selected, present the existing bulk actions as a compact sticky-bottom action bar without changing bulk target semantics, preview, retry, cleanup, or authorization behavior. Preserve Select All and cross-page selection visibility, ensure the bar does not cover pagination/content, and keep controls usable on narrow mobile/tablet widths. Polish the Users toolbar/table/Drawer responsive behavior against the requested premium management reference without removing columns or operations. Update the Stage 1 contract for the sticky bulk UX, run frontend type/build, then refresh committed `app/dashboard/build/**` exactly once and require dashboard parity green. No backend change is expected; if no backend code changes, do not invent backend work.

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
