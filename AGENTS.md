# V1 Active Execution Rules

Read in order: `AGENTS.md`, `docs/PROJECT.md`, `docs/STATE.md`, `docs/ROADMAP.md`, `docs/TESTING.md`, `docs/RELEASE.md`. Inspect actual git status, current main, open PRs, tags, Actions and releases before doing work. Preserve uncommitted work. Historic documents (including `docs/legacy-v0/`, old Admin roadmaps and runbooks) are **reference only**, not active instructions.

Owner-approved: **fresh empty MySQL deployment**; no former operational users, reseller Admins or old data. No historic product migration/role backfill/old-release rollback test required. Keep fresh schema Alembic migration chain, current-version data retention, security, billing, authorization, concurrency, backup and restore tests.

Invariant: Plan owns commercial entitlement; Access Group alone owns Nodes, Inbounds and Hosts. Missing necessary Access Group fails closed. Backend enforces Owner/Admin scope, preserves private billing, authoritative usage, current history, idempotent retries and Admin retirement. Preserve Node runtime and Panel-to-Node mTLS. Keep MySQL 8.0 and 26.7.0 matrix; don't change product features or runtime compatibility code under document cleanup.

Each deletion requires KEEP/MERGE/DELETE classification and runtime/build/CI reference check. Preserve LICENSE, attribution, required build assets, fixtures and migrations. `VERIFIED` needs direct evidence, `DOCUMENTED` is a prior claim, `NOT VERIFIED` means incomplete; skipped != passed. Compare baseline tag `baseline-v1-source`, review secrets/diff, require final PR-head gates before merge and exact immutable patch tag. No force pushes, moved/reused tags, bypassed checks or production deployments.
