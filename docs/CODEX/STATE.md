# V1 Continuation State

## Active Work: Users Management V3 — REVIEW FIX APPLIED / FINAL GATES PENDING

- Requested task: redesign the dedicated Users management surface to match the supplied premium dark/black-gold reference while preserving all existing business logic, permissions, pagination, billing/account restrictions, Plan/Access Group semantics, bulk operations, device limits, audit, renewal, subscription actions, and responsive behavior.
- Working branch: `feat/users-management-v3`.
- Pull request: `#41` (`feat: redesign users management surface`), Ready for Review; do not merge from a generic “continue” instruction.
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
- Checkpoint `UMV3-03` — compact Users table + real User Details Drawer: COMPLETE.
  - Replaced the legacy 1500px detail-heavy table with compact management columns: User, Status, current Plan, Usage, Expiry, Device, Last Activity, Owner-only Admin, and Operations.
  - Current Plan uses the bounded `plan_meta` map; no per-row Plan request was added.
  - Last Activity uses only the real `online_at` value and does not conflate it with User status.
  - Added `UserDetailsDrawer` with Overview, Subscription, optional Devices, and Activity/Audit tabs.
  - Device and Audit requests are lazy and fire only after the relevant Drawer tab is opened; existing Device modal semantics remain available to Owner.
  - Preserved QR/copy/edit/delete/renew/enable-disable/reset/revoke/audit/device operations and cross-page selection behavior.
  - Traffic warning visuals use 80% warning and 95% danger.
  - Updated the Stage 1 Users contract to require the compact table/Drawer architecture while preserving horizontal-scroll fallback and all actions.
- Checkpoint `UMV3-04` — sticky bulk UX + responsive Users management pass: COMPLETE.
  - Existing checked-user bulk behavior, target-scope preview, retry, cleanup, authorization, and cross-page selection semantics were preserved.
  - When a selection exists, the bulk controls become a compact sticky bottom action surface with safe-area spacing, desktop sidebar-aware centering, and horizontal action scrolling on narrow screens.
  - `UsersTablePro` reserves bottom content space while the sticky bar is active so pagination/table content is not covered.
  - The Admin/Plan/Sort row, smart-filter chips, creation/status controls, and search layout remain usable on mobile/tablet through bounded horizontal scrolling and responsive wrapping instead of squeezing controls.
  - Stage 1 UI contracts require the sticky selection surface, narrow-screen action scrolling, reserved table space, compact table/Drawer, lazy Device/Audit, and all existing row operations.
  - Self-review caught a parent `first-of-type` style rule that would have overridden the fixed bar border/background; the sticky Flex is isolated inside its own wrapper.
- Checkpoint `UMV3-05` — final PR review/fix pass: SOURCE REVIEW COMPLETE; FINAL GATES PENDING ON THIS CHECKPOINT HEAD.
  - PR #41 was moved from Draft to Ready for Review only after the original full gate set was green.
  - CodeRabbit completed a manual review and posted exactly one actionable finding: summary request failure was visually indistinguishable from a real count of zero.
  - The finding was verified against current source and fixed minimally in commit `7bc4cf5bfda2a4f7060f57633522f1ccac6f3e3b`: summary cards render `—` when `/api/users/summary` fails without cached data, while preserving skeleton loading and real numeric zeros on successful responses.
  - The production dashboard build was regenerated from that corrected source in commit `2b46acf3a76fb1e87398454f75db4cf517539b90`.
  - The one-time build-refresh workflow was removed again in commit `616c3fa742b09b9c53228a99948aa07bbf0fc2d3`; no temporary helper is intended to remain in the final branch.
  - The CodeRabbit thread was replied to with the fix/build commits and resolved.
  - Do not claim final merge readiness until the final-head `Dashboard UI Contracts` and `CI Checkpoints` runs are green after this checkpoint/state commit.

### CURRENT FILES

Before continuing after interruption, re-open these files and review their current branch versions:

- `app/dashboard/src/components/UserSummaryCards.tsx` — CodeRabbit review fix; failed summary requests must render an unknown state, never fake zero metrics.
- `app/dashboard/src/components/BulkUserActions.tsx` — completed sticky selection bar; verify no regression in bulk semantics and wrapper isolation.
- `app/dashboard/src/components/UsersTablePro.tsx` — compact table, reserved sticky-bar space, cross-page selection and Drawer integration.
- `app/dashboard/src/components/UserDetailsDrawer.tsx` — lazy Device/Audit details surface.
- `app/dashboard/src/components/FiltersCompact.tsx` — responsive toolbar and smart-filter controls.
- `app/dashboard/scripts/test-stage1-ui-contracts.cjs` — source contract for compact table/Drawer/sticky bulk UX.
- `app/dashboard/build/**` — regenerated after the CodeRabbit source fix; committed parity must be verified by final gates.
- `docs/CODEX/STATE.md` — this checkpoint; if interrupted, compare it against the actual branch head before doing anything else.

### NEXT EXACT TASK

Wait for and inspect the final-head `Dashboard UI Contracts` and `CI Checkpoints` triggered after this checkpoint. Require Stage 1/authenticated-autofill/typecheck/build/committed parity green, MySQL 8.0 and 26.7.0 backend/migration/Stage 8-11/backup/rollback green, installer/runtime/Panel-to-Node checks green, and no new unresolved review threads. If a real failure appears, reopen the exact failing file and fix only that failure, regenerate build assets if source UI changed, remove any helper, and re-run the relevant gates. If all gates are green, stop at PR-ready state and wait for a separate explicit merge instruction. Do not merge, tag, publish, or release from a generic “continue” instruction.

## Current State: v1.1.9 release candidate

- Release task: Users Management V3 + `v1.1.9` publication.
- Pull request `#41` was squash-merged into `main`.
- Reviewed Users Management PR head: `0a9d1780f68507cb3561211baebe46dd600298e5`.
- Users Management main commit: `ab98e693226eeaf3fea052e1d67f9c630f687393`.
- `v1.1.8` remains the latest published stable release until the new immutable tag and Release workflow complete.
- Release surfaces are prepared for `1.1.9` / `v1.1.9`; no tag, container alias, or GitHub Release is created by this preparation checkpoint.
- NEXT EXACT TASK: review and merge this release preparation, then create immutable tag `v1.1.9` from the reviewed `main` release commit and verify the canonical Release workflow.

## Previous Release: v1.1.8 released

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
