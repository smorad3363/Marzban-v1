# Product-first R06.i — read-only real-data, install/upgrade and safe-migration gate

Date: 2026-09-19. Authority: user-supplied FINAL v3.1 ZIP, Persian `ROADMAP-fa.md` controlling, particularly B14–B17/R06/R07 and release gates. User explicitly requested **five sequential R06.e–R06.i audit substeps in this turn**; previous independent checkpoints [e](product-first-r06e-period-reservation-snapshot-checkpoint.md), [f](product-first-r06f-user-credit-device-checkpoint.md), [g](product-first-r06g-trial-free-usage-checkpoint.md), [h](product-first-r06h-owner-freeze-restore-checkpoint.md) were written and each read back with a one-doc commit comparison, exact HEAD and absent check-runs. This fifth checkpoint only audits R06.i; no Product implementation/R07 or destructive operation is authorized.

## Current recovery status and next exact action

```yaml
repo: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
source_sha_inspected: f63bdb9895c13c5067e18d776eadd0de5ad22995
main_sha_last_verified_prior_turn: 14e5c9032e5f94f783f34bde391bba318a6de925
stage: R06
stage_state: DONE_AUDIT_ONLY_WITH_IMPLEMENTATION_GAPS
completed_substeps: [R06.a, R06.b, R06.c, R06.d, R06.e, R06.f, R06.g, R06.h, R06.i]
completed_this_commit: R06.i
remaining_R06_substeps: []
R07: NOT_STARTED
next_exact_action: 'STOP after verifying this R06.i commit, its full readback, one-doc diff, GitHub branch/main HEAD and exact-SHA checks. On NEXT separate user continue ONLY R07.a: reverify newest checkpoint/branch, secure actual local checkout and dirty-state/diff before source edits, write failing focused Product schema/model tests then minimal additive Product migration/model; if no local checkout or test/migration verification is possible, mark R07.a BLOCKED with exact recovery step, do not fabricate implementation or test PASS. R07.b and any other stages are NOT authorized by this turn.'
product_implementation: NOT_STARTED
code_changed: false
migration_changed: false
version_changed: false
runtime_tests: NOT_RUN_READ_ONLY_AUDIT
clean_install_test: NOT_RUN
upgrade_test: NOT_RUN
rollback_or_restart_test: NOT_RUN
live_database_connected: false
live_database_population: UNKNOWN_NOT_INSPECTED
installed_instance_and_alembic_version: UNKNOWN_NOT_INSPECTED
local_git_status_or_worktree: UNKNOWN_NO_LOCAL_CHECKOUT
other_machine_uncommitted_state: UNKNOWN
exact_sha_ci: NOT_VERIFIED_NO_CHECKS
user_successful_test_confirmation: null
release_gate: LOCKED_IMPLEMENTATION
release_actions_performed: []
```

**B15's statement that the panel has not been practically used is a user report, not database evidence.** There is no live DB/installed-instance connector or local repo checkout in this audit. No connection was made to production, no Alembic `current`, `heads`, `upgrade`, `downgrade`, MySQL query, destructive cleanup, restart or installer execution occurred. It is therefore **UNKNOWN**, not 'empty', whether any installed database has Users, Plans, Access Groups, wallets, ledgers, trials or an older schema revision. Treat lack of that proof as an explicit blocker for *destructive* migration/deletion, not an excuse to abandon additive design.

## Pinned actual code, migration and test evidence

| Inspected file | Source-grounded observation | Safety consequence |
|---|---|---|
| [`alembic.ini`](../../../alembic.ini), [`app/db/migrations/env.py`](../../../app/db/migrations/env.py), [`versions/`](../../../app/db/migrations/versions/) | Config points `script_location` at `app/db/migrations`. Environment configures online DB engine from app `SQLALCHEMY_DATABASE_URL` and `Base.metadata`, offline SQL mode, and runs migrations. GitHub's pinned migrations directory/tree exists and contains many historical versions, including monetary and Trial additions. This is **source inventory**, not proof the migration DAG is executable, that a particular installed revision equals code head, or that a target DB is empty. | Before any actual forward migration, inspect actual installed `alembic_version`/backend, ensure unique intended head and valid `down_revision` path in a disposable database, review dialect and existing data counts with authorized read-only access; record backup/checksum/restore readiness. Avoid printing DB URL/secrets in logs or checkpoint. |
| [`c2f4a8d6e913_add_monetary_reseller_billing.py`](../../../app/db/migrations/versions/c2f4a8d6e913_add_monetary_reseller_billing.py) | `revision=c2f4a8d6e913`, `down_revision=8b7d3e5f1a24`; upgrade conditionally ADDs four money settings columns and Plan price, and CREATEs separate reseller prices and Admin money-transaction table/indexes. It does not define new Product/I/D/H/paid-period/reservation fields. **Its downgrade unconditionally drops `admin_money_transactions`, `admin_user_plan_prices` and monetary columns when present**, potentially destroying data if applied to a live populated DB. | Make R07/R09/R24 changes additive, preserve ledger and Plan rows. Never run old downgrade on live data as an assumed safe rollback. Define application rollback/forward-repair plan and backup validation, distinguish schema rollback from non-destructive code revert. Do not alter or fabricate historical baseline migration. |
| [`5b8d1f3a7c64_add_trial_system.py`](../../../app/db/migrations/versions/5b8d1f3a7c64_add_trial_system.py) | Trial upgrade conditionally adds Plan/assignment flags, quota columns and cleanup table, with `down_revision=3a7e5c1b8d42`; its downgrade drops Trial table and flags. Older Plan/Trial tables retain historical purpose. | New Product must use new additive IDs/tables and keep legacy Plan/Access Group/Trial history readable. Removing Plan from **new UI and purchasing** does not authorize `DROP TABLE`, reassigning historical paid amounts or revoking existing service. |
| [`tests/test_monetary_billing_migration.py`](../../../tests/test_monetary_billing_migration.py) | Monetary tests check source tokens, linkage to one `down_revision`, metadata indexes/constraints; they are **not** an executed clean-install/upgrade/rollback test or complete chain validation. | Do not label presence of test source `PASS`; add/run isolated clean DB install and populated prior-revision upgrade tests for each new migration, checking old row counts/foreign keys, idempotent migrations if designed, defaults and nullability, old ledger balances, and new Product identity. |
| [`tests/test_stage6_trials.py`](../../../tests/test_stage6_trials.py) | Optional MySQL test is guarded by `TEST_MYSQL_DATABASE_URL`, asserts database name ends in `marzban_test`, then **drops every table in that selected test database** before upgrading from an older revision to `head` and checking preserved seeded Plan/admin values. It was READ as source and NOT RUN here. | This is intentionally destructive even though test-scoped; NEVER point it at an installed/live DB. Require confirmed disposable target and backup policy; execute only in appropriately isolated future test stage. No current full Product migration test exists in the inspected sources. |
| [`app/db/models.py`](../../../app/db/models.py), [R06.e](product-first-r06e-period-reservation-snapshot-checkpoint.md), [R06.c](product-first-r06c-money-debt-checkpoint.md) | Existing `AdminMoneyTransaction`, Plan/Access Group, `UserPlanAssignment` and `NextPlan` hold legacy records; inspected model/migration surfaces lack new immutable Product financial snapshots, `I/D/H`, and Product pending state. No real row contents were queried. | Preserve historical FKs/data and admin money ledger, add new tables/columns only when their read/write semantics and testable migration are ready; never guess initial funding from a balance or retrospectively charge/reprice. Maintain safe old installer/release protections. |

## Non-destructive future migration acceptance (NOT executed)

- Test both **fresh** schema installation and **populated prior-revision -> new head upgrade** in isolated SQLite/MySQL as appropriate; verify old Users/Plan/Access Group/ledger balances, trial and Admin rows remain identical, correct FK/index, nullable/default columns and UUID/key uniqueness; simulate migration interruption and application restart/retry. Account for online DDL/MySQL transaction limitations and backup before attempting live DDL.
- Inspect actual installed DB version, record non-sensitive table/row counts, resolve migration heads and compare data before/after, produce an authorized backup and verified restore rehearsal. Do not execute on production merely because user says panel unused. For unexpected existing Product ID collision/missing reference, fail safely and report BLOCKED rather than overwriting. Rollback must not drop money transactions or period history; use proven app rollback/forward migration, with separate permission for any true destructive schema/data removal.
- R07.a is the next **separately user-authorized step**, with independent one-topic schema/model tests and migration. R07.b–d follow only later one at a time. R06 audited semantics are documented, NOT Product acceptance: real-data proof, tests, no-check CI and implementation are outstanding gates. No VERSION/main changes, code, migration, PR, merge, release, tag, deployment or workflow dispatch in these five read-only audits.

**Post-write verification plan:** read this GitHub checkpoint at the returned SHA, compare its direct parent `f63bdb9895c13c5067e18d776eadd0de5ad22995`, verify branch/main SHA, inspect exact-SHA check-runs/status, and compare starting `682f5be665e5874e9ca9535c84ca1cc73b79a6d4` to resulting HEAD for exactly five new markdown docs. STOP, release stays locked.