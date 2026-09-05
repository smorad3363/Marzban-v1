# V1 Continuation State

## Baseline

- Baseline tag: `baseline-v1-source`
- Baseline commit: `0c714b182bcfd52d8eb24f1b06aa4f3f14784cf1`

## Current State

- Current branch: `main`
- Current HEAD: Plan commercial-contract checkpoint commit containing this file
- Current milestone/checkpoint: Plan create/update request and persistence detached from network topology

## Completed Checkpoints

- Created concise active execution, scope, and continuation files.
- Converted active application, installer, repository, branch, container, workflow, documentation, and release-test identity to V1.
- Renamed reviewed image publish/verification workflows for V1 and removed stale fixed vNext image digest.
- Rebuilt committed dashboard assets with version `1.0.0`.
- Removed Inbound/Host fields from `PlanVersionInput`; unexpected network fields now fail validation.
- Removed Plan create/update network validation and `AdminUserPlanInbound`/`AdminUserPlanHost` writes while retaining legacy response reads.
- Updated focused service, Access Group, seat-renewal, and trial tests for commercial-only Plans.

## Tests Passed

- `uv run --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_release_contract.py` — `1 passed`.
- `uv run --with-requirements requirements.txt --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_release_contract.py tests/test_marzhelp_migration_backup.py::test_installer_targets_release_image_and_pinned_mysql_image` with `SQLALCHEMY_DATABASE_URL=mysql+pymysql://marzban:test@127.0.0.1:3306/marzban_test` and `DEBUG=false` — `2 passed`.
- `npm.cmd run build -- --outDir build --assetsDir statics` with Node `v24.19.0` and `VITE_BASE_API=/api/` — passed; dashboard assets rebuilt.
- PyYAML `safe_load` of `.github/workflows/build.yml`, `.github/workflows/release-v1.yml`, and `.github/workflows/verify-v1-image.yml` — passed.
- Targeted `rg` for stale active vNext/`5.2.0`/`master` identity outside legacy docs, dependency locks, and intentional compatibility fixtures — no matches.
- `git diff --check` — passed.
- `uv run --with-requirements requirements.txt --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_stage4_plan_network_scope.py` — `8 passed`.
- Same environment, `python -m pytest -q tests/test_stage5_restricted_creation_namespace.py::test_seat_plan_renewal_charges_exact_cost_once_on_retry tests/test_stage6_trials.py` — `11 passed, 1 skipped`.

## Tests Failed

- `bash -n scripts/marzban.sh` — not run: Windows WSL launcher reports `execvpe(/bin/bash) failed: No such file or directory`; Docker Desktop daemon is also unavailable for fallback.

## Known Blockers

- Local Bash runtime unavailable; installer syntax verification remains required before publication.

## Uncommitted Work

- None; working tree clean after this checkpoint commit.

## NEXT EXACT TASK

Require a valid Access Group for Plan user creation, preserve the current Access Group on renewal, remove all runtime fallback to legacy Plan network scope (including subscription resolution and host-change Plan revisions), add focused fail-closed and renewal-preservation tests, verify, update this file, and commit the runtime Access Group checkpoint.
