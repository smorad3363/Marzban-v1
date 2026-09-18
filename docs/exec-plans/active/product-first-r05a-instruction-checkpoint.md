# Product-first R05.a — active-instruction reconciliation and six decisions

Date 2026-09-19. Product contract authority: user-provided `Marzban-Final-Product-v3.1-Revised(1).zip`, SHA-256 `bfbde1cfa3937433ca69735a094b42f825d114c6e1b4cd152a9021d825194886`, especially the Persian `ROADMAP-fa.md` B01–B20 and later explicit user answers. This file is an execution checkpoint, NOT a modification of that ZIP or completion of Product code. Earlier mapping: [`R05`](product-first-r05-network-instruction-checkpoint.md), [`R04`](product-first-r04-financial-checkpoint.md), [`R03`](product-first-r03-lifecycle-checkpoint.md), [`wallet-only decision`](product-first-wallet-only-decision.md), and [`primary ledger`](reseller-billing-roadmap.md). Older checkpoints have frozen historical `current_step` fields; newest checkpoint controls resume.

## Machine-readable recovery state

```yaml
contract_version: product_first_v3.1
contract_amendment: wallet_debt_controls_2026-09-19_and_six_answers
stage: R05
substep: R05.a
state: DONE_DOCS_ONLY
instruction_conflict: RESOLVED_SCOPED_NEW_PRODUCT_VS_LEGACY_V1
branch: docs/product-first-v3-1-r01-ledger
source_before_sha: 399d28fe1f84ab8fd9290d13d4576c4ccdbb5b9b
last_instruction_commit: ef93345952dd955c4b51c79557e74d49774155ed
next_exact_action: 'On next separate continue turn execute ONLY R06 read-only units and semantics audit against revised roadmap, including 30-day months, original I=0, rounding/GiB, node relationships, live Product network versus frozen paid quote, subtree freeze, trial fully zero and migration. Split R06 if genuinely necessary; no implementation under R05.a.'
app_code_changed: false
migration_changed: false
roadmap_zip_changed: false
version_changed: false
main_changed: false
runtime_tests: NOT_RUN_DOCS_ONLY_NO_LOCAL_CHECKOUT
local_git_status: UNKNOWN_NO_LOCAL_CHECKOUT
other_machine_uncommitted_changes: UNKNOWN
user_test_confirmation: null
ci_gate: NOT_VERIFIED_FINAL_SHA
release_gate: LOCKED_IMPLEMENTATION
release_actions_performed: []
```

## Explicit user decisions, authoritative above outdated wording

1. The user approved **only** minimal instruction reconciliation `R05.a`: add new-Product-scoped clarification to `AGENTS.md` and `docs/CODEX/V1_SCOPE.md`, add historical status pointer on top of `docs/CODEX/STATE.md`, do not erase historical code or records; no application change under this substep.
2. All commercial Product purchases/settlements in `USED_TRAFFIC`, `ALLOCATED_TRAFFIC`, and the one-User/1-or-2-concurrent-devices third mode use **one per-Admin Toman wallet**. Creation-time first grant is the immutable baseline `I`; subsequent grants add wallet balance but never rewrite I. Creation with initial grant **zero is permitted**: I=0, default D=0, hard H=0, no optional debt, no percentage warning until a positive I is validly recorded in the original creation transaction. If creation finishes with zero, subsequent ordinary top-ups do not retroactively redefine I. No new Admin volume/seat-credit wallet. Preserve legacy data safely. All Products draw from this same monetary wallet, with mode-specific debit timing.
3. For all package and duration semantics **one month means exactly 30 days**, not calendar months. Explicitly check timestamp/timezone/rounding and expiry under R06; do not adjust old historical purchased periods retroactively.
4. Trial (`test user`, 1 GiB/one day, five default allowed per Admin subject to Owner adjustable quota) is **fully monetary-free across all THREE models**, both creation/reservation price AND actual consumed bytes in `USED_TRAFFIC`; no wallet debit, fixed-account fee or Admin traffic/seat credit for this Trial. It still consumes distinct Trial issuance quota; deletion does not replenish it automatically. Ensure usage counters still work for real quota, audit and abuse limits; prevent later regular usage from inheriting free pricing. Implementation/test belongs to R40/R41 and affected settlement stages, NOT here.
5. Owner's one-click group freeze/instant connection disconnect targets **the chosen Admin and every descendant Admin's users** (scope snapshot/authorized subtree), not only directly owned users. Resumption restores only precisely the users frozen by that event and still eligible; never activate independently disabled, expired, over-quota or separately suspended users, never renew/change price, check every Node status, preserve retry/audit. ADMIN_EMERGENCY_FROZEN (panel read-only at H) is distinct from Owner's manual user freeze. Implementation and tests later under B20 and impacted stages.
6. Product network is **live configuration**, not reservation-time frozen Host/Inbound: when Owner changes Product's validated network, propagate to **all active users bound to that Product**, including when Product is archived but historical service remains; a previously accepted pending reservation resolves the latest **valid** same Product network at activation. Keep immutable Product ID, purchased/rate/duration/amount snapshots; changed multiplier/Owner grant/archive applies to **future purchases/selection** only and must not cancel a previously paid reservation. If new network is invalid/unavailable, fail closed and surface retry/actionable error; never silently grant unrestricted access or substitute another Product. The revised roadmap's historical `snapshot` wording is interpreted as **financial, entitlement, authorized-at-booking evidence**, not permanent Host/Inbound snapshot; this explicit later user choice takes precedence for network. R06 must investigate real Host↔Inbound↔Node mapping and propagation/fail-closed behavior before implementation.

Already confirmed, do not re-ask: D defaults `floor(0.05*I)` Toman, Owner edits per-Admin D with `0<=D<=H`, H=`floor(0.15*I)` absolute optional-charge ceiling, warning when balance `<= 0.10*I` for I>0, periodic consumption overrun is real ledger debt plus safety cutoff (never claim exact byte cutoff), zero balance alone does not automatically cancel fully prepaid customers. One user/account with one/two simultaneous device slots costs exactly one user entitlement; eight Owner-set fixed prices by Product, no compounding other multipliers. Actual enum `USER_CREDIT` remains distinct from historical weighted `SEAT_CREDIT`.

## Modified paths, exact before hashes, write and diff verification

Before stage branch HEAD: `399d28fe1f84ab8fd9290d13d4576c4ccdbb5b9b`; `main` baseline `14e5c9032e5f94f783f34bde391bba318a6de925`. Intent was recorded locally at `/mnt/data/marzban_work/R05a-intent.md` before remote writes (SHA-256 `5ea27106a9f330fd7f72455ca8f6646bba1ad3efbf8d21ad0217a1c1add3fdb6`). GitHub connector supports remote file edits but not local `git status` or inspection of uncommitted work on another computer.

| File | Before blob | After blob/commit | Exact authorized change |
|---|---|---|---|
| `AGENTS.md` | `0b29da49ac60f3679d7a7c58798e81a0eb1be497` | `209fe785e7ecf5d453118d457778e7eaad3d7c5d` / `0e685e06ff06aa73178a5aa6ebfa3f6b242ef198` | New Product-first scope, authority, network, legacy compatibility, wallet and release-lock preface. Prior text preserved, GitHub commit patch additions only. |
| `docs/CODEX/V1_SCOPE.md` | `1c99e3b1c9f32413881e6665c0a35ffe268a0bad` | `d817ccac168b79b12dd600855545e4f6ab7eac0a` / `76dc4d641d863a627ebbda974d07b357c1a69a5b` | Historical-scope note and Product-first addendum only. GitHub diff additions only, previous historical release contract unchanged. |
| `docs/CODEX/STATE.md` | `c15ede9dbff6c726b4602064e589cb0204f6b67c` | `3b3365648b6e89d3f161165ae73ba79882f96910` / `ef93345952dd955c4b51c79557e74d49774155ed` | Historical-state pointer at top only. First edit `36f94ad...` accidentally changed three historical SHA repetitions during whole-file API replacement. Self-review identified them immediately; corrective commit `ef933459...` restored all three to exact original. Verify cumulative diff from before SHA shows **only two added pointer lines**, no historical deletion/modification. |

The separately named `Project Engineering Agent Contract — AGENTS(7).md` is **now found and fully read** in user's connected Library, actual identity `file_000000003ed88246bcd2e80e860c6727`, version 1, 1113 lines (read in 3 contiguous chunks). This supersedes R05 mapping's earlier 'unavailable' observation; the Library document is not claimed to be committed to the GitHub repository or an attached file inside the revised ZIP. Its minimum-diff, protection of existing user work, tests honestly reported, migration, recoverability and no premature done rules apply. The newest specific user Product-first business contract takes precedence over incompatible historical V1 business instructions but does not relax its engineering or security safeguards.

**Post-write checks:** Each write returned exact GitHub commit/blob SHA and the instruction files were read back or their commit patch reviewed. `AGENTS.md` patch and `V1_SCOPE.md` patch were checked additions-only; `STATE.md` first patch was inspected and corrected before checkpoint; final cumulative additions-only must be checked after this commit. Compare `main` to final branch and exact-SHA check-runs/combined status separately, and record real results, no invented PASS. No PR, merge, tag, workflow dispatch, VERSION or release.

## R06 next, no implied authorization for source code

First audit precise financial rounding, positive duration/day and 30-day month boundaries, GiB bytes and 1-GiB refund threshold; `USER_CREDIT` single-account price vs `SEAT_CREDIT` history; initial funding field/migration (I immutable incl zero) and D/H/warnings state; full-free Trial ignoring monetary and usage fee across all modes without suppressing telemetry; actual Node↔Inbound↔Host relationships and safe dynamic Product propagation incl active + pending/archived; subtree freeze scope, per-Node disconnect acknowledgements, precise restore; clean-install/forward upgrade baseline. Only record observed vs missing, test names/results and residual blockers, do not implement R07 onward on that same turn.
