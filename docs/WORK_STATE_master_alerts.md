# Management-only Master and global alerts — work checkpoint

Authorized implementation from Marzban-next-work-plan-2026-10-31.md. Branch feat/master-management-alert-center; base a4cc71a80030c02d0cc1fb5db6f3d7feb50f122d (v1.1.19).

Implemented: management-only fresh install with existing mode retention; local runtime/stats/provisioning/log guards; explicit UI status; USED_TRAFFIC own base-rate display; durable scoped incidents/receipts/resolution history; authenticated watermark stream with 60-second foreground fallback; 120-second separate comprehensive collector; batched legacy warnings; financial/create/Trial/policy transaction integration.

Target v1.1.20. Required next actions: finish final regression/UI build and meaningful checks, inspect diff/secrets and exact-head PR gates; merge through canonical reviewed publisher only on PASS; verify immutable tag/image/installer; then fresh live recovery snapshot and authorized update preserving existing endpoints/mode. Record real evidence and limitations. Do not bypass or move tags.

Server last checked read-only: v1.1.19 Panel and MySQL healthy. No live modifications in this implementation stage yet. On resume verify actual branch/head/worktree, Actions and server before repeating operations. Public-IP discovery requests are stubbed in tests because automatic review rejected unnecessary external discovery during imports; runtime discovery unchanged.

Disposition: KEEP existing runtime/configuration/history assets; ADD incident files, tests and checkpoint. Replace generated bundles only through canonical build. See RELEASE_NOTES_v1.1.20.md for final behavior.
