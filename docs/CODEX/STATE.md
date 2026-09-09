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
- Checkpoint `UMV3-01` — scoped summary aggregate + four compact Summary Cards: COMPLETE at source level.
  - Added `/api/users/summary` with real scoped counts for total, 24h-online, near-expiry, and high-usage users.
  - Reused hierarchy/inbound restrictions, the existing 24h Online definition, and centralized notification thresholds.
  - Added focused hierarchy-scoping coverage in `tests/test_user_summary.py`.
  - Added responsive `UserSummaryCards` and integrated it into the dedicated Users page without removing existing operations.
- Checkpoint `UMV3-02` — scoped management list + real advanced filters + bounded current-Plan metadata: SOURCE COMPLETE; MIRRORED CI VERIFICATION PARTIAL.
  - Added `/api/users/management` while preserving the full existing User row payload, pagination, sort semantics, hierarchy scope, inbound scope, usage redaction, and authorization behavior.
  - Added server-side Plan/current-assignment, without-Plan, Trial, Attention, expiry, usage, device-limit, unlimited-traffic, and inactivity filters using only real database state.
  - Current Plan metadata is resolved for the bounded visible page from the latest immutable `UserPlanAssignment`; no per-row Plan requests were introduced.
  - Refactored the toolbar to compact Admin/Plan/Sort controls and smart filter chips while preserving Create User/Create From Plan/account restrictions and debounced search.
  - Added focused `tests/test_user_management_query.py` coverage for hierarchy scope, latest Plan assignment, no-Plan/Trial and attention/smart filters.
  - PR #41 source verification at head `d50d2f9f2a8322d7086fea3b06f807d29b51ab1f`: Stage 1 UI contracts SUCCESS; authenticated-autofill contract SUCCESS; TypeScript type-check + production dashboard build SUCCESS; MySQL 26.7.0 backend regression/migrations/Stage 8-11/backup/rollback SUCCESS; installer/runtime/Panel-to-Node checks SUCCESS.
  - The mirrored MySQL 8.0 job was still running its backend regression suite at the last checkpoint poll. Re-check it on resume before claiming both database tracks green.
  - Dashboard parity currently fails only because generated `app/dashboard/build/**` has not yet been refreshed on the feature branch. Do not treat that expected generated-output delta as a source/build failure. Refresh committed build assets once source UI work settles, then require parity green before final review/merge.

### CURRENT FILES

Before continuing after interruption, re-open these files and review their current branch versions:

- `app/utils/user_management.py` — authoritative new scoped filter/query service; preserve its hierarchy/inbound scope behavior.
- `app/routers/user_management.py` — dedicated management list contract and pagination/filter validation.
- `app/dashboard/src/contexts/DashboardContext.tsx` — management endpoint/filter state and bounded `plan_meta` integration.
- `app/dashboard/src/components/FiltersCompact.tsx` — compact toolbar/smart filters; source compiles successfully.
- `tests/test_user_management_query.py` — focused current-filter coverage.
- `app/dashboard/src/components/UsersTablePro.tsx` — NEXT implementation target; current branch version was re-opened after UMV3-02 and still contains the wide legacy table plus all existing actions.
- `app/dashboard/src/components/UserDeviceLimit.tsx` — existing lazy Device modal; preserve lazy Device loading and sudo/Owner action semantics.
- `app/dashboard/src/types/Audit.ts` and `app/dashboard/src/types/DeviceLimit.ts` — existing typed lazy-data contracts for the upcoming Drawer.

### NEXT EXACT TASK

Implement checkpoint `UMV3-03`: compact the Users table to the requested management columns and add a real User Details Drawer without removing any existing action. Use bounded `plan_meta` for the current Plan column, use only real `online_at` for last activity, move secondary row details into the Drawer, keep Device and Audit data lazy, and preserve QR/copy/edit/delete/renew/enable-disable/reset/revoke/audit/device operations. Update traffic warning visual thresholds to 80% warning / 95% danger. Keep the current selection behavior and prepare the bulk controls for the later sticky-bottom pass. Before marking `UMV3-03` complete, re-check the pending MySQL 8.0 result from `UMV3-02`, then run frontend type/build and focused backend regression for any new backend work (if none, do not invent backend changes).

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
