# Product-first R06.b — read-only binary GiB, refund boundary and byte counters

Date: 2026-09-19. Contract: user-supplied FINAL v3.1 ZIP, Persian `ROADMAP-fa.md` controlling, especially B05/B07–B13, B17, R06 and R34–R35, plus the latest explicit user decisions. The previous authoritative [R06.a checkpoint](product-first-r06a-time-semantics-checkpoint.md) is complete; [R05.a](product-first-r05a-instruction-checkpoint.md) resolved instruction scope. This checkpoint records ONLY R06.b, not Product implementation, a test result, completion of all R06, or authorization to start R07. Earlier ledger `current_step` fields are historical.

## Recovery state and one-substep boundary

```yaml
project: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
source_sha_inspected: 0e04a7fd64f4ebd1a38ec1ee2711aedb248efd21
main_sha_verified_before: 14e5c9032e5f94f783f34bde391bba318a6de925
stage: R06
stage_state: IN_PROGRESS_SPLIT_READ_ONLY
completed_substeps: [R06.a, R06.b]
completed_this_turn: R06.b
substep_state: DONE_AUDIT_ONLY
next_exact_action: 'On the next separate user continue, reverify actual GitHub HEAD and this R06.b checkpoint, then execute ONLY R06.c: audit integer Toman, rounding of prices and immutable I including I=0, default D=floor(5% I), hard H=floor(15% I), warning at <=10% I, spending/late-usage guard; record only that audit in a new scoped GitHub checkpoint, verify its exact SHA and stop. Do not start R06.d or R07.'
product_implementation: NOT_STARTED
source_code_changed: false
migrations_changed: false
version_changed: false
main_changed: false
runtime_tests: NOT_RUN_SOURCE_INSPECTION_ONLY
local_worktree_status: UNKNOWN_NO_LOCAL_CHECKOUT
other_machine_uncommitted_changes: UNKNOWN
final_sha_ci_gate: NOT_VERIFIED
user_test_confirmation: null
release_gate: LOCKED_IMPLEMENTATION
release_actions_performed: []
```

R06.a covers time; this substep covers ONLY unit/byte/refund semantics. R06.c–R06.i remain NOT_STARTED. Do not mark all R06 DONE on the strength of this checkpoint. No new business question is required.

## Binding exact units and boundary

- `GIB = 1024 ** 3 = 1,073,741,824` **bytes**, not 10^9 and not a rounded human-visible GiB. Contract B12 for deleting the current active paid period: USED_TRAFFIC settles final actual usage and **never refunds**; ALLOCATED_TRAFFIC and USER_CREDIT refund **only the actual Toman paid for that active period, once** when `current_active_period_used_bytes < GIB`. Exactly 1 GiB and above yield no automatic refund; optional Owner review is distinct. Pending reservations must be cancelled/refunded separately **before** active-period delete, with distinct idempotent ledger events. `lifetime_used_traffic`, Admin usage totals, plan allocation and UI-rounded GiB must not stand in for the active-period byte counter.
- Deterministic future tests: `used=0` => eligible; `GIB-1=1,073,741,823` => eligible; `GIB=1,073,741,824` => NOT eligible; `GIB+1` => NOT eligible; USED_TRAFFIC => never refund at every boundary. Also test a prior period with >1 GiB followed by an active period with 0 bytes, the reverse, quota reset/renewal, late in-flight samples, delete race, pending+active separate refund, a replay and two concurrent requests. All such *new Product* tests are NOT_RUN / NOT_YET_IMPLEMENTED.
- B07 permits USED_TRAFFIC **arbitrary positive GiB or unlimited**, with positive days and no upfront byte-wallet charge. B08 fixes ALLOCATED_TRAFFIC package choices to **20/30/50/100 GiB**; byte quota is per User and must never be deducted from a second Admin byte wallet. New API must validate selected amounts and convert positive integer GiB to exact integer bytes once, checking overflow/DB BigInteger range and rejecting NaN, fractional/truncated and disallowed choices. USER_CREDIT is the distinct one-account fixed-price mode; monetary and slot mapping are separately audited under R06.c/R06.f. Trial's 1 GiB quota is an exception to paid packages; complete monetary-free Trial audit is reserved for R06.g.

## Observed existing source at the pinned SHA (NOT a claim Product behavior exists)

| Source | Actual inspected behavior | Product boundary / risk |
|---|---|---|
| [`app/utils/money_billing.py`](../../../app/utils/money_billing.py), [`app/utils/owner_pricing.py`](../../../app/utils/owner_pricing.py) | Both define binary `GIB = 1024 ** 3`. Existing USED_TRAFFIC settlement takes aggregated Admin byte counts, calculates `(remainder + bytes * current_admin_price) divmod GIB` and carries fractional Toman remainder; legacy form quotes use binary GiB too. | Reuse integer binary units, but do not equate these legacy Admin-aggregate rates/rounding with Product-specific immutable per-User/period snapshots or conclude new refund is implemented. Detailed price rounding/I/D/H belongs R06.c. |
| [`app/models/user.py`](../../../app/models/user.py), [`app/utils/marzhelp_policy.py`](../../../app/utils/marzhelp_policy.py), [`app/db/models.py`](../../../app/db/models.py) | `User.data_limit`/`used_traffic`, `UserUsageResetLogs.used_traffic_at_reset`, `NodeUserUsage.used_traffic`, plan quota and legacy refund snapshot values use integer/BigInteger byte-like counters. `_effective_data_limit(None or 0)` means unlimited; `subscription_mode_for` distinguishes finite and unlimited. Pydantic `data_limit` pre-validator accepts float and truncates with `int(v)` in existing raw User input. | New Product endpoints must not accidentally accept fractional GiB converted/truncated to another quantity. Preserve legacy nullable/zero unlimited semantics where required, but distinguish unlimited from zero **usage**, zero initial funding and empty/invalid package; require per-period immutable byte accounting. BigInteger alone does not prove no overflow in product multiplication. |
| [`app/db/models.py`](../../../app/db/models.py) `User.lifetime_used_traffic` and [`app/utils/marzhelp_policy.py`](../../../app/utils/marzhelp_policy.py) summaries | Lifetime = accumulated `UserUsageResetLogs.used_traffic_at_reset` + current `User.used_traffic`; summaries combine current/reset/deleted bytes, but polymorphic `credit_used` means bytes for ALLOCATED/USED, account count for USER_CREDIT and device credits for SEAT_CREDIT. | Refund gate needs a **durable current Product period's** actual bytes; lifetime, `credit_used`, wallet Toman and quota must not be interchanged. Preserve all old history and metric interpretation. |
| [`app/jobs/record_usages.py`](../../../app/jobs/record_usages.py), [`app/db/models.py`](../../../app/db/models.py) `Node.usage_coefficient` | Xray user stats are read with `reset=True`, combined by user across Nodes; each Node sample is `int(raw_value * coefficient)` then added to User/Admin, while optional hourly NodeUserUsage persistence uses `raw_value * coefficient` in SQL. Node coefficient is Float, and optional node history is written **after** monetary/user DB commit. | Fractional coefficients may create counter reconciliation/rounding risks; actual mismatch is **not proven**. Reconcile canonical byte definition across quota, per-User charged usage, per-period refund and Node telemetry with targeted tests. `reset=True` before durable DB commit risks lost samples; a post-reset crash can make a refund decision unsafe without a final usage barrier/watermark. Recovery and dedup design belongs R22/R23 and refund implementation R34/R35, not this audit. No exact real-time byte cutoff claimed. |
| [`app/utils/billing_service.py`](../../../app/utils/billing_service.py), [`app/utils/marzhelp_policy.py`](../../../app/utils/marzhelp_policy.py) | Legacy `create_refund_request` ALLOCATED-only captures `remaining=max(quota-used,0)` and checks requested refund **bytes** against remaining; approval decreases `MarzhelpAdminSettings.used_traffic` bytes and creates `AdminCreditTransfer(resource='allocated_refund')`. `calculate_delete_refund` returns 0. No strict `< GIB` or paid Toman return in **these inspected paths**. | Existing byte-credit refund is **NOT** the new automatic Product Toman refund; do not reuse its ledger, remaining-quota formula or role policy as if they satisfy B12. USER_CREDIT Product refund also needs a new once-only paid amount record, not an implicit legacy SEAT_CREDIT refund. Preserve legacy workflows/rows. |
| [`tests/test_stage3_billing_modes.py`](../../../tests/test_stage3_billing_modes.py), [`tests/test_stage3_usage_collection.py`](../../../tests/test_stage3_usage_collection.py), [`tests/test_stage2_resource_ledger.py`](../../../tests/test_stage2_resource_ledger.py) | Existing test **source** checks byte-credit refund of 30 units, no refund on legacy delete, multi-Node sums/coefficients with integer multipliers, and GIB-sized old byte-credit transfers. | These are source inventory, NOT executed tests and not Product B12 threshold, fractional Node-factor reconciliation, current-period isolation, or one-wallet monetary refund proof. MySQL concurrency test in billing modes is conditional on TEST_MYSQL_DATABASE_URL; not executed here. |

## Verifiable future acceptance and stop

New R34 boundary tests must first expose the absent Product current-period/paid-Toman semantics; R35 then implements the limited once-only refund, with a final settled usage barrier and separate pending reservation cancellation (R30–R32). Per-User sample/period recovery and canonical byte attribution are R22/R23 prerequisites. No old purchased history may be recomputed, no legacy byte balances converted/destroyed without a safe migration. Unit conversions, test names, snapshot evidence and blocking risks are documented; no runtime or live database was inspected.

**Write/verification plan:** create only this new markdown checkpoint on the named docs branch after comparing its HEAD with the pinned source SHA. Read it back; inspect its GitHub diff against the source SHA, branch HEAD and exact resulting SHA check-runs/combined status. The environment lacks a local repository checkout (`git -C /mnt/data status --short` reported `not a git repository`), so do not claim local clean, local diff check, CI PASS or remote uncommitted-state inspection. No code, migration, VERSION, PR, merge, tag, GitHub Release, deployment or workflow dispatch. Release remains `LOCKED_IMPLEMENTATION`; next separate `ادامه بده` is R06.c ONLY.
