# Product-first R06.g — read-only genuinely free Trial and actual-usage exclusion audit

Date: 2026-09-19. Source of truth: supplied FINAL v3.1 Persian `ROADMAP-fa.md` B02/B03/B07/B09/B13/B17–B19 and R06/R22–R23/R40–R43. Earlier [R06.f USER_CREDIT](product-first-r06f-user-credit-device-checkpoint.md) separately committed/verified. This is third of the five explicitly authorized read-only substeps; neither a test result nor Product implementation.

```yaml
repo: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
source_sha_inspected: 1f9396c05a57032e61e273116e97f5ad10e6e2dd
stage: R06
stage_state: IN_PROGRESS_SPLIT_READ_ONLY
completed_substeps: [R06.a, R06.b, R06.c, R06.d, R06.e, R06.f, R06.g]
completed_this_commit: R06.g
next_exact_action_in_current_five_substep_request: 'After verifying R06.g file, one-doc diff, branch and CI, audit ONLY R06.h: distinct automatic Admin emergency vs explicit Owner subtree freeze/restore, ownership and per-Node result; separate checkpoint/verification.'
remaining_substeps: [R06.h, R06.i]
product_implementation: NOT_STARTED
runtime_tests: NOT_RUN_SOURCE_INSPECTION_ONLY
local_worktree_or_external_uncommitted_state: UNKNOWN_NO_LOCAL_CHECKOUT
ci_gate: NOT_VERIFIED
release_gate: LOCKED_IMPLEMENTATION
```

## Contract boundary

New Product Trial is precisely one account, 1 binary GiB, one 24-hour day, a selected currently ACTIVE/authorized Product and own independent Trial quota (default five per Admin; Owner configurable). This exception overrides normal paid mode volume/duration/fixed-price choices. **Fully free in all three modes**: create and any applicable reservation: zero Toman and no legacy byte/device balance debit; USER_CREDIT does not charge its fixed price; USED_TRAFFIC must still record actual test bytes for its 1-GiB cutoff, reporting and abuse signals **but exempt these bytes from every monetary settlement and upstream reseller usage charge**. A later paid period must start with paid rate and its own watermark, not inherit free classification. Trial deletion does not automatically restore quota; replay consumes at most one entitlement. No name/notes heuristic may classify Trial.

## Source-grounded findings: prior V1 trial is not Product B13

| Pinned source | Observed behavior | Gap / priority |
|---|---|---|
| [`app/db/models.py`](../../../app/db/models.py), [`app/utils/admin_plans.py`](../../../app/utils/admin_plans.py) | Legacy `AdminUserPlan.is_trial` and immutable `UserPlanAssignment.is_trial` are first-class metadata. `create_user_from_plan` atomically decrements `MarzhelpAdminSettings.trial_quota` via conditional UPDATE and records assignment; `money_billing.charge_plan_purchase` bypasses upfront Plan money if `plan.is_trial`. It still requires legacy Plan plus separately selected Access Group and takes the Plan version's requested quota/days/device, with no generic enforced **new Product** 1-GiB/1-day form. | Reuse metadata/quota/idempotency, but new Product Trial must validate exact shape, new selection permissions and no charge/second-wallet debit across modes. Trial being free at **Plan creation** does NOT establish free USED_TRAFFIC bytes. |
| [`app/jobs/record_usages.py`](../../../app/jobs/record_usages.py), [`app/utils/money_billing.py`](../../../app/utils/money_billing.py) | Usage worker reads Xray stats with reset, aggregates User bytes to `admin_usage: dict[admin_id, bytes]`, increases User.used_traffic and Admin.users_usage, then calls `settle_used_traffic(db, admin_usage)`. Settlement filters only Admin mode `USED_TRAFFIC` + money billing, then charges all aggregated bytes at Admin's current GiB rate (and eligible upstream chain); **no User ID, Trial assignment, Product period or trial-free flag is carried into the settlement function**. | Concrete uncovered billing path: real trial bytes from a monetized USED_TRAFFIC Admin are not distinguishable at charge time; cannot claim B13 monetary-free consumption. R22 must add a failing test and R23 preserve per-User/period trial flag in durable sample attribution and exclude trial bytes from money while retaining usage. Do not suppress actual byte accounting. |
| [`app/utils/trials.py`](../../../app/utils/trials.py) | Owner trial grant/reclaim and authorized quota reset use separate `trial_quota` resource ledger with idempotency. Cleanup selects by `UserPlanAssignment.is_trial` and expiry and preserves deleted-usage snapshot; no name matching. | Cleanup/deletion must not refund quota silently. Product-period Trial status needs durable history after subsequent paid conversion, so current Trial's usage cannot be misclassified/rebilled retroactively. |
| [`tests/test_stage6_trials.py`](../../../tests/test_stage6_trials.py) | Existing source parameterizes Plan Trials with `(1GiB,1)`, `(2GiB,1)`, `(unlimited,1/2)` and one-day, checks quota decrement/replay and metadata cleanup. Its modes/shapes are legacy-compatible, **not** proof that new Product Trial is fixed to exactly 1 GiB or that USED_TRAFFIC bytes are free. A MySQL test is conditional on `TEST_MYSQL_DATABASE_URL`. These tests were only READ. | Add R40/R43 all-three-mode tests: `1GiB/1day`, quota default=5/grant/exhaust/replay, invalid Product/archive/mode, zero ledger at create/reserve, USED sample of `GiB-1`, `GiB`, multi-node and late sample bills zero with byte counter preserved, upstream zero, conversion to paid period bills only post-conversion bytes, delete does not refund quota. |

**No invented success:** no runtime tests, actual Xray sampling, DB values or successful Product-free implementation verified. Preserve V1 legacy Trial shapes/tests and historical accounting while adding separate Product behavior later; prevent a broad global settlement change that makes non-Trial traffic free. Verify only this new doc's commit/readback/diff and exact-SHA check state. No R07, code, migrations, VERSION, main, PR, release, workflow dispatch, tag or deployment; release LOCKED.