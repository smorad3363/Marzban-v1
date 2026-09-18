# Product-first R06.a — read-only fixed-month, time and timezone audit

Date: 2026-09-19. This is a **new stage checkpoint**, not a Product implementation or permission to start R07. Authoritative attached ZIP: `Marzban-Final-Product-v3.1-FINAL-2026-09-19(1).zip`, SHA-256 `d589677dedc4bf4e83d49414f211847356f20adb5aebc29c275a9794e9337879`, CRC OK; its `ROADMAP-fa.md` SHA-256 `bf58373dae3e43286bf6a44719adcce7145e3199de60e2ad41c24a374f621448` is the translation authority. Later explicit user decisions override old wording. Its B06 requires **one month = exactly 30 × 86400 elapsed seconds**, and B10 activation starts a new period at its *actual activation instant*, not booking time. Old purchased period records must not be rewritten. Read the complete handoff and the actual 1,113-line Library `Project Engineering Agent Contract — AGENTS(7).md` (not claimed to be committed). Active GitHub instructions `AGENTS.md` and newest [R05.a](product-first-r05a-instruction-checkpoint.md) were read; R05.a is DONE_DOCS_ONLY and the earlier checkpoints' current/next values are historical.

## Recovery (only ONE substep executed on this continue turn)

```yaml
project: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
verified_source_head: 533ca9dfcd878971cac93944a1654fa9eaafbecd
verified_main_head_before: 14e5c9032e5f94f783f34bde391bba318a6de925
stage: R06
stage_state: IN_PROGRESS_SPLIT_READ_ONLY
completed_substep: R06.a
substep_state: DONE_AUDIT_ONLY
next_exact_action: 'On the next separate user continue, execute ONLY R06.b: audit binary GiB/bytes, strict active-period <1 GiB refund boundary, unlimited quota and counter units against actual code/tests; record findings in a separate scoped GitHub checkpoint and stop. No R06.c or R07.'
product_implementation: NOT_STARTED
source_code_changed: false
migrations_changed: false
version_changed: false
main_changed: false
runtime_tests: NOT_RUN_READ_ONLY_NO_LOCAL_CHECKOUT
local_git_status: UNKNOWN_NO_LOCAL_CHECKOUT
other_machine_uncommitted_changes: UNKNOWN
user_test_confirmation: null
ci_final_sha_gate: NOT_VERIFIED
release_gate: LOCKED_IMPLEMENTATION
release_actions_performed: []
```

**Split decided before audit because R06 mixes independent units/network/finance/migration domains.** R06.a time/duration/timezone (this turn); R06.b byte/GiB and strict refund; R06.c Toman integer, price rounding, I=0/D/H/warning and delayed-usage guard; R06.d actual Host↔Inbound↔Node relationships and live network propagation; R06.e paid financial snapshot timing versus pending activation; R06.f one account/1-or-2 concurrent slots and distinct USER_CREDIT vs legacy SEAT_CREDIT; R06.g fully free Trial with preserved counters; R06.h Owner subtree freeze and Node acknowledgment semantics; R06.i clean install/forward migration and safe historic data. **All b–i are NOT_STARTED**, not findings, implementation or DONE. Complete R06 only after the remaining substeps have evidence; R07 is never part of this turn.

## R06.a: source-verified current behavior vs binding contract

| Inspectable source at pinned SHA | Verified behavior | Finding/required future test (not a code change now) |
|---|---|---|
| [`app/models/admin_hierarchy.py`](../../../app/models/admin_hierarchy.py) `PlanVersionInput`, `DurationPresetInput` | Legacy Plans and Owner duration presets carry positive *integer days* (`1..3650`); no calendar-month abstraction in these DTOs. | Product future month input must be mapped explicitly to 30/60/90/120/150/180 days for allocated purchases; USER_CREDIT 1/2/3/6 months becomes 30/60/90/180 days. Do not incorrectly treat the legacy 3650-day cap as the new USED_TRAFFIC business cap. |
| [`app/utils/admin_plans.py`](../../../app/utils/admin_plans.py) `_plan_user_payload`, `renew_user_from_plan` | Plan creation uses `datetime.now(timezone.utc)+timedelta(days=version.duration_days)` and saves integer Unix seconds; legacy immediate renewal extends `max(now_ts, user.expire)+version.duration_days*86400`. | These are day-based, not calendar months; they **do not implement** the new reserve-then-activate clock. New paid period must begin at actual activation (B10), use `N*30*86400` seconds and avoid extending historical expiry or recharging on activation. Preserve old immediate-renew historical records. |
| [`app/utils/owner_pricing.py`](../../../app/utils/owner_pricing.py) `duration_preset`, `duration_days_preset`, `form_price`, `adjustment_price` | Legacy form infers days using `round((expire-now)/86400)` and accepts up to **300 seconds** difference from rounded whole days; extension requires `%86400==0`. Monetary form pricing rounds **up** to whole Toman, but R06.a does not decide new money rounding (R06.c). | Do not copy `round` + 300-second tolerance into Product entitlement/duration boundary. Test exact elapsed seconds around 30/31, 60/61, 150/180 days and the instant before/at expiry; evaluate quote/activation clock once rather than letting small wall-clock skew select a different duration tier. Legacy form tolerance stays unchanged by this read-only audit. |
| [`app/jobs/reset_user_data_usage.py`](../../../app/jobs/reset_user_data_usage.py) | The **legacy usage-reset** map explicitly defines `month: 30 days`; scheduler is hourly and condition is `(now-last_reset_time).days >= 30`. | Existing *quota reset cadence* is not evidence of new *purchased period expiry*. Hourly execution can occur later than exact elapsed expiry; new entitlement must use timestamp boundary and not equate traffic reset with subscription renewal. Preserve legacy reset history. |
| [`app/jobs/review_users.py`](../../../app/jobs/review_users.py) | Legacy periodic expiry checks `now=datetime.utcnow()` then `now_ts=now.timestamp()`; `start_user_expire` in [`app/db/crud.py`](../../../app/db/crud.py) likewise does `datetime.utcnow().timestamp()`. Review's on-hold datetime conversions use `datetime.timestamp(...)`. | **Timezone hazard:** `utcnow()` is naive and Python `.timestamp()` interprets a naive value in the host's local timezone. The observed source can offset expiry checks/on-hold activation when runtime timezone is non-UTC. Actual deployed TZ and observable impact are UNKNOWN, not claimed reproduced. Future tests must set non-UTC TZ and cover UTC-aware instant round-trip, midnight/day rollover, DST and on-hold start; narrow fixes to Product paths and directly affected shared helpers, preserving historical expiry fields. |
| [`app/utils/helpers.py`](../../../app/utils/helpers.py) `calculate_expiration_days` | Computes `(datetime.fromtimestamp(expire)-datetime.utcnow()).days`, mixing local naive time with UTC naive time and floor-day calculation. | Notification remaining-day values can disagree with true UTC expiry in non-UTC hosts; do not use this as Product's authoritative period clock. Record boundary tests separately from UI display. |
| [`app/dashboard/src/components/CreateUserFromPlan.tsx`](../../../app/dashboard/src/components/CreateUserFromPlan.tsx), [`tests/test_stage4_plan_network_scope.py`](../../../tests/test_stage4_plan_network_scope.py) | Legacy UI displays `duration_days` as days and existing Plan-network test constructs an example with `duration_days=30`. | A 30-day fixture is not a test of all Product 30-day month boundaries, pending activation or timezone. Targeted *new* regression tests must cover 30/31/60/61/150/180, exact expiry, on-hold and accepted pending activated after archive; not run in this doc-only substep. |

**Not yet inspected in this substep:** other R06 unit, money, networking, account-slot, Trial, freeze, actual production DB and clean-install/migration semantics. R03/R04/R05 findings are recovery pointers, not repeated audits. No inference is made that actual runtime TZ is non-UTC, or that all historical timestamps have one representation. There is no new business decision to ask: 30-day month, paid snapshots and live Product network are fixed by the user. Future work should store UTC instants explicitly, distinguish elapsed purchased duration from calendar display, and not backfill or reinterpret old purchases without an approved data-compatible migration.

## Write intent, verification scope, risk and stop

Before the GitHub write, documented intent at `/mnt/data/marzban_r06_work/R06a-intent.md`, SHA-256 `27073a27c7c6b1dc8ab2906155eef0baaa73b0437e4e5e638b4cb58173a1ae61`: create only **this one new document** on the existing safe docs branch, never overwrite earlier checkpoints; follow with readback, diff/changed paths and exact postwrite SHA checks. No local repository checkout (`git -C /mnt/data status --short` reports `not a git repository`); therefore no claim of clean worktree, local `git diff --check`, local unit-test pass, or other-machine status. Inspect GitHub commit diff rather than substituting claims about a nonexistent local checkout. This is source examination, **not an executed behavior test**. The release workflow is tag push / explicit workflow_dispatch triggered, not a push to this docs branch (inspected `.github/workflows/build.yml`); no tag or dispatch will be performed. CI check-runs and commit status on the resulting **new exact SHA** must be observed and described honestly, `NO_CHECKS` not PASS. Next action is precisely R06.b on a **separate** `ادامه بده`; halt here.
