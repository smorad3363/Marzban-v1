# Remaining Roadmap — 2026-10-16

**CONFIRMED:** Published stable release [v1.1.10](https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.10) preserves the approved fresh-empty-MySQL scope. Follow [STATE](STATE.md) for verified outcomes. The following remaining stages are **PROPOSED**, not approved feature development.

1. **VERIFIED (basic disposable release install):** tagged image, exact source SHA/digest, empty MySQL bootstrap, healthy runtime, first Owner and version/downgrade controls passed in [installer CI](https://github.com/smorad3363/Marzban-v1/actions/runs/38931250688). A full lifecycle qualification is separate.
2. **PROPOSED:** Owner/Admin hierarchy, credit, Plan, Access Group and User lifecycle. **Done when:** scoped permissions, accounting and history/retention pass including retries, concurrent renewal and retirement.
3. **PROPOSED:** real Panel/Node mTLS, usage, device limits and disconnect/restart. **Done when:** authoritative counters and bounded reconnect are validated without duplicate accounting.
4. **PROPOSED:** backup and separate restore for current-version newly created data. **Done when:** checksum plus record, credit and audit parity are confirmed.
5. **PROPOSED:** workload/performance measured against Owner-agreed targets. **Done when:** scripts and measured latency/resource thresholds are recorded.
6. **PROPOSED:** select future features only after explicit Owner scope approval. **Done when:** requirements and acceptance tests are agreed.

**Resolved former blocker:** all required final PR-head CI checks passed, and the independent published-image and fresh-install verifiers passed. Some main-push jobs intentionally remained **SKIPPED**; see [STATE](STATE.md) for exact coverage.
