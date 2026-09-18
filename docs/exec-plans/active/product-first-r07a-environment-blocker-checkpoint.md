# Product-first R07.a — blocked implementation preflight and exact recovery

Date: 2026-09-19. Authority: user-supplied FINAL v3.1 ZIP, controlling Persian `ROADMAP-fa.md` §§0/A/E R07, repository [`AGENTS.md`](../../../AGENTS.md) amended for new Product flows, and previous [R06.i](product-first-r06i-data-migration-gate-checkpoint.md). The user explicitly requested **the entirety of R07** in this turn. The implementation preflight for its FIRST prerequisite R07.a found a real verification blocker; this checkpoint records the incomplete state honestly instead of claiming Product CRUD, migration or tests were done. No source code was changed.

## Live checkpoint

```yaml
repository: smorad3363/Marzban-v1
safe_branch: docs/product-first-v3-1-r01-ledger
verified_parent_head_before: 2e97c9e51fc00c84067d7999b1f5814d5473a747
stage: R07
stage_state: BLOCKED_ENV_NOT_DONE
R07.a: BLOCKED_NO_VERIFIABLE_LOCAL_CHECKOUT
R07.b: NOT_STARTED_DEPENDS_ON_R07.a
R07.c: NOT_STARTED_DEPENDS_ON_R07.a_AND_R07.b
R07.d: NOT_STARTED_DEPENDS_ON_R07.a_AND_R07.b
R08: NOT_STARTED
R09: NOT_STARTED
product_implementation: NOT_STARTED
source_code_changed: false
migrations_changed: false
version_changed: false
runtime_tests: NOT_RUN_NO_CHECKOUT
fresh_schema_install: NOT_RUN
populated_upgrade: NOT_RUN
working_tree_status: UNKNOWN_NO_LOCAL_REPO
other_machine_uncommitted_changes: UNKNOWN
installed_database_population: UNKNOWN_NOT_CONNECTED
final_sha_ci: NOT_VERIFIED
user_test_confirmation: null
release_gate: LOCKED_IMPLEMENTATION
release_actions: []
next_exact_action: 'Recover an actual complete local checkout of smorad3363/Marzban-v1 on docs/product-first-v3-1-r01-ledger, after Git network/DNS works or a trustworthy complete repository checkout is mounted. Reverify its HEAD against current GitHub branch and this checkpoint, inspect git status --short, git diff --stat, git diff and local intents; preserve all uncommitted work. Then perform R07.a ONLY with scoped failing Product schema/model tests, minimal additive Product identity/Owner+network mapping/model migration, focused tests and isolated fresh/seeded-upgrade verification; commit/push only when test and diff evidence permits. If blocked again, update checkpoint accurately. After VERIFIED DONE R07.a, R07.b/c/d can be tackled separately in dependency order under the user’s original full-R07 authorization; do not skip R07.a or mark R07 DONE. Never touch R08, main, VERSION, release or live DB in this recovery.'
```

## Actual diagnostics and source evidence

- GitHub connector independently read the exact branch `HEAD=2e97c9e51fc00c84067d7999b1f5814d5473a747` and full R06.i checkpoint at that ref, then rechecked the branch before writing this new file. R06.i marked Product unimplemented, real data and installed Alembic revision uninspected, no runtime tests and CI no-checks.
- Candidate workspace discovery in the accessible container (`/workspace`, `/workspaces`, `/repo`, `/app`, `/home/oai/share`, `/home/oai/work`, `/mnt/data`, `/tmp`, depth ≤4) found **no Git checkout**. The supplied ZIP contains only seven Product specification files, not source checkout. Attempted `git ls-remote https://github.com/smorad3363/Marzban-v1.git refs/heads/docs/product-first-v3-1-r01-ledger` fails `Could not resolve host: github.com`. GitHub connector reads/writes do work but provide no trustworthy checked-out full tree, `git status`/diff or executable application environment. Installed `pytest`, SQLAlchemy and Alembic binaries alone do not make tests runnable against absent source. This is an environment blocker, not a claimed source bug or permissions refusal.
- [Current `app/db/models.py`](../../../app/db/models.py) lines inspected around old Plan/AccessGroup/Assignment: `AdminUserPlan` owns historical quota/term/price via `AdminUserPlanVersion`; `AccessGroup` and independent `AccessGroupInbound`/`AccessGroupHost`/`AccessGroupNode` exist; `UserPlanAssignment` is historical. No new Product table in this targeted model section. Do not infer a safe new Product→Node relationship from Host IDs or reuse legacy public permissions. Detailed R06.c/d/e checkpoints record monetary snapshots and live-network/fail-closed constraints.
- [`AGENTS.md`](../../../AGENTS.md) expressly authorizes Product-first **new flows** while preserving old Plan/Access Group and migration history, requires targeted delta, status/diff, focused tests and forward migrations. R07 demands Owner-only CRUD, name and Inbound/Host selection, multiplier default 1 and positive, safe archive/restore and referenced hard-delete protection, no quota/duration/base price on Product. R07.a schema/model and tests precede R07.b Owner operations, R07.c archival, R07.d stripping legacy Plan commercial fields from **new** Product editor/path only. R08 permission distribution and R09 detailed pricing remain separate later stages.

## Recovery acceptance boundary, not asserted PASS

1. Pin verified working branch SHA; preserve existing user changes; write local pre-patch intent with target file hash and expected failing test; no blind entire-file overwrite. If repository is mounted with uncommitted work, reconcile first and never `reset --hard`/`clean -fd`.
2. R07.a tests first: Product identity vs old Plan, owner FK, immutable stable Product ID, uniqueness rules, default positive multiplier 1 and no Product fields for traffic quota, duration, base price or eight fixed prices; explicit Inbound/Host rows with constrained identity and fail-closed invalid topology; no accidental group-wide/Node unrestricted fallback. Add the smallest non-destructive model/migration, retaining all legacy rows. Defer Owner CRUD to R07.b, lifecycle service to R07.c, new-UI commercial isolation to R07.d and Admin mode-specific grants and pricing to R08/R09.
3. In disposable databases, actually run relevant pytest, `alembic heads`, clean-install and seeded old-head→new-head upgrade; verify original Plan, users, Access Groups, money/Trial rows and balances survive; prove constraints/indexes. Do not run historical destructive downgrade or MySQL tests pointed at an installed DB. Record actual PASS/FAIL/SKIP with commands and hashes. An absent check-run is `NO_CHECKS`, **never PASS**.
4. Stage R07 may only be `DONE` when independently tested R07.a/b/c/d and full acceptance pass; release still locked until all other roadmap stages, final SHA CI and user testing with separate release order.

**Stop after this blocker checkpoint:** Read back its exact returned commit, compare with its single parent for this single documentation addition, verify GitHub branch/main HEAD and check-runs/status. No source patch, migration, database access, tests, VERSION, main, workflow dispatch, PR, merge, tag, release or deployment is claimed or performed.