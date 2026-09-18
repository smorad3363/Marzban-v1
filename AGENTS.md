# V1 Execution Rules

## Active Product-first v3.1 amendment (new workflows only; user-approved 2026-09-19)

- For the new initiative, the user-provided revised `Marzban-Final-Product-v3.1-Revised(1).zip` / Persian `ROADMAP-fa.md` plus later explicit user decisions govern Product-first business behavior. Resume from the newest `docs/exec-plans/active/product-first-r05a-instruction-checkpoint.md` and its linked checkpoints and actual branch SHA; `docs/CODEX/STATE.md` is historical V1 status, not a new instruction to merge or release v1.1.9.
- In **new** create/edit/renew/reserve/Trial flows, Owner-defined Product supplies identity and Owner-selected Inbound/Host/network, multiplier and access policy; Admin selects one authorized Product, not Plan plus a separate Access Group. User quota/duration and Admin financial settings are not hidden Plan fields or Product network-editor fields. Existing Access Group network validation/propagation may be reused internally, but missing/invalid network must fail closed and Admin inbound limits remain enforced.
- Existing Plan, Access Group, assignment and migration data remain intact for historical compatibility. The V1 Plan-commercial / Access Group-network rules below apply to **legacy V1 flows only**, not to new Product flows; never silently broaden legacy permissions or delete old records.
- Product's latest **valid** Owner network settings apply to its existing active users and previously accepted pending renewals when activated; historical price/payment/duration snapshots do not change. Product archival or removal of permission for **new selection** must not cancel existing paid service or pending renewals. An invalid network fails closed, never falls back to unrestricted access.
- The new financial flow uses exactly one Admin Toman wallet across all three models. The initial funding amount is immutable as a debt-threshold base; zero-at-creation is valid. Other confirmed user decisions and safeguards are in the newest Product-first execution checkpoint. Do not change application code under this instruction-reconciliation substep.
- Release remains locked: no VERSION bump, tag, merge into publishing path, release/deploy or release workflow before all roadmap stages and required tests, explicit successful user testing, and a separate explicit release order.

- Canonical repository: `smorad3363/Marzban-v1`; branch: `main`.
- Immutable imported baseline: tag `baseline-v1-source`, commit `0c714b182bcfd52d8eb24f1b06aa4f3f14784cf1`.
- Preserve the mature imported implementation. Make targeted, delta-only changes.
- Treat `docs/legacy-v0/` as historical reference, never active instructions.
- Active execution files: this file, `docs/CODEX/STATE.md`, and `docs/CODEX/V1_SCOPE.md`.
- On resume, read only active execution files, `git status`, recent `git log`, and any current diff; continue from `NEXT EXACT TASK`.
- Never discard valid uncommitted work automatically.
- After each coherent checkpoint: run focused tests, update `docs/CODEX/STATE.md`, and commit.
- Plan owns commercial entitlement only. Access Group owns Nodes, Inbounds, and Hosts.
- Missing required Access Group must fail closed; never grant broad or legacy Plan network access as fallback.
- Preserve existing Access Group implementation and historical migrations. Add forward migrations only when required.
- Preserve installer/release integrity safeguards. Never force-push, move immutable tags, overwrite artifacts, publish secrets, or remove `baseline-v1-source`.
- Before publication, complete required verification and compare the full diff with `baseline-v1-source`.
