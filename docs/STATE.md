# V1 release candidate — 2026-10-30

Release target: v1.1.11. Unified PR #45 includes commercial renewal enforcement,
Access Group runtime scope, API listener, durable non-reset usage cursors, clock
jump safety, atomic node user history, seat creation guard and Admin price safety.
Three formerly deselected regressions are reenabled with valid pricing fixtures.
Permanent installer: scripts/install.sh -> official installer -> latest published
stable version, with version-specific image/configuration/CLI.

Previous published stable remains v1.1.10 until canonical release succeeds.
Final PR-head MySQL 8.0/26.7.0, dashboard parity, installer and mTLS evidence must
be checked before merge. Real traffic, load, full lifecycle and independent
restart/restore qualification remain NOT VERIFIED. Volatile Xray counters may
lose unsampled traffic during simultaneous database outage and Xray reset.
No live server or production database has been changed.

## Previous publication evidence (v1.1.10)

# V1 Verified State — 2026-10-16

Evidence: **VERIFIED** = directly observed in GitHub/Actions; **DOCUMENTED** = a source statement; **NOT VERIFIED** = still needs qualification.

## Current verified release

- **VERIFIED:** PR [#43](https://github.com/smorad3363/Marzban-v1/pull/43) merged into `main`, resulting in source/release commit `b09801ca922199b06eaf43938664544331328668`. Previous stable version was `v1.1.9`; this maintenance release is `v1.1.10`.
- **VERIFIED:** annotated immutable `v1.1.10` tag points to `b09801ca922199b06eaf43938664544331328668`. [GitHub Release](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.10) published 2026-10-16; canonical [Release workflow](https://github.com/smorad3363/Marzban-v1/actions/runs/38929559689) succeeded.
- **VERIFIED:** published GHCR image `ghcr.io/smorad3363/marzban-v1@sha256:2b37aefc1b37a2e3f6c27489e69ca323f34e5aa3c00ff2e51c55c59361f5bb8f`, sourced from `b09801ca922199b06eaf43938664544331328668` with `linux/amd64` and `linux/arm64`; standalone [image verification](https://github.com/smorad3363/Marzban-v1/actions/runs/38931246448) **PASS**.
- **VERIFIED:** the exact image/digest passed the disposable [fresh-install lab](https://github.com/smorad3363/Marzban-v1/actions/runs/38931250688), including MySQL bootstrapping, healthy version `v1.1.10`, first Owner creation and downgrade refusal (`FRESH_INSTALL_CREATE_OWNER_VERSION_PASS`). This was an isolated CI runner, **not a production deployment**.
- **VERIFIED:** exact final PR head `95974c32ba5b6e53f636a6a458a8305af079c7ae` passed five required GitHub checks: backend on both MySQL 8.0 and 26.7.0, installer/panel/Node including mTLS and cross-version MySQL logical restore, dashboard build/parity, and dashboard UI contracts. [PR CI](https://github.com/smorad3363/Marzban-v1/actions/runs/38916527553) / [PR dashboard](https://github.com/smorad3363/Marzban-v1/actions/runs/38916527482).
- **VERIFIED:** [main-push CI](https://github.com/smorad3363/Marzban-v1/actions/runs/38928817307) and [dashboard contracts](https://github.com/smorad3363/Marzban-v1/actions/runs/38928817447) succeeded. On the main-push event the backend matrix, image-build/mTLS and logical-restore substeps were **SKIPPED** (they are covered by the final-head PR runs, not by that push). The main-push Branch Hygiene job was also **SKIPPED**; skipped is not passed.
- **VERIFIED:** temporary tag/verification dispatch branches were deleted. No live servers, external volumes or operational databases were changed for this release.

## Owner-approved scope

Fresh deployment into a new empty MySQL database; no older live Users/Admins/data or historical product upgrades are required for this milestone. Preserve current-version migrations, security, Owner/Admin scope, financial privacy, authoritative usage, Plan-as-commerce, Access Group-as-network-authority, backup and restore, Panel/Node mTLS, retries/idempotency and concurrent accounting. See [PROJECT](PROJECT.md) and [TESTING](TESTING.md).

## File disposition and maintenance changes

| Files | Decision / evidence |
| --- | --- |
| `docs/CODEX/STATE.md`, `docs/CODEX/V1_SCOPE.md` | **MERGE then DELETE**: superseded by this STATE and PROJECT |
| `docs/legacy/MARZBAN_FILE_HYGIENE_AUDIT.md` | **MERGE then DELETE**: lasting precautions moved into legacy README |
| `tests/release_upgrade_lab.sh` | **DELETE**: vNext 5.2.0 -> historical V1 product-line upgrade only |
| Historical v4.8.0 rollback CI check | **REMOVE**: historical application rollback outside owner-approved fresh-install scope |
| Temporary one-off release workflow helpers | **DELETE**: canonical `.github/workflows/build.yml` remains the official publisher |
| `docs/legacy-v0/`, unique historical runbooks and Admin design rationale | **KEEP** with explicit historical-only labels |
| Alembic migrations, LICENSE, release assets, both current MySQL engines, security/accounting tests, backup/current DB restore, dashboard source/build | **KEEP** as necessary present-version functionality |

The previous incomplete state and historical handoffs were consolidated in PR #43; no new product capabilities or runtime refactor were introduced.

## Remaining qualification (NOT VERIFIED)

The isolated installer demonstrates fresh bootstrap and first Owner; it does **not** independently certify the entire real-world Owner/Admin/User commercial lifecycle under traffic, Node restart/reconnect and device-limit workloads, full historical-current-version accounting scenarios or measured performance. These are future acceptance tasks, not evidence against the published release. Do not represent production deployment as completed.

## NEXT EXACT TASK

On a **separate disposable v1.1.10 installation**, exercise the complete Owner/Admin/User, credit/renewal, Plan versus Access Group, Node reconnect/device-policy and current-data backup/restore lifecycle; record actual success/fail evidence and any defects before proposing new features.
