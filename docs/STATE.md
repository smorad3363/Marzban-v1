# V1 Verified State — 2026-10-16

Evidence: **VERIFIED** = direct GitHub evidence, **DOCUMENTED** = source claim, **NOT VERIFIED** = still needs testing.

- VERIFIED: main HEAD at review start `14e5c9032e5f94f783f34bde391bba318a6de925`.
- VERIFIED: latest stable release `v1.1.9`, published 2026-09-09: https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.9 .
- VERIFIED: PR #41 (Users Management V3) and PR #42 (release preparation) were merged. Former CODEX STATE incorrectly marked work as pending.
- VERIFIED: Release run https://github.com/smorad3363/Marzban-v1/actions/runs/34407436988 succeeded. Dashboard UI Contracts run https://github.com/smorad3363/Marzban-v1/actions/runs/34407246187 succeeded.
- VERIFIED: CI Checkpoints main-push run https://github.com/smorad3363/Marzban-v1/actions/runs/34407246190 concluded success, **but backend MySQL matrix was skipped** and package steps for image building, Node mTLS and upgrade were skipped. The push Branch Hygiene run was skipped. Skipped is not passed.
- CONFIRMED OWNER SCOPE: fresh empty DB and no historical operational Users/Admins/data. See [PROJECT](PROJECT.md).
- NOT VERIFIED: complete tests for pending maintenance v1.1.10, real fresh installation, image publication and restore. Do not claim v1.1.10 is released until GitHub confirms it.

## File disposition review before deletion

| Files | Decision | Reason |
| --- | --- | --- |
| `docs/CODEX/STATE.md` | MERGE then DELETE | stale state; status and next task transferred here |
| `docs/CODEX/V1_SCOPE.md` | MERGE then DELETE | stale v1.0.0; architecture and scope moved to PROJECT |
| `docs/ADMIN_SIMPLIFICATION_HANDOFF_FA.md` | KEEP for now | unique finished-stage detail; needs full dependency/knowledge audit before deletion |
| `docs/ADMIN_HIERARCHY_ROADMAP_FA.md`, `docs/MARZBAN_CODEX_MASTER_RUNBOOK.md` | KEEP as historical reference | long unique technical context not fully reviewed |
| `docs/legacy-v0/`, `docs/legacy/` | KEEP as historical reference | do not delete based on folder name alone |
| `tests/release_upgrade_lab.sh` | DELETE after detaching caller | exclusively vNext v5.2.0 -> V1 historical product migration |
| Existing backend tests and CI, MySQL 8.0 and 26.7.0 matrix | KEEP | current-version invariants and schema/bootstrap protections |
| Alembic migrations, dashboard build, LICENSE, historical release notes | KEEP | required schema, runtime, licensing or release integrity |

This document describes the **pre-PR verified baseline**, not success of a future release.

## NEXT EXACT TASK

Finish the focused documentation and historical-only-test changes on the working branch, inspect its final PR-head CI jobs including skipped steps, fix real failures while preserving both MySQL matrix engines, security and current accounting coverage, then merge/tag/publish only after all required gates provide direct evidence. Record actual release commit, tag, digest, result and subsequent documentation SHA here after publication.
