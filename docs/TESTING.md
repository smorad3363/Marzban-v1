# Fresh Install / Current-Version Testing

Read the real `.github/workflows/` definitions for exact commands and matrix. Relevant CI: `checkpoints.yml` (both `mysql:8.0` and `mysql:26.7.0`, current migration and partial-DDL recovery, Stage 8-11, backup/restore, dashboard, Compose/installer/Node/mTLS); `dashboard-ui-contracts.yml` (UX, autofill, build, committed parity); `build.yml` (tag, source/image revision, GHCR and Release); `verify-v1-image.yml`; `validate-v1-installer.yml` (disposable fresh install).

Focus checks:
```bash
bash -n scripts/marzban.sh
bash tests/test_installer_v1_contract.sh
python -m pytest -q tests/test_release_contract.py tests/test_ci_matrix_contract.py tests/test_node_deployment_contract.py
cd app/dashboard && npm ci && node scripts/test-stage1-ui-contracts.cjs && node scripts/test-autofill-contract.cjs && VITE_BASE_API=/api/ npm run build
cd ../..
git diff --exit-code -- app/dashboard/build
```

Mandatory current-version behavior: empty MySQL schema to Alembic head, first Owner/bootstrap/login; new Admin and hierarchy scope; Plan separate from Access Group; current-version credit/usage/renewal/delete/financial history; backup+restore newly created data; Panel/Node mTLS, device policy and reconnect; current retry/idempotency/concurrency; backend authentication and Owner accounting secrecy.

Historical vNext->V1 conversion, old v4.8.0 application rollback and old MySQL upgrade-only rehearsal are outside required *fresh-install* qualification. Never remove the supported **two-MySQL-version matrix**, current migration chain, present business invariants or backup. Main-push matrix and PR-only packaging steps can be `skipped` despite workflow green. Mark PASS/SKIPPED/NOT RUN separately. The installer lab is destructive **on isolated disposable runner only**, never production.
