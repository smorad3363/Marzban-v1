# Product-first R06.e — read-only paid-period / pending financial snapshot audit

Date: 2026-09-19. Authority: supplied FINAL v3.1 Persian `ROADMAP-fa.md` B02/B05–B06/B10–B12/B14/B17–B18 and R06/R24–R31; amended [`AGENTS.md`](../../../AGENTS.md). Previous [R06.d](product-first-r06d-live-network-checkpoint.md) was read back at its exact SHA before this audit. The user explicitly authorized five ordered audit substeps R06.e–R06.i in one turn, each in its own verified commit. This file is R06.e ONLY: no code, migration, tests or R07.

```yaml
repo: smorad3363/Marzban-v1
branch: docs/product-first-v3-1-r01-ledger
source_sha_inspected: 682f5be665e5874e9ca9535c84ca1cc73b79a6d4
stage: R06
stage_state: IN_PROGRESS_SPLIT_READ_ONLY
completed_substeps: [R06.a, R06.b, R06.c, R06.d, R06.e]
completed_this_commit: R06.e
next_exact_action_in_current_five_substep_request: 'Verify R06.e readback/diff/branch/checks, then R06.f ONLY: audit one USER_CREDIT account with one/two concurrent device connections, legacy SEAT_CREDIT distinction and fixed eight-price combinations; separately checkpoint/verify.'
remaining_substeps: [R06.f, R06.g, R06.h, R06.i]
product_implementation: NOT_STARTED
runtime_tests: NOT_RUN_SOURCE_AUDIT_ONLY
local_worktree_or_external_uncommitted_state: UNKNOWN_NO_LOCAL_CHECKOUT
ci_gate: NOT_VERIFIED
release_gate: LOCKED_IMPLEMENTATION
```

## Binding snapshot/transition contract, not current implementation

- At first paid Product creation, immutable owner Admin, mode, Product ID and name-at-purchase, acceptance/authorization evidence, current-period ID, quota/days, period start/end, effective traffic base/product/duration multipliers and rounding OR independent USER_CREDIT fixed price, total **actually paid** Toman, transaction/idempotency keys and per-period usage/rate watermark must be durable. Subsequent Owner edit to multiplier or pricing does not reprice history. Network selection snapshot is audit evidence only: **latest valid network of the same Product applies live**, even when archived or permission for *new selection* revoked.
- Every renewal is a reservation of the NEXT period, never immediate overwrite. Exactly one PENDING per subscription, with unique constraint/lock; at acceptance Product must be ACTIVE and authorized and per-mode amount/terms fully snapshotted. USED_TRAFFIC reserves at zero upfront charge and bills only future actual usage; ALLOCATED_TRAFFIC and USER_CREDIT prepay once at reservation under the single Toman wallet/D guard, and activation never charges again.
- On earliest current-period time or quota exhaustion (unlimited: time only), finalize old actual-usage billing and immutable history; lock user/period/reservation, atomically transition exactly `PENDING -> ACTIVE` while closing prior period, set new period start to **actual activation**, reset its usage to zero and apply the saved paid quota/duration/rate/price and same Product ID. Resolve latest **valid** Product Host/Inbound then, even if Product since archived/revoked, without rechecking an already-accepted purchase as a new order. Invalid topology fails closed and requires recoverable retry, not silent cancellation, network fallback, loss of paid amount or double charge.
- Cancellation competes with activation under the same lock/state compare: `PENDING -> CANCELLED_REFUNDED` only by owning Admin before activation. Refund once the **saved actual amount paid** for prepaid modes, zero for USED, and do not touch active period. Deletion with both: cancel/refund pending first, then independently settle/refund active according to strict current-period `< 2^30` bytes; two separate ledger events and idempotency. No current balance, revised Product price, lifetime bytes or current Host constitutes historic payment evidence.

## Source-inspected differential at pinned SHA

| Existing source | Evidenced legacy behavior | New Product gap |
|---|---|---|
| [`app/db/models.py`](../../../app/db/models.py) `UserPlanAssignment`, `NextPlan`, `User`, `AdminMoneyTransaction` | `UserPlanAssignment` snapshots old Plan/version, actor, trial flag, operation and unique key, **not** Product/paid period/effective pricing. `NextPlan` stores user ID, data limit, expire, add-remaining and fire-on-either, not Product ID, owner, state, price, paid transaction or acceptance evidence. `User` has `next_plan` uselist=False relation, used-traffic and expire; relationship alone is not proof of DB-enforced one pending. `AdminMoneyTransaction` has signed Toman, before/after, Plan/version/user and JSON details but no dedicated Product/period/reservation/rate-snapshot/watermark links in inspected schema. | Additive R24 period/reservation schema and authoritative snapshot plus unique single-pending DB guard, immutable financial ledger linkage and migration; preserve old history and avoid guessing past prices. |
| [`app/utils/admin_plans.py`](../../../app/utils/admin_plans.py) `create_user_from_plan`, `renew_user_from_plan` | Legacy create binds Plan + separate Access Group, assigns version and money charge in same transaction. Legacy **renew** locks User, resets `used_traffic`, rewrites quota/status/slots and extends `expire=max(now, old_expire)+days*86400` **immediately**, then records `UserPlanAssignment` and charge. Not a deferred, paid Product PENDING. Existing plan renewal revalidates current Plan/group permission; cannot apply this new-purchase check to already accepted Product reservations at activation. | Separate reserve and activation services R24–R29, with saved price and no early rewrite/re-charge; old historical Plan renew remains intact. |
| [`app/utils/money_billing.py`](../../../app/utils/money_billing.py), [`app/utils/owner_pricing.py`](../../../app/utils/owner_pricing.py) | Plan charge uses current version/override price; Form price uses current global policy and upward rounding; USED billing prices aggregate Admin bytes using mutable current Admin rate and hourly ledger. No Product-specific immutable rate boundary is demonstrated by these paths. | Product/period rate snapshots and per-user watermarks before rate edit, exact paid amount for refunds, no reinterpretation of old legacy ledger. |
| [`app/utils/access_groups.py`](../../../app/utils/access_groups.py), [`app/subscription/share.py`](../../../app/subscription/share.py) | Existing Access Group has live Host scope and resyncs active users; archived group fails scope. Product identity/pending activation/network resolution is not implemented in inspected paths. | Product archive may not delete/disable live backing network; pending activation resolves latest valid network without modifying saved money/term snapshot, with per-node propagation tests reserved for R21/R27–R29. |

## Future tests, risks, stop

Not run: one pending constraint under two simultaneous requests; concurrent cancel-vs-activate exactly one wins; prepaid one debit at reservation/none activation; USED no upfront debit; zero/positive refund on cancellation; immutable `paid_toman` after Owner price edits; archived/revoked product allows existing accepted pending; invalid Host aborts activation without losing pending/payment; exact trigger time/quota simultaneous; reset/late usage barrier and old/new rate watermark; delete pending+active two events. Source audit does not claim any Product persisted data exists or database is empty; no live DB, local checkout or CI PASS available. Write only this new doc; verify its own readback, single-doc diff, branch SHA and CI. No VERSION/main/merge/tag/release/deploy/workflow dispatch. Release LOCKED.