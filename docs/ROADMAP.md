# Remaining Roadmap (2026-10-16)

**CONFIRMED:** Current maintenance goal is one authoritative document set and a fresh-install-only, current-security-preserving test scope. See [STATE](STATE.md) for whether release is truly complete. No percentage estimates.

The following steps are **PROPOSED**, not approved new features:

1. Disposable fresh MySQL installation with tagged image, Alembic head and first Owner login. **Done when:** SHA/digest, schema version, CLI and login evidence recorded.
2. Owner/Admin hierarchy, credit, Plan, Access Group and User lifecycle. **Done when:** scoped permissions, accounting ledger and retention pass, including retry, concurrent renewal and retirement.
3. Real Panel/Node mTLS, usage and device limits with disconnect/restart. **Done when:** authoritative counters and bounded reconnect are validated without double-charge.
4. Current-version backup and separate restore. **Done when:** checksum and record/credit/audit parity verified.
5. Performance at workload agreed by Owner. **Done when:** scripts and measured latency/resource thresholds recorded.
6. Choose future capability with explicit Owner approval. **Done when:** requirements and acceptance tests agreed.

**BLOCKED:** prior main-push CI backend MySQL matrix was skipped; require current PR full matrix and inspect actual job steps before publication.
