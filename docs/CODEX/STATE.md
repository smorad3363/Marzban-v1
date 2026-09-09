# V1 Continuation State

## Active Task: v1.1.8 Dashboard Owner/Admin V2 release candidate

- Working branch: `feat/dashboard-owner-admin-v2`
- Pull request: `#39`
- Base/main SHA at task start: `e8f9ce09c7939c15a2fbdeae858ba990d79db846`
- Immutable prior release: `v1.1.7` MUST remain at `c0775a624b7081f794b492e4596bbc484aa6be02`; never move/recreate it.
- Target release: `v1.1.8`.

## Completed Product Work

- Credential autofill is suppressed throughout authenticated UI and Chakra portals; Login retains `username` / `current-password` autofill.
- Owner/Admin Dashboard V2 uses `/api/dashboard/overview` with backend-enforced role/scope.
- Real traffic history comes from existing `NodeUserUsage`; no additional Xray reset-counter poller exists.
- Attention, top consumers, recent users, current activity, status distribution, Owner Node summary, and Owner Admin summary are real database aggregates.
- Admin sees no Owner-only Node/Admin summary and receives no billing-mode distribution from Dashboard overview.
- Admin credit UI remains generic and does not disclose accounting-model basis.
- Users remains the dedicated management surface.
- `host_update_impact` unrelated behavior was restored to the `main` baseline during self-review.
- Version surfaces and release notes are prepared for `v1.1.8`; canonical Release workflow also verifies the authenticated-autofill contract.

## Non-regression Invariants

- Preserve Node Operations V2, one authoritative reset-counter collector, safe Admin retirement, Plan permissions, Access Group semantics, Owner unrestricted behavior, and Panel-to-Node mTLS.
- `v1.1.7` is immutable and must never be moved/recreated.
- `v1.1.8` may be tagged only from the final reviewed merge commit on `main` after all required CI gates are green.

## Last Work File

`app/dashboard/src/components/DashboardOverview.tsx`

## Last Work Section

Final release-candidate self-review: UTC timestamp handling, generic Admin credit presentation, accurate status/current-activity semantics, legacy-safe Owner Admin summary, and Admin billing-mode privacy.

## NEXT EXACT TASK

1. Remove the one-time release-preparation script/workflow from the feature branch.
2. Verify the resulting clean PR #39 HEAD and run both `CI Checkpoints` and `Dashboard UI Contracts` to completion.
3. If any gate fails, inspect the exact failing job/step and fix only its root cause; regenerate committed dashboard build if dashboard source changes.
4. Re-review the final PR diff for scope/security/unrelated changes and verify `main` has not moved.
5. Mark PR #39 ready and squash-merge only the verified head.
6. Verify post-merge `main` CI and all release surfaces (`VERSION`, `app/__init__.py`, `scripts/marzban.sh`, `docker-compose.yml`, `docs/RELEASE_NOTES_v1.1.8.md`).
7. Verify `v1.1.8` does not already exist, then create it at the exact verified release commit on `main` without moving any existing tag.
8. Wait for the canonical `Release` workflow to succeed, including dashboard contracts/parity, multi-arch GHCR publish, anonymous/runtime image verification, and GitHub Release creation.
9. Confirm tag SHA, GitHub Release, `ghcr.io/smorad3363/marzban-v1:v1.1.8`, `latest`, and release workflow source SHA all match.

## Recovery Rule

When work resumes, fetch this file, fetch/review `Last Work File`, verify PR/main/tag/release state, then continue from the first incomplete `NEXT EXACT TASK` item. If `v1.1.8` already exists, never recreate or move it; verify publication instead.
