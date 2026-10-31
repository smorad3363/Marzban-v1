# Management-only Master and global alerts — work checkpoint

User authorized implementation on 2026-10-31 from Marzban-next-work-plan-2026-10-31.md (Library libfile_745c5b64644481918b931c8d6d61de26).
Base main/release: a4cc71a80030c02d0cc1fb5db6f3d7feb50f122d / v1.1.19.
Branch: feat/master-management-alert-center.

Implemented initial changes, not released or deployed:
- XRAY_LOCAL_CORE_ENABLED defaults true for existing installations; fresh installer explicitly writes false.
- Disabled mode skips local start/restart and local usage polling; remote Node lifecycle stays enabled.
- Local user provisioning/update/remove skips the local API in disabled mode.
- Core response reports local_enabled; config update does not treat intentionally disabled local core as startup failure.
- USED_TRAFFIC dashboard displays own base Toman/GiB price and explains per-account duration weighting.
- Offline deterministic public-address discovery in tests, required because automatic review rejected external ipify requests during test import. No runtime IP discovery behavior changed.

Focused validation: tests/test_management_only_master.py, test_core_inbound_lifecycle.py, test_core_review_runtime.py and test_access_group_core_tag_changes.py. Syntax/compile and diff whitespace checked. Full suite, installer lab, dashboard build/parity and both MySQL gates remain pending.

Remaining work before release:
1. Complete management-only status/UI and tests for no-local usage polling, remote provisioning/reconnect and fresh installer versus existing update behavior. Audit every local-core-dependent runtime path; keep subscription/config metadata and current live endpoints intact.
2. Implement durable scoped active incidents, separation of resolved/read state, threshold details and efficient summary/filtering. Keep Owner/all and Admin/self+descendant privacy.
3. Separate 120-second alert reconciliation from existing financial enforcement. Shared frontend refresh 60 seconds; critical known transitions must not wait for a full scan. Avoid duplicate queries/full subtree scans per viewer.
4. Add persistent global alert indicator and dashboard detail/filter UI; active critical issues remain visible, deduplicate unchanged notifications and signal stale/error state.
5. Review rate display and missing/zero semantics; no change to billing, coefficients, history or counters.
6. Canonical frontend build; full regression, MySQL 8.0/26.7.0, installer and mTLS gates. Synchronize unused next version only when implementation is ready. Do not merge or deploy partial work.
7. After exact-head gates and independent image/installer verification, fresh backup and authorized server update. Preserve existing local-core mode unless endpoint topology has been deliberately migrated.

Server was checked read-only: v1.1.19 Panel and MySQL healthy. No server changes were made during this implementation stage. On resume verify actual main, worktree, branch/head and server first; do not repeat previous wallet repairs or deployments.

Disposition: KEEP existing runtime/history/configuration assets; ADD tests/checkpoint. No unrelated deletion.
