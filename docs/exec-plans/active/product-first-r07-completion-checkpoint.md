# Product-first R07 completion checkpoint

Date: 2026-09-19  
Branch: `docs/product-first-v3-1-r01-ledger`  
Pre-stage SHA: `4e2c946de9a93ad51c40131beec74a371f36b5aa`

## Outcome

R07.a through R07.d are complete on the isolated feature branch:

- R07.a added a Product-owned identity/network catalog with a positive traffic-price multiplier and no Plan quota, duration, device, node, or price fields.
- R07.b added Owner-only Product list/read/create/update endpoints, fail-closed Inbound/Host validation, API scopes, and audit events.
- R07.c added idempotent soft archive/restore. Archive retains the row and network scope for historical references; restore refuses invalid live network state.
- R07.d added the Owner Product editor, route and navigation, a static UI contract, and rebuilt committed dashboard assets. The form exposes only Product identity, multiplier, Inbound and Host fields.

Atomic implementation commits:

1. `7b21cf4` — `feat(product): add independent catalog schema`
2. `09f825d` — `feat(product): add owner catalog API`
3. `34f2f32` — `feat(product): add safe archive and restore`
4. `40c48dd` — `feat(product): add owner product editor`

## Fresh-install database decision

The user confirmed that this version will be installed from zero and that prior-version database data may be discarded. R07 therefore validates a disposable clean-database upgrade/downgrade/re-upgrade path and does not add a data-conversion dependency.

Legacy Plan and Access Group tables are not dropped in R07 because existing user, Trial, billing, and renewal runtime paths still reference them. Removing them now would make a clean installation fail at runtime. They may be removed only after those paths move to Product in later stages and a dedicated fresh-schema cleanup test proves no remaining references.

## Verification evidence

Backend command (isolated configuration; no production database):

```text
python -m pytest -q \
  tests/test_product_catalog.py \
  tests/test_product_owner_lifecycle.py \
  tests/test_admin_hierarchy_api_contract.py \
  tests/test_stage4_plan_network_scope.py \
  tests/test_monetary_billing_migration.py \
  tests/test_admin_hierarchy_migration.py
```

Result: `41 passed`. This includes the disposable SQLite file test for fresh Product migration, downgrade, and re-upgrade. MySQL service/container was not available locally; no production or shared database was contacted.

The full backend suite was also run: `467 passed, 9 skipped, 3 failed`. All three failures are existing Stage 5 legacy user-creation tests. Running only those same three tests in a detached worktree at pre-R07 SHA `4e2c946` produced the identical `3 failed`, proving they were not introduced by R07. Their failures are in legacy `used_traffic=None` subscription formatting and duration-preset expectations; they remain outside this stage rather than being hidden or counted as a pass.

Dashboard verification:

```text
npm run test:products       # passed
npm run test:access-groups  # passed
npm run build               # passed
```

The build emitted existing dependency `use client` notices and bundle-size warnings; neither failed compilation or bundling.

Closeout results:

- `git diff --check`: passed.
- `python -m compileall -q app tests`: passed.
- `alembic heads`: one head, `f7a3c9e1d205`.
- Database/container clients `docker`, `podman`, `mysql`, and `mysqld`: unavailable in this environment, so the MySQL matrix remains a later CI gate rather than a claimed pass.
- Exact branch: `docs/product-first-v3-1-r01-ledger`; expected uncommitted files before this checkpoint commit were only this checkpoint, the recovery ledger, the fresh-install instruction amendment, and the fresh-database migration test.
- Remote synchronization: not performed. The environment rejected the feature-branch push because the external GitHub destination was not explicitly authorized for source disclosure. Local commits are complete; remote branch still points to pre-R07 SHA `4e2c946`.

## Boundary and next action

- `main`, `VERSION`, tags, release workflows, deployment and publication remain untouched.
- R07 does not assign Products to Admins/users and does not implement traffic, allocated, or account-price calculation; those begin in R08/R09.
- Next exact task: R08.a Product-assignment and authorization tests.
