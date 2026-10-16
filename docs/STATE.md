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
| `docs/ADMIN_SIMPLIFICATION_HANDOFF_FA.md` | KEEP as labeled historical reference | contains unique financial/UI implementation rationale; stale resume directives are explicitly non-authoritative |
| `docs/ADMIN_HIERARCHY_ROADMAP_FA.md`, `docs/MARZBAN_CODEX_MASTER_RUNBOOK.md` | KEEP as historical reference | unique stage-by-stage design and evidence; explicitly historical, not a second active execution contract |
| `docs/legacy-v0/` and other `docs/legacy/` records | KEEP as labeled historical reference | imported architecture, decisions, review evidence, design and operator provenance; historical instructions are superseded by AGENTS |
| `docs/legacy/MARZBAN_FILE_HYGIENE_AUDIT.md` | MERGE then DELETE | obsolete 2026-08-22 local cache/working-tree report; lasting preservation/build-context cautions moved to `docs/legacy/README.md`; only inbound document link updated, no runtime/build/test consumers |
| `.github/workflows/tag-and-dispatch-v1.1.10-once.yml` | DELETE | temporary automatic main-push publisher; canonical tag/manual Release workflow already exists, and temporary helpers must not remain in the final tree |
| `tests/release_upgrade_lab.sh` | DELETE after detaching caller | exclusively vNext v5.2.0 -> V1 historical product migration |
| Existing backend tests and CI, MySQL 8.0 and 26.7.0 matrix | KEEP | current-version invariants and schema/bootstrap protections |
| Alembic migrations, dashboard build, LICENSE, historical release notes | KEEP | required schema, runtime, licensing or release integrity |

## Current correction checkpoint

- VERIFIED by native Git: PR #43 source was `d6bdeb6a55909982d802ff2c201492c98ae6ab2f` when this correction started; main remains `14e5c9032e5f94f783f34bde391bba318a6de925`. The working tree was clean before corrections. No `v1.1.10` tag existed at that check.
- VERIFIED by source history: dashboard assets were rebuilt in `6991abb`; the dashboard refresh helper was removed in `1a3dd73`. A second one-time publishing helper was added in `d6bdeb6`; it is removed by this correction. Use the canonical Release workflow after final-head gates.
- VERIFIED by workflow/source inspection: both supported MySQL engines are retained. The 8.0 logical dump/checksum -> 26.7.0 restore gate is restored because it protects newly created data across supported database engines, not just historical product upgrades. Historical vNext-to-V1 and v4.8.0 application rollback gates remain excluded.
- Historical handoffs, runbooks and imported execution instructions now explicitly link to the active AGENTS/state documents and mark old commands and results as historical. Their unique technical context is retained; no new roadmap is introduced.
- Access limitation: `gh api` requests are denied at the environment HTTPS proxy (CONNECT 403 for `api.github.com`). Native Git and public GitHub HTML reads work. Do not infer PR merge permission or completed publication from Git read access.
- NOT VERIFIED: CI on the forthcoming correction commit, final merge, `v1.1.10` publication, image digest/revision, and a fresh installation of the published release. Local and earlier CI results cannot replace final-head evidence.

## Local validation of this correction

- PASS: installer Bash syntax and `bash tests/test_installer_v1_contract.sh` (`INSTALLER_V1_CONTRACT_OK`).
- PASS: `python -m pytest -q --disable-warnings tests/test_release_contract.py tests/test_ci_matrix_contract.py tests/test_node_deployment_contract.py tests/test_release_workflow_contract.py tests/test_release_workflow_fast_path.py` — 23 passed.
- PASS: exact restored workflow shell block for logical dump/checksum/restore, executed on isolated MySQL 8.0 and 26.7.0 Docker volumes; checksum, target version and sentinel-content assertions succeeded (exit 0). Only the test's own containers/volumes were removed.
- PASS: changed-document relative Markdown link targets and `git diff --check`. Version alignment is covered by the release contract tests.
- The immutable `baseline-v1-source` tag was fetched and scoped changes compared. Full final release-source/baseline review and final-head remote gates remain required before publication.

This checkpoint supersedes the pre-PR-only status. A commit containing this document is not a release-completion claim.

## NEXT EXACT TASK

Validate and push this correction on PR #43, then inspect all required jobs for its exact final commit. Resolve access to the GitHub API if needed to inspect protected-branch requirements and merge the PR. Only after verified gates, merge through the PR and publish from the exact reviewed main commit via the canonical Release workflow; record the immutable tag, source SHA, image digest, fresh-install result and follow-up documentation commit. Do not merge or publish while required checks or access are unresolved.
