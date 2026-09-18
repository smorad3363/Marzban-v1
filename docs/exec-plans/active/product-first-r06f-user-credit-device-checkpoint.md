# Product-first R06.f — read-only USER_CREDIT / 1–2 concurrent-device semantics audit

Date: 2026-09-19. Authority: FINAL v3.1 Persian `ROADMAP-fa.md` B04/B09/B14/B17, R06/R09.i/R16–R18 and the user's **already final** business decision: one User account with one or two simultaneous device connections; do not ask again. Prior [R06.e](product-first-r06e-period-reservation-snapshot-checkpoint.md) read back, single-doc diff and branch HEAD verified; no CI check reported. This second of five requested substeps covers R06.f only.

```yaml
repo: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
source_sha_inspected: 7b9f890b53be56b5d9a93c8d46b37be637b80b6e
stage: R06
stage_state: IN_PROGRESS_SPLIT_READ_ONLY
completed_substeps: [R06.a, R06.b, R06.c, R06.d, R06.e, R06.f]
completed_this_commit: R06.f
next_exact_action_in_current_five_substep_request: 'Verify this file/diff/HEAD/CI, then R06.g ONLY: audit genuinely free one-day/one-GiB Trial across all three modes including real USED_TRAFFIC bytes; checkpoint and verify separately.'
remaining_substeps: [R06.g, R06.h, R06.i]
product_implementation: NOT_STARTED
runtime_tests: NOT_RUN_SOURCE_INSPECTION_ONLY
local_worktree_or_external_uncommitted_state: UNKNOWN_NO_LOCAL_CHECKOUT
ci_gate: NOT_VERIFIED
release_gate: LOCKED_IMPLEMENTATION
```

## Binding account, slots and price boundary

- The selectable third commercial mode in inspected code is `USER_CREDIT`; `SEAT_CREDIT` is a **different historical weighted capacity mode** and must stay preserved. One purchase always makes **exactly one `User` row/account**, with `concurrent_user_limit` exactly 1 or 2 and one/two corresponding independently revocable device credential slots; two devices are **not** two User purchases or two USER_CREDIT charges. A user with no finite device count or 0/3+ is invalid for a new paid B09 order. Preserve legacy NULL/unlimited semantics for historical flows only.
- Eight separate configurations per **Product ID**: device connections `{1,2}` × months `{1,2,3,6}` (months 30 days each). Owner alone configures a whole-Toman fixed price for each combination in distinct finance settings/API, not Product network editor, old Plan/version price, a global fixed price or per-device seat credit. Missing combination => reject purchase deterministically. Paid user creation or PENDING reservation debits **exactly this saved amount once** from the shared Admin Toman wallet with D/H guard and ledger; activation does not debit again. Do **not** apply base GiB rate, Product multiplier, traffic volume or duration multiplier to this fixed price. Quota/account count for this mode is distinct from price and device slots; edits of paid user quota/device in ordinary new flow forbidden. Trial exception in R06.g.

## Evidence from inspected current repository (V1, not new Product implementation)

| Source | Verified existing behavior | Product-specific gap |
|---|---|---|
| [`app/utils/admin_billing.py`](../../../app/utils/admin_billing.py) | Enum separately defines `USER_CREDIT`, `SEAT_CREDIT`. `UserCreditStrategy` explicitly returns 0 device-capacity charge for 1 or 2 (or any) connections and says one owned account is counted using `max_users`; legacy `SeatCreditStrategy` uses `finite_seat_cost(concurrent_user_limit)` to charge the number of devices, rejecting None/zero/nonpositive. | Reuse correct **account count vs device limit** mapping. Neither strategy encodes eight per-Product whole-Toman prices or exact Product mode authorization. Do not unify the strategies. |
| [`app/db/models.py`](../../../app/db/models.py) `User`, `DeviceSlot`, `DeviceLimitSettings` | `User.concurrent_user_limit` is nullable Integer and `User` has many `DeviceSlot`; `DeviceSlot` unique `(user_id,slot_index)`, separately enabled with credential and token. Settings declare `device_slots_enabled` independently of default `enabled=False` for the wider device-limit engine. Inspected `AdminUserPlanVersion.price_toman`, `AdminUserPlanPrice`, `OwnerCommercialPolicy` are Plan/global pricing, not Product × device-count × months. | Additive Owner fixed-price table keyed `(product_id,devices,months)` and validation; runtime 1/2 simultaneous connection enforcement cannot be inferred solely from column/slot creation or default settings. Test disabled/alternate settings and remote-Node enforcement before claiming exact concurrency. |
| [`app/device_limit/slots.py`](../../../app/device_limit/slots.py), [`app/xray/operations.py`](../../../app/xray/operations.py) | `sync_device_slots` creates/reenables precisely indices `1..desired` for finite user limit when slot support enabled; excess disabled rather than deleted. Slot 1 uses primary identity; subsequent indices create separate revoked/independent credentials, and Xray add/update enumerates enabled slots. If slot support disabled, desired becomes 0; if limit None, enabled_device_slots returns empty and Xray falls back to base credentials. | Ensure B09 1/2 devices are actually enforced under system settings, failed/reconnected cores and concurrency. One account with two slots must still have a single User ID and one fixed-price ledger entry; no implicit second wallet or SEAT_CREDIT transfer. |
| [`app/utils/admin_plans.py`](../../../app/utils/admin_plans.py), [`app/utils/money_billing.py`](../../../app/utils/money_billing.py) | Old USER_CREDIT Plan creation/renewal uses Plan version quota/device and Plan money price and inherited `UserPlanAssignment` flow; old Plan renewal applies immediately. | New Product B09 must not inherit Plan's amount, apply a duration multiplier, duplicate renewal charge at activation, or persist 1/2 as user-account counts. |
| [`tests/test_stage3_billing_modes.py`](../../../tests/test_stage3_billing_modes.py), [`app/device_limit/engine.py`](../../../app/device_limit/engine.py) | Source tests cover distinct legacy seat cost and USER_CREDIT usage masking; engine is a bounded in-memory activity tracker with settings-based runtime enablement. This audit did not run those tests or trace every engine enforcement branch. | R16/R43 must test one User/two slots/one money debit, all 8 combinations, missing price, no multiply, proper duration, D/H, concurrent purchase/replay and device policy actually enforced (including settings disabled/Node recovery). |

**Stop/verification:** Documentation-only, no table/source/test modifications. Verify the exact new checkpoint blob, one-file diff, branch HEAD and SHA-specific CI/status before R06.g. No live DB, runnable local git checkout or remote-uncommitted inspection. No R07, VERSION, main, workflow dispatch, merge, tag, release or deploy.