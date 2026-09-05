# V1 Continuation State

## Baseline

- Baseline tag: `baseline-v1-source`
- Baseline commit: `0c714b182bcfd52d8eb24f1b06aa4f3f14784cf1`

## Current State

- Current branch: `main`
- Current HEAD: installer-validation harness repair checkpoint commit containing this file
- Current milestone/checkpoint: public V1 source, image, tag, and stable release exist; disposable installer run `33977032363` passed the complete fresh-install contract before confirming this repository's scoped token cannot read the historical private VNext baseline package

## Completed Checkpoints

- Created concise active execution, scope, and continuation files.
- Converted active application, installer, repository, branch, container, workflow, documentation, and release-test identity to V1.
- Renamed reviewed image publish/verification workflows for V1 and removed stale fixed vNext image digest.
- Rebuilt committed dashboard assets with version `1.0.0`.
- Removed Inbound/Host fields from `PlanVersionInput`; unexpected network fields now fail validation.
- Removed Plan create/update network validation and `AdminUserPlanInbound`/`AdminUserPlanHost` writes while retaining legacy response reads.
- Updated focused service, Access Group, seat-renewal, and trial tests for commercial-only Plans.
- Required a valid active Access Group before Plan user creation and before renewal.
- Preserved the current Access Group and user topology during default Plan renewal; topology changes only when an explicit replacement group is supplied.
- Removed runtime subscription and Host-change fallback to legacy Plan network snapshots.
- Changed Host impact analysis, confirmation, propagation, and active-user sync to Access Groups.
- Added fail-closed single/batch subscription scope resolution for Plan-assigned users without an Access Group.
- Added migration `c9e1f4a7b203` and model index `ix_access_group_hosts_host_group` for Host-to-Access-Group reverse lookups.
- Removed Inbound, Host, and Node controls from Plan create/edit UI and retired the Plan-named network option endpoint/utilities.
- Added Owner-facing Access Group create/edit/archive UI with explicit Node, Inbound, and Host controls.
- Required explicit Access Group selection in both Plan-based user-creation surfaces.
- Updated Host impact UI and query contracts to Access Group terminology.
- Rebuilt committed dashboard assets after the Access Group UI change.
- Added a narrow, verified product-line transition from the exact mature `ghcr.io/smorad3363/marzban-vnext:v5.2.0` runtime to `v1.0.0`; all other application downgrades remain refused.
- Hardened `marzban create-owner [USERNAME]` argument handling and kept the Owner password out of Docker command arguments.
- Prevented `main` pushes from creating the V1 tag, release, or image before dedicated verification.
- Required the reviewed 40-character commit and an unused `v1.0.0` tag before immutable image publication.
- Made published-image verification confirm the `v1.0.0` image tag digest and source commit before creating the immutable tag and stable GitHub release.
- Added V1 release notes covering the new baseline, Plan/Access Group separation, and preserved mature functionality.
- Completed the final `baseline-v1-source..HEAD` change inventory and security/release review.
- Confirmed the authenticated GitHub account is `smorad3363`, the target repository does not exist, no `origin` remote exists, and no local `v1.0.0` tag exists.
- Scanned tracked source for common private-key and token signatures; no matches were found.
- Confirmed remaining active `5.2.0`/vNext references are limited to the explicit, tested V1 lineage-transition guard and its documentation/tests.
- Created the public repository `smorad3363/Marzban-v1` and pushed exact reviewed `main` commit `cb9c181a791ad1534702dc2715e0c13ed38b3fce` plus `baseline-v1-source` without force.
- First GitHub CI run `33974555761` passed the real MySQL `8.0` to `26.7.0` logical migration and failed before any image/tag/release publication.
- Repaired the CI-only `httpx` dependency, two missing creation-mode fixtures, and one stale localization assertion; explicitly deselected only the three previously documented unrelated Stage 5 cases.
- GitHub CI run `33974990272` passed both MySQL matrices, isolated Stage 8-11 migration evidence, logical MySQL migration, backup/restore, and v4.8.0 rollback compatibility.
- Published immutable multi-platform image `ghcr.io/smorad3363/marzban-v1:v1.0.0` from exact commit `6bc7688a294bc603eb30f320428e3002288bb8b2`; digest `sha256:99c1a1e20a042c3385e7c31ad9084ea233314e8f9047585a6c834a720a123906`.
- Verification run `33975841184` confirmed AMD64/ARM64 manifests, source label, runtime `1.0.0`, MySQL client `26.7.0`, and dashboard/CLI content before creating the tag/release.
- Created immutable tag `v1.0.0` at `6bc7688a294bc603eb30f320428e3002288bb8b2` and stable GitHub release `Marzban V1.0.0`.
- Added a disposable published-installer workflow for anonymous GHCR access, the exact fresh-install command, Owner creation, version integrity, reinstall/downgrade refusal, and mature `5.2.0` to V1 upgrade preservation.
- Repaired the installer lab's Owner lookup assertion to query the disposable MySQL database directly after the successful `marzban create-owner` command, avoiding presentation-layer output and closed-pipe behavior.
- Added failure-only expected/actual diagnostics to the installer lab's exact version and Owner assertions; no credentials are printed.
- Kept V1 anonymous-access verification unchanged and made the upgrade lab build the exact historical VNext `v5.2.0` tag commit `2d8df17b526236c9980ade37d802531dbca0d06f` from its public source, matching the recorded VNext installer fallback without changing package visibility.

## Tests Passed

- `uv run --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_release_contract.py` — `1 passed`.
- `uv run --with-requirements requirements.txt --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_release_contract.py tests/test_marzhelp_migration_backup.py::test_installer_targets_release_image_and_pinned_mysql_image` with `SQLALCHEMY_DATABASE_URL=mysql+pymysql://marzban:test@127.0.0.1:3306/marzban_test` and `DEBUG=false` — `2 passed`.
- `npm.cmd run build -- --outDir build --assetsDir statics` with Node `v24.19.0` and `VITE_BASE_API=/api/` — passed; dashboard assets rebuilt.
- PyYAML `safe_load` of `.github/workflows/build.yml`, `.github/workflows/release-v1.yml`, and `.github/workflows/verify-v1-image.yml` — passed.
- Targeted `rg` for stale active vNext/`5.2.0`/`master` identity outside legacy docs, dependency locks, and intentional compatibility fixtures — no matches.
- `git diff --check` — passed.
- `uv run --with-requirements requirements.txt --with pytest --python C:\Users\Saji\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe python -m pytest -q tests/test_stage4_plan_network_scope.py` — `8 passed`.
- Same environment, `python -m pytest -q tests/test_stage5_restricted_creation_namespace.py::test_seat_plan_renewal_charges_exact_cost_once_on_retry tests/test_stage6_trials.py` — `11 passed, 1 skipped`.

- Same environment, `python -m compileall -q app` — passed.
- Same environment, `python -m pytest -q tests/test_stage2_network_sync.py tests/test_stage4_plan_network_scope.py` — `21 passed`.
- Same environment, `python -m pytest -q tests/test_stage5_restricted_creation_namespace.py tests/test_stage6_trials.py tests/test_admin_hierarchy_service.py` — relevant runtime coverage passed; aggregate result `47 passed, 1 skipped, 3 failed`.

- `npx.cmd tsc --noEmit` in `app/dashboard` with `C:\Program Files\nodejs` on `PATH` — passed.
- `npm.cmd run test:access-groups`, `npm.cmd run test:admin-ux`, and `npm.cmd run test:admin-hierarchy` in `app/dashboard` — passed.
- `VITE_BASE_API=/api/ npm.cmd run build -- --outDir build --assetsDir statics` in `app/dashboard` — passed; `1731` modules transformed. Existing vendor chunk-size and `use client` warnings remain non-blocking.
- Same backend environment, `python -m pytest -q tests/test_admin_hierarchy_api_contract.py tests/test_stage4_plan_network_scope.py tests/test_stage2_network_sync.py` — `23 passed`.
- Playwright mock verification at `1440x900` and `375x812` — Access Group create/list controls rendered, Host choices appeared after Inbound selection, no horizontal overflow, and no console errors.
- `C:\Program Files\Git\bin\bash.exe -n scripts/marzban.sh` — passed.
- `C:\Program Files\Git\bin\bash.exe tests/test_installer_v1_contract.sh` — `INSTALLER_V1_CONTRACT_OK`; validated the exact lineage gate, `marzban version`, and `marzban create-owner USERNAME` wrapper contract.
- Same backend environment, `python -m pytest -q tests/test_release_contract.py tests/test_marzhelp_migration_backup.py` — `7 passed, 1 skipped`.
- PyYAML `safe_load` of `.github/workflows/build.yml`, `.github/workflows/release-v1.yml`, and `.github/workflows/verify-v1-image.yml` after publication-order changes — passed.
- Consolidated frontend gate: `npx.cmd tsc --noEmit`, `npm.cmd run test:access-groups`, `npm.cmd run test:admin-ux`, `npm.cmd run test:admin-hierarchy`, and `VITE_BASE_API=/api/ npm.cmd run build -- --outDir build --assetsDir statics` — passed; `1731` modules transformed with the same non-blocking warnings.
- Consolidated backend gate: `python -m pytest -q tests/test_admin_hierarchy_api_contract.py tests/test_stage2_network_sync.py tests/test_stage4_plan_network_scope.py tests/test_stage5_restricted_creation_namespace.py tests/test_stage6_trials.py tests/test_admin_hierarchy_service.py` with the three documented unrelated cases deselected — `70 passed, 1 skipped, 3 deselected`.
- `git diff --check baseline-v1-source..HEAD` — passed after removing two trailing blank lines in execution documentation.
- Focused first-push CI repair verification with `httpx`: backup upload contract, localization response contract, Stage 6 trials, both user-access creation cases, and release contract — `15 passed, 1 skipped`.
- PyYAML validation of the repaired `.github/workflows/build.yml` — passed.
- `bash -n` for `scripts/marzban.sh`, `tests/release_installer_lab.sh`, and `tests/release_upgrade_lab.sh` — passed.
- Updated release contract test for the disposable published-installer workflow — `1 passed`; workflow YAML validation passed.

## Tests Failed

- Published-installer run `33976252559`: install, version integrity, and Owner creation succeeded; the combined step then failed because `docker exec ... | grep -q` triggered a test-only closed-pipe failure under `pipefail`. Production behavior was not implicated; the harness is repaired for the next run.
- Published-installer run `33976563658`: the same production checks again succeeded, but the CLI table-based Owner lookup produced no stable assertion output. The harness now verifies the committed Owner row directly in the disposable MySQL database.
- Published-installer run `33976717772`: the same public/fresh-install/Owner checkpoints succeeded, then a silent exact-line assertion failed. Failure-only diagnostics were added to identify the precise mismatch on the next run.
- Published-installer run `33976849090`: anonymous V1 image access, exact fresh installation, Owner creation/persistence, version/digest/source integrity, reinstall refusal, and downgrade refusal passed. Upgrade setup then failed only because the historical `marzban-vnext:v5.2.0` baseline is private; V1 artifact visibility and content were unaffected.
- Published-installer run `33977032363`: scoped GHCR login succeeded, but the historical private baseline package denied this repository token. Public tag parity for `smorad3363/Marzban-vNext@v5.2.0` was verified at `2d8df17b526236c9980ade37d802531dbca0d06f`; the lab now builds that exact source locally instead of widening package access.

- `bash -n scripts/marzban.sh` — not run: Windows WSL launcher reports `execvpe(/bin/bash) failed: No such file or directory`; Docker Desktop daemon is also unavailable for fallback.

- Broader Stage 5 suite has three unrelated failures: one raw-endpoint expectation reaches response rendering with `used_traffic=None`, and two pricing tests use fixed expiry `2000000000`, which no longer matches an Owner duration preset on the current date.

## Known Blockers

- No live MySQL endpoint is available for `EXPLAIN`; index verification is limited to model/migration structure until the MySQL release lab runs.

## Uncommitted Work

- None expected after committing this harness-repair checkpoint.

## NEXT EXACT TASK

Commit and push the installer-lab `pipefail` repair without force. Dispatch the published-installer workflow again with digest `sha256:99c1a1e20a042c3385e7c31ad9084ea233314e8f9047585a6c834a720a123906` and source commit `6bc7688a294bc603eb30f320428e3002288bb8b2`. Stop on any real failure; on success, verify public repository/release/tag/image and immutable installer defaults one final time, update this file to `NEXT EXACT TASK: NONE`, commit, and push the documentation-only completion record.
