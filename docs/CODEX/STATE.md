# V1 Continuation State

## Active Task: Dashboard Owner/Admin V2 + credential-autofill hardening

- Working branch: `feat/dashboard-owner-admin-v2`
- Base/main SHA at task start: `e8f9ce09c7939c15a2fbdeae858ba990d79db846`
- Published stable release invariant: `v1.1.7` MUST remain at `c0775a624b7081f794b492e4596bbc484aa6be02`; never move/recreate it.
- Latest published stable release at task start: `v1.1.7`.
- **Target next release version for this work: `v1.1.8`.** The development branch name is not the release version.
- Do not create/tag/publish `v1.1.8` until the full feature, CI, review, merge, release metadata/build parity, and publication gates are complete.

## User Request / Priority Order

1. Fix credential autofill leaking the saved login username (example: `saji`) into non-login inputs. Credential autofill is wanted only on the Login page.
2. Then implement the supplied Owner/Admin Dashboard redesign using real backend data, real role/scope/permissions, existing Chakra/design system, responsive RTL, no fake/mock/hardcoded metrics, and no duplicate Users-management UI.
3. Prepare the completed work as the next stable version `v1.1.8` after all verification gates pass.
4. Long-task recovery is mandatory: when the user says `ادامه بده`, re-read this file, re-read the `Last Work File`, verify branch HEAD/CI, and continue from `NEXT EXACT TASK`.

## Source Requirements

- User-supplied design spec: Dashboard Owner/Admin redesign prompt attached in the conversation (1016 lines).
- User-supplied visual references: separate Owner and Admin dark/black-gold dashboard screenshots.
- Repository rules: `AGENTS.md`, `docs/CODEX/V1_SCOPE.md`.

## Non-regression Invariants

- Preserve mature implementation and make targeted delta-only changes.
- Keep Users page as the full user-management surface; Dashboard remains overview/alerts/trends/quick actions only.
- Owner/sudo: system/global authorized scope. Admin: own/authorized scope only.
- Backend must enforce scope; frontend-only hiding is insufficient.
- Reuse actual `useGetUser`, AccountSummary, AdminCapabilities, ManagedAdminList, `/account/summary`, `/admin/capabilities`, Users APIs, Node APIs, React Query, AppShell, CSS variables, OWNER/is_sudo, account status, billing mode, user creation mode, and current permission system when applicable.
- Do not expose accounting-model basis to Admin; preserve existing Admin self-accounting privacy.
- Preserve Plan/Access Group semantics and Node Operations V2 behavior.
- No unnecessary dependencies, broad refactors, lockfile/config changes, or unrelated release changes.
- Dashboard committed build parity remains a required gate.
- `v1.1.7` is immutable; `v1.1.8` will be created only from the final reviewed/verified release source.

## Current Status

TASK STARTED. BRANCH CREATED FROM CURRENT MAIN. NO PRODUCT EDITS YET. TARGET RELEASE RECORDED AS `v1.1.8`.

### Confirmed Autofill Root Cause

- `NodesManagementWorkspace.tsx` initializes the Node search state with an empty string and does not load the Admin username.
- The Node search input is a plain Chakra `Input` with no explicit search/autocomplete identity.
- Login intentionally declares `autoComplete="username"` and `autoComplete="current-password"`.
- Therefore the reappearing saved username is browser/password-manager credential autofill, not backend data or a placeholder.
- Goal: prevent credential autofill throughout authenticated/non-login UI while preserving Login autofill.

## Planned Milestones

1. **Autofill hardening**
   - Audit shared/custom input components and direct Chakra inputs.
   - Add a safe non-login default/guard and explicit semantic search identity where needed.
   - Preserve Login username/password autocomplete.
   - Add focused UI-contract coverage and dashboard build/parity verification.

2. **Dashboard architecture audit**
   - Audit current Dashboard, DashboardContext, user/admin/account/node APIs/models/status definitions, permissions/capabilities, online tracking, usage history sources, and existing charts/dependencies.
   - Decide whether current APIs are sufficient or role-aware aggregate dashboard endpoints are required to avoid N+1 requests.
   - Define real Attention logic only from actual model/status/config fields.

3. **Backend dashboard data (only if required)**
   - Add minimal role-aware aggregate endpoint(s), with backend-enforced Owner/Admin scope.
   - Support summary, online count, status distribution, attention, traffic history/downsampling, top consumers, recent users, compact Node/Admin summaries as applicable.
   - Add authorization/scope/aggregation tests.

4. **Owner/Admin Dashboard UI**
   - Owner: management header, 5 top metrics, real traffic chart, user status ring, attention list, top consumers, compact Node summary, compact Admin summary.
   - Admin: users header, permission/capability-aware quick actions, 5 top metrics including own credit, scoped traffic/status, credit/capacity, attention, top consumers, recent users.
   - Responsive RTL; current dark/light theme tokens; black/navy charcoal with restrained gold accent; no fake data.
   - Loading/empty/error/refresh isolation per async section.

5. **Final verification and v1.1.8 release preparation**
   - Focused backend tests, authorization/scope tests, dashboard UI contracts, TypeScript production build, committed dashboard parity, full CI gates on the final PR head.
   - Self-review full diff for permission leaks, N+1 queries, duplicate Users UI, unintended Plan/Access Group/accounting changes.
   - After merge, prepare version/release metadata for `v1.1.8`, re-run required release gates, then create immutable `v1.1.8` tag and canonical GitHub/GHCR release only from the verified source.

## Last Work File

`docs/CODEX/STATE.md`

## Last Work Section

Release-target correction: next stable version is `v1.1.8`; working branch remains a descriptive implementation branch only.

## NEXT EXACT TASK

1. Fetch and review `app/dashboard/src/components/Input.tsx` and all explicit `autoComplete=` usage in dashboard source.
2. Audit direct Chakra `Input` usage in authenticated screens, starting with `app/dashboard/src/components/NodesManagementWorkspace.tsx` where the saved Admin username is currently injected by browser/password-manager autofill.
3. Implement the smallest robust fix so credential autofill remains enabled only in `pages/Login.tsx` and is suppressed for non-login inputs without breaking normal form values.
4. Add/adjust focused dashboard UI-contract tests for the autofill invariant.
5. Build/regenerate dashboard committed artifacts and verify parity/CI for this checkpoint.
6. Update this file with the exact last edited file, commit/run IDs, verification result, and the first Dashboard architecture-audit task.

## Recovery Rule

When the user says `ادامه بده` or work resumes after interruption:

1. Fetch `docs/CODEX/STATE.md` from `feat/dashboard-owner-admin-v2` (or from the current PR head if the branch name later changes).
2. Fetch and review `Last Work File` and specifically the `Last Work Section` before editing anything else.
3. Verify branch HEAD and any CI/run recorded by the checkpoint.
4. Execute `NEXT EXACT TASK` starting at the first incomplete item.
5. After every coherent milestone or failure/fix boundary, update this state with exact files, commit/run IDs, verified results/failures, and the next exact action.
