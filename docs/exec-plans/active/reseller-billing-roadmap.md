# Product-first v3.1 — live execution ledger

> This is the **implementation checkpoint**, not the authoritative roadmap. Authoritative source: the user-provided `Marzban-Final-Product-v3.1(1).zip` / `ROADMAP-fa.md` (`product_first_v3.1`), especially sections 0, A–G and B01–B16. The ZIP is specifications, not implemented code; the original roadmap is not changed here. Read this ledger and current repository state before every continuation. Date of initial checkpoint: 2026-09-19.

## A. Machine-readable recovery state

```yaml
project: https://github.com/smorad3363/Marzban-v1
contract_version: product_first_v3.1
roadmap_revision: 3.1
roadmap_authority: user-provided ROADMAP-fa.md
baseline_commit: 14e5c9032e5f94f783f34bde391bba318a6de925
baseline_branch: main
baseline_latest_release_or_tag: v1.1.9
baseline_release_commit: 14e5c9032e5f94f783f34bde391bba318a6de925
branch: docs/product-first-v3-1-r01-ledger
worktree_status_at_start: UNKNOWN_NO_LOCAL_CLONE
preexisting_changes: UNKNOWN_NO_LOCAL_WORKTREE
files_modified_by_agent:
  - docs/exec-plans/active/reseller-billing-roadmap.md
current_step: R01
current_substep: null
state: DONE
last_touched_file: docs/exec-plans/active/reseller-billing-roadmap.md
last_touched_hunks: [initial_ledger]
repo_instruction_conflict: UNRESOLVED_FOR_R05
repo_instruction_resolution_evidence: 'User explicitly approved replacing Plan with Product in new product/business flows; whether active AGENTS.md/V1_SCOPE.md can be minimally edited is to be documented precisely in R05 before conflicting changes.'
product_prerequisites: R07_R08_R09_PENDING
release_gate: LOCKED_IMPLEMENTATION
user_test_confirmation: null
final_release_sha: null
release_actions_performed: []
ci_gate: NOT_EVALUATED_FOR_NEW_PRODUCT_IMPLEMENTATION
last_step_github_check:
  sha: null
  status: UNKNOWN
  source: 'R01C must determine stage-required checks on exact future SHA; past release checks are not evidence for new code.'
next_exact_action: 'R01C: inspect actual branch/check protections and six workflow triggers; identify stage-required and final-required nonpublishing checks, record findings only; do not dispatch release.'
recovery_action: 'Read this file on the actual branch, inspect live branch/main HEAD, status/diff if local checkout exists, and the most recent touched hunk before doing R01C.'
```

## B. R00 observation / provenance (read-only, not implementation)

- Authenticated GitHub metadata reports repository `smorad3363/Marzban-v1`, default `main`, with read/write permissions. `main` SHA was independently observed as `14e5c9032e5f94f783f34bde391bba318a6de925`; `VERSION` reads `1.1.9`. GitHub tag `v1.1.9` points at this SHA and stable GitHub Release v1.1.9 is published. Prior `docs/CODEX/STATE.md` still contains historical v1.1.9 release-candidate instructions and is not a reliable status for this new initiative.
- Active instruction files actually found: [`AGENTS.md`](https://github.com/smorad3363/Marzban-v1/blob/main/AGENTS.md), [`docs/CODEX/V1_SCOPE.md`](https://github.com/smorad3363/Marzban-v1/blob/main/docs/CODEX/V1_SCOPE.md), [`docs/CODEX/STATE.md`](https://github.com/smorad3363/Marzban-v1/blob/main/docs/CODEX/STATE.md). The separately named `AGENTS(7).md` attachment is unavailable and was not assumed to have been read. The older `docs/legacy-v0/` is history only.
- Conflict: `AGENTS.md` and `V1_SCOPE.md` say Plan owns commercial entitlement and Access Group owns network. New B01 contract says Product replaces Plan **in new flows**, with Owner-controlled inbound/host, multiplier, lifecycle and authorization. Preserve existing historical Plan records and migration compatibility; do not silently weaken Access Group authorization. User explicitly chose new Product behavior. R05 must reconcile exact instruction changes before conflicting product-code edits.
- Actual code evidence: [`app/utils/admin_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/admin_billing.py) has USED_TRAFFIC / ALLOCATED_TRAFFIC / USER_CREDIT and also SEAT_CREDIT / LEGACY_COMPAT; model-three semantics remain R02/R06 work. [`app/utils/money_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/money_billing.py) contains monetary wallet charges, plan purchases, `charge_form_purchase` and `settle_used_traffic`; existing settlement uses real usage byte deltas, price per GiB, remainder, admin wallet deltas and hourly ledger buckets. The upstream usage producer / per-user watermark and retries have **not** yet been verified; do not label no-double-charge as tested. [`app/utils/access_groups.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/access_groups.py) holds topology/access enforcement. [`app/utils/owner_pricing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/owner_pricing.py) holds legacy form pricing. Existing models and tests are present under `app/db/models.py`, `app/models/`, `app/db/migrations/versions/`, and `tests/`; applicability to Product remains unverified.
- Workflow inventory observed: `.github/workflows/{branch-hygiene,build,checkpoints,dashboard-ui-contracts,validate-v1-installer,verify-v1-image}.yml`. `build.yml` publishes on version-tag push or manual dispatch, not a normal feature-branch push. `checkpoints.yml` targets PR/main, dashboard UI workflow has path filters, installer/image validation are manual, branch-hygiene targets merged PR/main. No rulesets were returned, and `main` metadata reports unprotected: **the release lock is a process rule, not a GitHub-enforced protection**. R01C must verify actual required checks and new-branch behavior, not assume old CI is green for new work.
- Local `git clone`/`git status --short`/`git diff` cannot be checked here: no checked-out repository is present and shell DNS cannot resolve github.com; authenticated GitHub connector reads/writes remote refs only. Pre-existing uncommitted work on someone else's machine is therefore UNKNOWN, not clean. Remote branch `docs/product-first-v3-1-r01-ledger` was created from the exact main baseline after verifying its name did not exist. The ledger path did not exist on main.
- R00 outcome: initial read-only reconnaissance completed with the above explicitly bounded UNKNOWN areas. No Product implementation or regression tests were run or asserted. The historical v1.1.9 work is not counted as any completed Product-first stage.

## C. User-confirmed business decisions — preserve literally in implementation

1. Replace Plan with Product for all **new** product, user creation/edit, renewal/reservation and management flows; do not rename a hidden legacy Plan while reusing its old price/quota semantics. Historical data remain safe.
2. `USED_TRAFFIC`: count **actual new traffic consumed by each user**, charge its owning Admin's **monetary balance** for exactly the unsettled delta at the snapshotted B05 rate, without deducting allocated quota at creation or reservation. On subsequent readings, charge only the new difference. Settle outstanding use before a rate/product change or deletion. Prevent double charges on retries; this is a required future test, not a currently verified property.
3. `ALLOCATED_TRAFFIC`: charge the Admin monetary balance for **the full selected provisioned package** immediately and once at user creation or reservation. Allowed packages `[20,30,50,100]` GiB and durations `[1..6]` months, subject to B05 rate and snapshot. Never charge the same reservation again on activation.
4. Seat/user-count model: **independent Owner-defined fixed pricing** per Product for eight choices (1 or 2 seats × 1/2/3/6 months); do not multiply the seat price by traffic price, product multiplier, or duration multiplier again. Verify actual repository third-mode enum and exact meaning of seats in R02/R06 instead of guessing.
5. For the two traffic modes only: effective per-GiB price = Admin base per-GiB × Product multiplier (default 1) × duration multiplier; apply deterministic rounding after verifying existing units in R06. Product holds identity/network/multiplier/access only; price-per-GiB is Admin financial config and eight fixed seat prices are separate Owner financial config keyed by product ID.
6. All other detailed constraints (access policy, archival preserving active/pending periods, one pending renewal, refunds, security, pricing boundaries, release gate) remain defined by B01–B16 in the attached Persian roadmap. Do not add out-of-scope credit/debt features or change unrelated UI.

## D. Dependencies, conflict and release gate

- Work sequence: `R00 → R01 → R01C → R02..R06 → R07..R09 → R10..R18 → R19..R45`. Before coding each change record intent, path/hunk and before-hash, then focused test and precise diff. Existing completed functionality needs proof on *current* SHA before marking a Product-first stage done.
- Planned atomic substeps, only executed in their own future turns: `R07.a` Product model/migration/tests; `R07.b` Owner create/edit and inbound/host; `R07.c` archive/restore with historical references; `R07.d` disconnect old Plan commercial fields in new flows. `R08.a` authorization tests; `R08.b` all-mode policy; `R08.c` explicit admin-ID policy and UI. `R09.a` duration boundaries/traffic formulas; `R09.b` Owner Product multiplier; `R09.c` Admin base GiB pricing; `R09.d` independent eight-price seat table/API; `R09.e` historical snapshots/ledger tests. Split further if needed and never claim parent DONE until all substeps truly verified.
- `R05` conflict gate: specific contradictory instructions at `AGENTS.md` (Plan owns entitlement), `docs/CODEX/V1_SCOPE.md` (Plan scope), and historic `docs/CODEX/STATE.md`; **business decision approved** in chat, but any edit to active repository instructions must first be scoped and its authority confirmed/documented in R05. Do not edit contradictory implementation before that. Missing `AGENTS(7).md` must not be fabricated.
- Release contract: target `1.1.20` is **not** the current app version; leave VERSION, release notes/tag, GHCR, deployment, dispatch and published aliases alone. No merge into a publishing path. `LOCKED_IMPLEMENTATION` until all 47 stages including R45 and all substeps genuinely DONE, same-SHA CI verified, user explicitly reports their own test succeeded, and a distinct later release command is given. No implicit user-test approval.
- At this docs-only R01 checkpoint: targeted product tests `NOT_RUN` (no product code changed); `git diff --check` on remote tree `NOT_AVAILABLE_NO_LOCAL_CLONE`; validate by readback and GitHub compare for the exact branch commit. GitHub status for baseline cannot be transferred to the new SHA. R01C must assess required vs optional checks and branch rules; do not run release workflows.

## E. Full stage register (47 permanent IDs)

`PENDING` below means **not yet verified or executed in this Product-first initiative**, not proof that code is absent. Stage-specific files/tests are inspected on reaching that step; historical v1.1.9 work never automatically marks stages DONE. Each row's next action is to inspect mapped B clauses and identify exact code paths/nearest test on current branch. Last observed baseline for the entire register: `14e5c903` on 2026-09-19.

| ID | Subject | Status | Evidence / next acceptance |
|---|---|---|---|
| R00 | Repository reconnaissance | DONE (bounded) | GitHub main/tag/AGENTS/STATE, workflow inventory, billing/access/models; uncommitted work UNKNOWN; see B. |
| R01 | Durable execution ledger | DONE (docs-only) | This new file on isolated branch; readback/compare checkpoint required. |
| R01C | Safe GitHub checks | PENDING | Inspect actual protection, required/optional CI, trigger safety; no publishing. |
| R02 | Billing-mode/owner map | PENDING | Inspect real third-mode enum, owner/admin create settings, legacy policy and related tests. |
| R03 | Lifecycle map | PENDING | Trace create/edit/reserve/delete/activation/reset/job/UI routes and tests. |
| R04 | Financial map | PENDING | Trace monetary debit/refund, watermark, price snapshot, rounding, ledger/transactions. |
| R05 | Product/network/UI and instruction conflict | PENDING | Inventory Plan/Access Group/Host/Inbound paths; precisely resolve active instruction conflict before incompatible edits. |
| R06 | Units and semantics | PENDING | Verify day/month, GiB and currency rounding, one-GiB refund boundary, seat meaning and migrations. |
| R07 | Product model and Owner lifecycle | PENDING | Complete R07.a–d; owner-only CRUD, archival and safe migration tests. |
| R08 | Product assignment and authorization | PENDING | Complete R08.a–c; backend/UI tests for mode/admin grants and future admins. |
| R09 | Product/admin/seat pricing | PENDING | Complete R09.a–e; formula boundaries, independent seat prices and historical ledger. |
| R10 | Usage-mode creation tests | PENDING | Positive/unlimited user quota and arbitrary day tests; no upfront debit. |
| R11 | Usage-mode backend | PENDING | Product-bound create, access, snapshot, no Plan in new path. |
| R12 | Usage-mode UI | PENDING | Product/name/day/quota only and focused UI contract. |
| R13 | Allocated-mode creation tests | PENDING | Four quotas/six durations, invalid API rejection and exactly-once upfront debit. |
| R14 | Allocated-mode backend | PENDING | Atomic charge/package snapshot, immutable active period. |
| R15 | Allocated-mode UI | PENDING | Only allowed packages/durations and product selector. |
| R16 | Seat-mode creation tests | PENDING | Eight combos, missing-price refusal and no compounded charge. |
| R17 | Seat-mode backend | PENDING | Fixed Owner monetary prices and single upfront debit. |
| R18 | Seat-mode UI | PENDING | Eight choices, independent price display, no Plan. |
| R19 | Unified product selection | PENDING | One authorized active Product; reject direct unauthorized API selection. |
| R20 | Simplify Admin creation | PENDING | Appropriate Admin mode/base rate and auto mode-wide Product grants. |
| R21 | Product network propagation | PENDING | Verify nodes derived through access relationships; preserve active quotas/financial state. |
| R22 | Incremental-usage tests | PENDING | Two readings + retries + rate-change boundary, user-owned actual bytes. |
| R23 | Incremental settlement | PENDING | Watermark, exact deltas, owner wallet debit, snapshot and idempotency. |
| R24 | Reservation-only model | PENDING | One pending, snapshot/keys, no immediate service switch. |
| R25 | Reservation tests | PENDING | Authorization, concurrency, upfront vs usage behavior. |
| R26 | Reservation API/service | PENDING | Atomic reserve, persisted snapshot, idempotency and billing. |
| R27 | Activation trigger tests | PENDING | First end of quota or time; unlimited quota uses time only. |
| R28 | Atomic activation | PENDING | Settle old period first, single activation, never charge prepaid twice. |
| R29 | Runtime integration | PENDING | Scheduler/reset/usage checks and restart recovery. |
| R30 | Cancellation tests | PENDING | Pending-only cancellation, refund once and permission boundaries. |
| R31 | Reservation cancellation API | PENDING | Safe atomic cancel/refund and duplicate key behavior. |
| R32 | Reservation UI | PENDING | Clear reserve vs immediate renew behavior, price/period details. |
| R33 | Cancellation UI | PENDING | Permission-aware pending cancellation and balance update. |
| R34 | Deletion-threshold tests | PENDING | Usage 1 GiB boundary, active period, pending precedence, modes. |
| R35 | Active-period delete refund | PENDING | Final settlement; below-one-GiB prepaid refund once; usage never refunded. |
| R36 | Delete with pending reservation | PENDING | Cancel pending and refund before active settlement/delete exactly once. |
| R37 | Edit-authorization tests | PENDING | Usage-only editable active; owner/scope remains enforced. |
| R38 | Usage-mode edit backend | PENDING | Settle old rate first and snapshot new; restrict fields. |
| R39 | Usage-mode edit UI | PENDING | Authorized limited edit, no direct network/device controls. |
| R40 | Trial tests | PENDING | Preserve existing quota/cleanup, Product compatibility. |
| R41 | Targeted Trial repair | PENDING | Only if B clauses fail on current SHA; no speculative rewriting. |
| R42 | Financial audit | PENDING | Verify charge/refund/snapshot/retries and ledger traceability. |
| R43 | Focused end-to-end verification | PENDING | Mode, access, archival, reservation, concurrency, migrations, recovery. |
| R44 | Full scope/release review | PENDING | Every changed hunk mapped to B; no unrelated changes/deploy. |
| R45 | Handoff for user testing | PENDING | All IDs/substeps DONE and final SHA checks PASS; tell user to test, NOT release. |

## F. Recovery checklist / exact next task

1. Fetch this exact file and branch head, then compare it with `main`. Inspect any existing local working-tree status/diff if access becomes possible; do not assume clean based on GitHub.
2. Confirm R01 docs-only commit/readback and branch diff: exactly one new ledger file, no product code, version, tag, workflow or release changes. If unexpected diff, mark `NEEDS_REVIEW` and stop.
3. Execute **only R01C** in the next user turn: discover truly required GitHub checks and workflow triggers; distinguish stage and final gates; record unknown permissions/branch protection. If a test workflow is missing, plan isolated nonpublishing addition as its own future substep rather than editing it in the same turn.
4. Then stop and request explicit continuation. Never equate successful historical v1.1.9 CI with new Product implementation tests.

Last completed step: `R01` (ledger only). Next ID: `R01C`. No user test, release action, tag, merge or deployment authorized.
