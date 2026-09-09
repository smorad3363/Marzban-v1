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
- UTC timestamp parsing, current-activity semantics, status legend, and legacy Admin counting were corrected during final self-review.
- Version surfaces, `RELEASES.md`, and `docs/RELEASE_NOTES_v1.1.8.md` are prepared for `v1.1.8`.
- Canonical Release workflow verifies both Stage 1 UI and authenticated-autofill contracts.
- All one-time release-preparation scripts/workflows have been removed from the net PR diff.

## Validation History

- One earlier final-candidate CI run exposed a missing `aria-live="polite"`; fixed. Its backend result was otherwise 448 passed, 1 skipped, 3 deselected.
- One later installer contract run exposed stale `RELEASES.md` target metadata; fixed by setting release target/install/update references to `v1.1.8` while keeping prior tags immutable.
- Targeted release-preparation validation passed Python compilation, Stage 1 UI contract, authenticated-autofill contract, TypeScript/production dashboard build, release-surface checks, and canonical build regeneration.
- A fresh full PR CI run on the final HEAD is still required before merge.

## Non-regression Invariants

- Preserve Node Operations V2, one authoritative reset-counter collector, safe Admin retirement, Plan permissions, Access Group semantics, Owner unrestricted behavior, and Panel-to-Node mTLS.
- `v1.1.7` is immutable and must never be moved/recreated.
- `v1.1.8` may be tagged only from the final reviewed squash-merge commit on `main` after all required CI gates are green.

## Last Work File

`RELEASES.md`

## Last Work Section

Final release metadata contract: `Release target: v1.1.8`, matching notes/install/update references, while existing `v1.1.7` remains immutable.

## NEXT EXACT TASK

1. Treat the current branch HEAD after this checkpoint as the final PR candidate and run both `CI Checkpoints` and `Dashboard UI Contracts` to completion.
2. If any gate fails, inspect the exact failing job/step and fix only its root cause; regenerate committed dashboard build only if dashboard source changes.
3. Re-review the final PR diff for scope/security/unrelated changes; verify one-time helpers are absent and `main`/`v1.1.7` have not moved.
4. Mark PR #39 ready and squash-merge only the exact verified head.
5. Verify the squash commit on `main`, post-merge CI, and all release surfaces (`VERSION`, `app/__init__.py`, `scripts/marzban.sh`, `docker-compose.yml`, `RELEASES.md`, `docs/RELEASE_NOTES_v1.1.8.md`).
6. Verify `v1.1.8` does not already exist, then create it at the exact verified release commit on `main` without moving any existing tag.
7. Wait for the canonical `Release` workflow to succeed, including dashboard contracts/parity, multi-arch GHCR publish, anonymous/runtime image verification, and GitHub Release creation.
8. Confirm tag SHA, GitHub Release, `ghcr.io/smorad3363/marzban-v1:v1.1.8`, `latest`, and release workflow source SHA all match the verified release commit.

## Recovery Rule

When work resumes, fetch this file, fetch/review `Last Work File`, verify PR/main/tag/release state, then continue from the first incomplete `NEXT EXACT TASK` item. If `v1.1.8` already exists, never recreate or move it; verify publication instead.
