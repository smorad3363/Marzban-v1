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
  - app/db/models.py
  - app/db/migrations/versions/f7a3c9e1d205_add_product_catalog.py
  - app/models/product.py
  - app/utils/products.py
  - app/routers/products.py
  - app/dashboard/src/pages/Products.tsx
  - tests/test_product_catalog.py
  - tests/test_product_owner_lifecycle.py
  - docs/exec-plans/active/product-first-r07-completion-checkpoint.md
current_step: R07
current_substep: R07.d
state: DONE_LOCAL_VERIFIED
last_touched_file: docs/exec-plans/active/product-first-r07-completion-checkpoint.md
last_touched_hunks: [R07_product_schema, R07_owner_api, R07_archive_restore, R07_owner_ui]
repo_instruction_conflict: RESOLVED_PRODUCT_FIRST_NEW_FLOWS
repo_instruction_resolution_evidence: 'R05a amended AGENTS.md for Product-first new flows; on 2026-09-19 the user further confirmed fresh-install-only and accepted prior-data loss, now recorded without dropping still-referenced legacy tables prematurely.'
product_prerequisites: R07_DONE_R08_R09_PENDING
release_gate: LOCKED_IMPLEMENTATION
user_test_confirmation: null
final_release_sha: null
release_actions_performed: []
ci_gate: LOCAL_R07_PASS_REMOTE_NOT_RUN
branch_protection_observation: 'main metadata protected=false; protection details returned 403; repo rulesets including parent rulesets empty; no required checks demonstrably enforced'
last_step_github_check:
  sha: bd650070011151eb88c2e2c5e5db783b58ac96e8
  status: NO_CHECK_RUNS_OR_STATUSES_FOR_R01C_HEAD
  source: 'GitHub exact-SHA check-runs/status observed at previous R01C checkpoint; after this R02 docs commit, query checks on the new HEAD separately.'
next_exact_action: 'R08.a: add Product assignment and authorization tests without changing main, VERSION, release workflows, tags, or deployment.'
recovery_action: 'Fetch this branch at the R07 completion SHA, read product-first-r07-completion-checkpoint.md, confirm the four R07 commits and clean worktree, then start only R08.a.'
```

## B. R00 observation / provenance (read-only, not implementation)

- Authenticated GitHub metadata reports repository `smorad3363/Marzban-v1`, default `main`, with read/write permissions. `main` SHA was independently observed as `14e5c9032e5f94f783f34bde391bba318a6de925`; `VERSION` reads `1.1.9`. GitHub tag `v1.1.9` points at this SHA and stable GitHub Release v1.1.9 is published. Prior `docs/CODEX/STATE.md` still contains historical v1.1.9 release-candidate instructions and is not a reliable status for this new initiative.
- Active instruction files actually found: [`AGENTS.md`](https://github.com/smorad3363/Marzban-v1/blob/main/AGENTS.md), [`docs/CODEX/V1_SCOPE.md`](https://github.com/smorad3363/Marzban-v1/blob/main/docs/CODEX/V1_SCOPE.md), [`docs/CODEX/STATE.md`](https://github.com/smorad3363/Marzban-v1/blob/main/docs/CODEX/STATE.md). The separately named `AGENTS(7).md` attachment is unavailable and was not assumed to have been read. The older `docs/legacy-v0/` is history only.
- Conflict: `AGENTS.md` and `V1_SCOPE.md` say Plan owns commercial entitlement and Access Group owns network. New B01 contract says Product replaces Plan **in new flows**, with Owner-controlled inbound/host, multiplier, lifecycle and authorization. Preserve existing historical Plan records and migration compatibility; do not silently weaken Access Group authorization. User explicitly chose new Product behavior. R05 must reconcile exact instruction changes before conflicting product-code edits.
- Actual code evidence: [`app/utils/admin_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/admin_billing.py) has USED_TRAFFIC / ALLOCATED_TRAFFIC / USER_CREDIT and also SEAT_CREDIT / LEGACY_COMPAT; model-three semantics mapped in H but exact new Product seat/account wording remains R06. [`app/utils/money_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/money_billing.py) contains monetary wallet charges, plan purchases, `charge_form_purchase` and `settle_used_traffic`; existing settlement uses real usage byte deltas, price per GiB, remainder, admin wallet deltas and hourly ledger buckets. The upstream usage producer / per-user watermark and retries have **not** yet been verified; do not label no-double-charge as tested. [`app/utils/access_groups.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/access_groups.py) holds topology/access enforcement. [`app/utils/owner_pricing.py`](https://github.com/smorad3363/Marzban-v1/blob/main/app/utils/owner_pricing.py) holds legacy form pricing. Existing models and tests are present under `app/db/models.py`, `app/models/`, `app/db/migrations/versions/`, and `tests/`; applicability to Product remains unverified.
- Workflow inventory observed: `.github/workflows/{branch-hygiene,build,checkpoints,dashboard-ui-contracts,validate-v1-installer,verify-v1-image}.yml`. `build.yml` publishes on version-tag push or manual dispatch, not a normal feature-branch push. `checkpoints.yml` targets PR/main, dashboard UI workflow has path filters, installer/image validation are manual, branch-hygiene targets merged PR/main. No rulesets were returned, and `main` metadata reports unprotected: **the release lock is a process rule, not a GitHub-enforced protection**. R01C verified triggers and safe check strategy in section G.
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
- At R02: targeted Product tests `NOT_RUN`; `git diff --check` `NOT_AVAILABLE_NO_LOCAL_CLONE`; GitHub exact-SHA checks for the new docs commit must be assessed independently. No code/business mutation was needed for this mapping.

## E. Full stage register (47 permanent IDs)

`PENDING` below means **not yet verified or executed in this Product-first initiative**, not proof that code is absent. Stage-specific files/tests are inspected on reaching that step; historical v1.1.9 work never automatically marks stages DONE. Each row's next action is to inspect mapped B clauses and identify exact code paths/nearest test on current branch. Last observed baseline for the entire register: `14e5c903` on 2026-09-19.

| ID | Subject | Status | Evidence / next acceptance |
|---|---|---|---|
| R00 | Repository reconnaissance | DONE (bounded) | GitHub main/tag/AGENTS/STATE, workflow inventory, billing/access/models; uncommitted work UNKNOWN; see B. |
| R01 | Durable execution ledger | DONE (docs-only) | One added ledger file on isolated branch; confirmed readback and compare against main on exact R01 SHA. |
| R01C | Safe GitHub checks | DONE (audit only) | Actual branch rules, triggers and gate matrix documented in G; checks are NOT_RUN and not enforced by GitHub. |
| R02 | Billing-mode/owner map | DONE (audit only) | Source-verified mode/Owner/Admin/legacy mapping and existing test inventory in H; no business code changed or tests run. |
| R03 | Lifecycle map | DONE (audit) | Exact create/edit/reserve/delete/activation/reset/job/UI paths recorded in the R03 checkpoint. |
| R04 | Financial map | DONE (audit) | Debit/refund/watermark/snapshot/rounding/ledger paths recorded in the R04 checkpoint. |
| R05 | Product/network/UI and instruction conflict | DONE (audit/instruction) | Network ownership and UI paths audited; Product-first amendment recorded in R05/R05a. |
| R06 | Units and semantics | DONE (audit/decisions) | R06.a–i checkpoints record time, byte, money, network, reservation, user-credit, Trial, freeze/restore, and migration decisions. |
| R07 | Product model and Owner lifecycle | DONE (local verified) | R07.a–d: independent schema, owner-only API, safe archive/restore, Owner UI; disposable fresh-DB migration and 41 focused backend tests passed; see R07 completion checkpoint. |
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

1. Fetch this exact branch head and read `product-first-r07-completion-checkpoint.md`; compare the R07 diff against its recorded pre-stage SHA.
2. Confirm the four atomic R07 implementation commits plus the final test/checkpoint commit, and verify the worktree is clean before new work.
3. Execute **only R08.a** next: Product-assignment and authorization tests. Fresh-install is the accepted deployment target, but do not drop still-referenced legacy tables until their runtime paths are replaced and a dedicated schema-cleanup test exists.
4. Continue to keep `main`, VERSION, tags, release workflows, deployment, and publication untouched.

Last completed step: `R07` (Product model and Owner lifecycle; locally verified). Next ID: `R08`. No user test, release action, tag, merge or deployment authorized.

## G. R01C — exact GitHub protections, workflow triggers and safe CI gates (2026-09-19)

### G1. Direct observations at R01 head

- `main` HEAD = `14e5c9032e5f94f783f34bde391bba318a6de925`; R01 branch HEAD = `014abc104e4899961dfd8404954676b1522fb54d`; GitHub compare reports exactly one added documentation file and no modifications to app/workflow/version. Confirm HEAD again after this R01C commit.
- `GET /branches/main` has `protected: false`, `protection.enabled: false`, `required_status_checks.enforcement_level: off`, empty contexts/checks. `GET /rulesets?includes_parents=true` returned `[]`. Direct `GET /branches/main/protection` returned `403 Resource not accessible by integration`; do not assert all administrative policy details are known. **No enforced required check can be demonstrated on this connection**; treat review/check gates as human-controlled and do not merge automatically.
- R01 SHA GitHub check-runs = `0`, commit statuses = `[]`, branch workflow-runs = `0`. This is `NOT_RUN`, not `PASS`; the CI history for `v1.1.9` is not transferable to this SHA. On final code SHA insist on actual run details and job conclusions, not an aggregate green badge with skipped backend.

### G2. All six workflows as actually read at R01 SHA

| Workflow | Automatic triggers | Safe pre-release usage and caution |
|---|---|---|
| `.github/workflows/checkpoints.yml` (`CI Checkpoints`) | `pull_request` targeting `main`; `push` to `main`; `workflow_dispatch`. No automatic feature-branch push. | Nonpublishing: permissions `contents:read`; on PR or manual dispatch runs backend MySQL `8.0` and `26.7.0`, migrations/Stage 8–11/backup/rollback, dashboard build/parity, packaging/8→26 restore, local-only image build/runtime, Panel-to-Node mTLS. On `main` push the backend job is deliberately SKIPPED; packaging PR/dispatch-only steps are SKIPPED. Therefore main-push success is insufficient for final release gate. |
| `.github/workflows/dashboard-ui-contracts.yml` (`Dashboard UI Contracts`) | `pull_request` to `main` or `push` to `main` **only when** dashboard source/scripts/build or workflow path matches; `workflow_dispatch`. | Nonpublishing read-only workflow. Runs Stage 1 UI, authenticated-autofill, typecheck/build and committed bundle parity. Backend-only/docs-only PR does not automatically trigger it; for final gate obtain a head-SHA verified run when needed, or add a separately authorized nonpublishing gate later. |
| `.github/workflows/build.yml` (`Release`) | `push` of `v*` tag except `v1.0.0`; manual `workflow_dispatch` defaults `git_ref: main`, `image_tag: latest`, `tests_only: false`. | **DANGEROUS/PUBLISHING**: writes content/packages, pushes GHCR multiarch images and tag/latest; for tagged ref may create a GitHub Release. `tests_only: true` skips entire publish job and does not provide a test substitute. Never dispatch this workflow for development, including a proposed testing-only invocation; do not create version tags. |
| `.github/workflows/branch-hygiene.yml` (`Branch Hygiene`) | PR to `main` when closed; `push` to `main`. | Contents-write workflow automatically DELETES merged PR head branches from same repo (except two hardcoded names). Main push has a special old-commit-message cleanup path. Avoid merging working PR before explicit authorization and durable state; do not assume merged work branch survives. |
| `.github/workflows/validate-v1-installer.yml` (`Validate published V1 installer`) | `workflow_dispatch` only, mandatory published digest/source SHA/release tag. | Nonpublishing validation but **post-publication** source/image validation; not a replacement for pre-release checks and not run now. |
| `.github/workflows/verify-v1-image.yml` (`Verify published V1 image`) | `workflow_dispatch` only, mandatory digest/source SHA/release tag. | Nonpublishing verification of an already-published tagged image, manifest and runtime; not pre-release evidence and not run now. |

### G3. Required project gates versus actually enforced GitHub settings

1. **Docs-only / R01C:** prove remote compare changes only ledger; fetch commit and file readback; inspect check-runs/status on precise branch SHA. Running a product test for unchanged code is optional here; record `NOT_RUN`, never `PASS`.
2. **Per Product-code stage before claiming DONE:** test exact touched behavior locally or under an explicitly nonpublishing test workflow, examine exact diff, migration or UI contract as appropriate, and write results into this ledger. `git diff --check` is `NOT_AVAILABLE` until a local worktree is accessible; do not claim it passed.
3. **PR/integration:** only a nonmerged PR targeting main triggers full `CI Checkpoints` automatically. Require backend matrix both MySQL versions with all backend/migration/backup/rollback jobs genuinely `success`, dashboard build/parity and packaging including Docker and mTLS genuinely `success`, no failure/cancelled/skipped critical job. Inspect the tested commit identity: PR workflows may build a synthetic merge ref; a green result on that ref is not automatically a green result on exact source head.
4. **Dashboard-specific gate:** require separate `Dashboard UI Contracts` Stage 1/autofill/typecheck/build/parity when dashboard changed and for final release readiness. Workflow path filters can omit backend/docs-only PRs. If no qualifying exact-head check exists, arrange a separately approved nonpublishing run or workflow update; do not substitute an old run, a skipped check, or a Release run.
5. **Final project gate:** all 47 IDs/substeps DONE; current final source SHA verified; required nonpublishing checks on matching SHA/content all successful with no skipped mandatory matrix; migrations/backups/rollback/installer/Node/financial regression confirmed; check full baseline diff; user explicitly tests and approves, then gives a *different, explicit* release command. `main` has no demonstrated branch protection, so this is an operational lock until protection can be separately configured/verified. Never use the Release workflow as a test tool.
6. **No configuration mutations during R01C:** no branch rules, workflow changes, PR, tag, release or dispatch performed. If stronger enforced CI or guaranteed exact-head checks are needed, plan a separate authorized isolated docs/workflow step; verify that any workflow addition cannot publish and runs on the intended SHA.

### G4. R01C checkpoint test and evidence status

- Readback target: this file on `docs/product-first-v3-1-r01-ledger`, blob previously `a35803665810a683ba118a85a135dbd72cadaa99`; after commit, verify full new blob and the comparison contains **only** this Markdown file, main unchanged.
- Product test `NOT_RUN`; GitHub checks for prior `014abc104e4899961dfd8404954676b1522fb54d`: `0` check-runs / `[]` statuses / `0` branch workflow-runs. Check new documentation commit SHA separately; no passing CI claimed.
- Evidence on fixed source revision: `.github/workflows/checkpoints.yml`, `dashboard-ui-contracts.yml`, `build.yml`, `branch-hygiene.yml`, `validate-v1-installer.yml`, `verify-v1-image.yml`; GitHub branch metadata, rulesets, failed protection access, exact-SHA check-runs and compare.
- Resume at **R02** only after confirming this checkpoint; do not run or dispatch `Release`.

## H. R02 — Owner/Admin billing-mode and legacy mapping (read-only code audit, 2026-09-19)

### H1. Provenance and exact symbols (all inspected at pre-stage SHA `bd650070011151eb88c2e2c5e5db783b58ac96e8`)

- [`app/utils/admin_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/utils/admin_billing.py), `BillingMode` and `STRATEGIES`: five stored enum values exist: `LEGACY_COMPAT`, `SEAT_CREDIT`, `USED_TRAFFIC`, `ALLOCATED_TRAFFIC`, `USER_CREDIT`. The third *new* commercial mode is **`USER_CREDIT`**, whose strategy explicitly says each owned account costs one user credit and device counts do not affect its charge. `SEAT_CREDIT` instead uses `concurrent_user_limit` as weighted finite devices, rejects 0/unlimited and retains consumed capacity on deletion. Preserve it for old records; do not rename/reuse it as the Product user-count mode.
- [`app/utils/admin_hierarchy.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/utils/admin_hierarchy.py), `allowed_child_billing_modes` / `configure_new_child_admin_creation`: Owner may select exactly `USED_TRAFFIC`, `ALLOCATED_TRAFFIC`, `USER_CREDIT` for a new child. Used-traffic parent may create Used and optionally Allocated children if delegated; Allocated→Allocated; User→User. `SEAT_CREDIT` and `LEGACY_COMPAT` remain inherited old-mode branches only, not Owner's new child options. Child role/admin creation permissions and budgets are independently checked. Legacy creation flags are `FREE_FORM/FORM_ONLY`, `PLAN_ONLY` and `BOTH`, not Product authorization.
- [`app/routers/admin.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/routers/admin.py), `GET /admin/capabilities`, `POST /admin-management`, `PUT /admin-management/{username}`: Owner capabilities expose the same three new modes. Managed create rejects `LEGACY_COMPAT` on initialized hierarchy, creates Admin + settings in one transaction, enables monetary billing, starts wallet at zero and optionally grants initial monetary credit via parent/Owner transfer. It validates purchase price per GiB for USED_TRAFFIC but still carries old Plan category/grants, per-Plan child overrides and `user_creation_mode`; USER_CREDIT forcibly gets PLAN_ONLY. Generic managed edit preserves current billing mode; USD usage-price changes check parent-floor/descendant resale; separate owner-only billing transition service is required to change modes. The legacy `POST /admin` creates a raw admin separately and must not silently be treated as the new managed Product path.
- [`app/utils/billing_service.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/utils/billing_service.py), `assign_billing_mode`: Owner-only/idempotent explicit mode change refuses an existing user or nonzero usage/capacity/delegated/renewal state until settlement, avoiding silent reinterpretation. Its allocated-refund flow snapshots Plan IDs and belongs to historical behavior, not the new Product refund formula.
- [`app/db/models.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/db/models.py), `MarzhelpAdminSettings`, `AdminUserPlanVersion`: existing rows default `LEGACY_COMPAT` and monetary billing false; new managed commercial Admin is monetized. Monetary `money_balance_toman` (whole Toman), nullable `used_traffic_price_per_gib_toman`, exact usage remainder, `max_users/user_count_used`, `device_capacity_limit/capacity_used`, `total_traffic/used_traffic`, `calculate_volume` coexist. Legacy PlanVersion currently stores traffic, days, device count and price together; this is NOT the new Product-independent pricing table. No new Product implementation claim is made by this source inspection.
- [`app/utils/marzhelp_policy.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/utils/marzhelp_policy.py), `user_count_used`, `_adjust_user_count`, `capacity_weight`, `quota_summary`, `validate_create`: USER_CREDIT corresponds to actual owned User row count (`max_users`), whereas SEAT_CREDIT corresponds to summed device capacity (`device_capacity_limit`). `_validate_traffic_credit` bypasses byte quotas for these two existing legacy nontraffic modes. Existing quota and subscription checks still run; their new Product semantics must be proven in R06/R16–R18, not assumed.
- [`app/utils/money_billing.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/app/utils/money_billing.py), `charge_plan_purchase` / `PRICED_PLAN_MODES`: USER_CREDIT and ALLOCATED_TRAFFIC currently purchase old Plans using plan price/version and optional per-child price override; USED_TRAFFIC does not pay at Plan purchase and instead settles actual byte usage into a money wallet. This confirms the existing USER_CREDIT purchase path must be DECOUPLED from Plan, replaced by exactly eight Owner-set Product/user-count fixed prices, not multiplied by a traffic formula; the exact future cost ledger is R04/R09/R16–R18 work.

### H2. Tests actually present, not executed in R02

- [`tests/test_stage3_billing_modes.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/tests/test_stage3_billing_modes.py) tests old SEAT_CREDIT finite device cost/no delete refund, old-mode conversion settlement refusal, derived used-byte total through resets, allocated positive increase, reseller usage price floor and refund idempotency; MySQL concurrency refund test is conditional on `TEST_MYSQL_DATABASE_URL`. Their source presence is not Product acceptance and they were NOT_RUN.
- [`tests/test_admin_management.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/tests/test_admin_management.py) has policy/create-in-one-transaction and legacy internal-counter regression tests; [`tests/test_admin_hierarchy_service.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/tests/test_admin_hierarchy_service.py), [`tests/test_monetary_billing_migration.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/tests/test_monetary_billing_migration.py) and [`tests/test_stage5_restricted_creation_namespace.py`](https://github.com/smorad3363/Marzban-v1/blob/bd650070011151eb88c2e2c5e5db783b58ac96e8/tests/test_stage5_restricted_creation_namespace.py) are confirmed present for later focused review. Do not claim they test new fixed eight-price matrix or new Product eligibility.

### H3. Implementation boundary, unresolved semantic and status

- Confirmed target mapping: **new admin-count commercial mode is `USER_CREDIT`**, not old `SEAT_CREDIT`. Each existing USER_CREDIT user account consumes one account slot; whether the new package labels `1/2 seats` denote number of accounts or concurrent sessions/devices must be matched to B09's customer-facing definition in R06, not inferred from the word `seat`. This does not block R03 reconnaissance or change the user-confirmed independent eight prices.
- New Owner Product must replace Plan commercial entitlements in new paths; do not remove legacy Plan tables, repurpose old `device_capacity_limit`, change billing mode on populated accounts or drop history. Product access/group authorization, proration, duration and seat pricing are not yet implemented or verified here; detailed design deferred to R05–R09.
- R02 change intent: ONLY update the current ledger's recovery state, stage row, next action, and append this H audit; prior blob SHA `1c2d9c262c78a4cac474f258dc3e10617a32b4d6`. No source code, tests, migrations, workflow, VERSION, main, PR, release, tag or dispatch changed by this stage. Product tests `NOT_RUN`; local worktree/diff-check `UNKNOWN/NOT_AVAILABLE`. Verify remote readback/compare and exact new SHA check runs before asserting successful documentation checkpoint. Next stage: **R03 lifecycle map only**.
