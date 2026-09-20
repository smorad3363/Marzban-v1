# Product-first R08.a — Product assignment and authorization RED-test checkpoint

Date: 2026-09-20
Branch: `docs/product-first-v3-1-r01-ledger`
Source SHA: `e2ee36051abdf5e2698bc6bca996216b9aaf3377`

## Recovery state

```yaml
stage: R08
substep: R08.a
state: DONE_RED_TESTS
branch: docs/product-first-v3-1-r01-ledger
source_sha: e2ee36051abdf5e2698bc6bca996216b9aaf3377
production_code_changed: false
migration_changed: false
version_changed: false
main_changed: false
release_actions_performed: []
next_exact_action: 'After separate user authorization, execute only R08.b: implement the minimum additive Product access schema/service for billing-mode grants and the shared fail-closed selection checks required by these tests. Do not start R08.c UI or explicit-ID implementation beyond the shared schema contract.'
```

## Test-first contract added

Added `tests/test_product_assignment_authorization.py`. It defines the Product new-selection boundary before implementation:

- Product access has dedicated mode and exact-Admin association tables, separate from legacy Access Group permissions.
- A Product with no access rows is deny-all; there is no legacy public fallback.
- A grant to `USED_TRAFFIC`, `ALLOCATED_TRAFFIC`, or `USER_CREDIT` applies to current and future active Admins in that billing mode.
- Exact Admin-ID grants do not leak to another Admin with the same billing mode.
- Only Owner may change Product access policy.
- `LEGACY_COMPAT` and historical `SEAT_CREDIT` cannot be new Product policy modes.
- Unknown, Owner-role, or inactive explicit targets are rejected.
- Selection rechecks Product archive state, live Product network, and the target Admin's inbound ceiling.
- Policy revocation blocks new selection without deleting Product identity.
- Admin-visible Product listing is scoped by the same server-side authorization.

The tests intentionally name the shared backend contract expected from later implementation:

```text
products.replace_access_policy
products.require_selectable
products.list_selectable
product_billing_mode_access
product_admin_access
```

R08.a does not implement those symbols or tables. This keeps the required RED phase distinct from R08.b and R08.c.

## Verification evidence

Isolated environment: repository-local `.venv`; `SQLALCHEMY_DATABASE_URL` pointed at the non-listening disposable address `mysql+pymysql://test:test@127.0.0.1:65535/marzban_test`. Tests in this checkpoint created only in-memory SQLite databases. No production/shared database was contacted.

Existing R07 focused regression:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_product_catalog.py tests/test_product_owner_lifecycle.py tests/test_admin_hierarchy_api_contract.py tests/test_stage4_plan_network_scope.py tests/test_monetary_billing_migration.py tests/test_admin_hierarchy_migration.py
```

Result: exit code `0`; `41 passed`.

R08.a RED suite:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_product_assignment_authorization.py
```

Result: exit code `1`; `11 failed`, `0 passed`, `0 skipped`. Failures are expected missing-contract evidence: the two Product access tables and three Product policy service functions do not exist at the R07 source SHA. No unrelated runtime assertion failed before those gates.

Additional checks:

- `python -m compileall -q tests/test_product_assignment_authorization.py`: passed.
- `git diff --check`: passed on the final staged diff.
- Initial test attempts without isolated environment overrides failed during collection on configuration (`SQLALCHEMY_DATABASE_URL` and host `DEBUG=release`); rerunning with explicit test-only values produced the results above. These were environment errors, not Product regressions.

## Boundary

R08 remains in progress. `R08.a = DONE_RED_TESTS`; R08.b and R08.c are not started. No application source, migration, dashboard, `main`, `VERSION`, tag, release workflow, deployment, or publication was changed. The next turn requires separate authorization for R08.b.
