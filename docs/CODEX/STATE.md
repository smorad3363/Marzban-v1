# V1 Continuation State

## Active Task: Node Operations V2

- Working branch: `feat/node-operations-v2`
- Base/main SHA at task start: `59bdb0dd2b65435a5e3f774b5ebd4f8186217906`
- Stable release invariant: `v1.1.6` MUST remain at `b6056e3e3f91828a18c39ea71df8252608562216`; do not move or recreate the tag.
- Release workflow verified before this task: `34339151023` succeeded.
- Latest main CI verified before this task: `34339215039` succeeded.
- Draft PR: `#37` (`feat: Node Operations V2`).
- Release policy: do not create a Git tag, GitHub Release, or publish a new stable version unless the user explicitly requests publication.

## Status

AUDIT COMPLETE. PERSISTENCE MILESTONE IMPLEMENTED AND VERIFIED. NEXT MILESTONE: AUTHORITATIVE COLLECTOR INTEGRATION + STRUCTURED EVENT INGESTION.

Current verified branch HEAD before this checkpoint: `0b08dfd33b1e1edd406497673bac65438d34e4b8`.

## Completed Milestone: Persistence

Implemented:

- `app/db/node_operations_models.py`
  - `node_events`: structured/sanitized operational events with runtime replay identity, reconnect fields, safe metadata, and node/time/type/severity/retention indexes.
  - `node_traffic_buckets`: one-minute durable traffic buckets with node/time indexes and unique node+bucket identity.
- `app/db/migrations/versions/a4c2e1f8b7d9_add_node_operations_telemetry.py`
  - revises verified head `e7b1c4d9a213`.
  - creates both tables/indexes and has a clean downgrade.
- `app/db/node_operations.py`
  - bounded text/metadata sanitization.
  - runtime replay dedupe.
  - event listing/filtering.
  - traffic bucket accumulation and average/history queries.
  - bounded retention purge helper.
- `tests/test_node_operations_persistence.py`
  - sanitization, dedupe, traffic aggregation/average, bounded retention, migration chain/index contracts.

Verification:

- PR CI run `34342797216` for HEAD `0b08dfd33b1e1edd406497673bac65438d34e4b8`: `completed / success`.
- `dashboard build and parity`: success.
- `backend checkpoints (mysql:8.0)`: success, including backend regression, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore and rollback compatibility.
- `backend checkpoints (mysql:26.7.0)`: success with the same gates.
- `installer, panel compose and node contracts`: success, including installer contracts, 8.0->26.7 restore, release image runtime contract and Panel-to-Node mTLS.
- A retention test bug found during self-review was corrected in commit `0b08dfd33b1e1edd406497673bac65438d34e4b8`; retention is intentionally based on event `received_at`, not runtime-provided `occurred_at`.

## Verified Architecture Findings

### Transport and reconnect

- `app/xray/operations.py` is the single connection/reconnect control path. Do not create a second reconnect engine.
- `app/jobs/node_watchdog.py` already performs automatic reconnect with bounded exponential backoff; it lacks persisted attempts/results/downtime and jitter.
- Existing transport status remains `connected|connecting|error|disabled`. Operational health/reconnecting/degraded views must be derived from transport state plus recent events/telemetry rather than a contradictory second DB status column.

### Runtime V2 and reliable delivery

- `app/xray/node_protocol_v2.py` owns protocol/version handshake validation and capability negotiation.
- Existing V2 delivery already uses monotonic event IDs, duplicate filtering, bounded batches, and ACK-after-success semantics.
- `node_runtime/events.py` provides a durable bounded SQLite/WAL event spool with independent consumer cursors and dropped-event accounting.
- `node_runtime/service.py` exposes V2 handshake/session/control/events/ack endpoints.
- `node_runtime/core.py` currently emits raw `xray.log` spool events only; structured lifecycle/service-health events are the missing extension point.
- New runtime capabilities must be optional so old Node runtimes continue to connect and provide basic status.

### Traffic

- `app/jobs/record_usages.py` is the authoritative reset-counter collector. `get_outbounds_stats(reset=True)` must remain the only reset-counter collection path.
- `app/utils/bandwidth.py` is the existing bounded live-rate store and must remain the only live bandwidth cache.
- Durable traffic buckets must be written from the successful samples already collected by `record_node_usages()`; never poll Xray separately.
- Existing `NodeUsage` hourly accounting remains compatible and unchanged.

### Frontend

- Actual Node frontend files include `NodesManagementWorkspace.tsx`, `NodeBandwidthPanel.tsx`, `NodesUsage.tsx`, `Header.tsx`, `NodesContext.tsx`, and `DashboardContext.tsx`.
- `NodesManagementWorkspace` already has compact list/search/filter/pagination and a temporary in-session sparkline.
- Missing required capabilities are durable history, real 1h/24h averages, sort, operational health/error/reconnect detail, event timeline, and a Details Drawer.
- Keep old `/nodes/usage` endpoint temporarily for API compatibility; remove the separate UI action only after the unified surface is functional.

### Installer

- Panel and Node install/runtime paths are already isolated.
- Certificate flow already validates PEM and does not place the Panel private key on Node.
- Node CLI supports `install|update|status|logs`; `doctor` remains to be added.

## Invariants To Preserve

- v1.1.6 Dashboard/Users split and Admin self-information privacy.
- v1.1.5 safe Admin retirement/delete behavior.
- Plan and Access Group authorization/network ownership behavior.
- MySQL 8.0 and 26.7.0 migration/rollback gates.
- Installer, dashboard source/build parity, release-image runtime contract, and Panel-to-Node mTLS gates.
- Existing Node Runtime V2, certificate model, bandwidth collector, reconnect path, and authorization patterns unless a verified defect requires a scoped change.

## Last Work File

`app/jobs/record_usages.py`

Before resuming after any interruption, fetch and review this file first, then verify branch HEAD/CI and read this state again if HEAD moved.

## NEXT EXACT TASK

1. Integrate durable `node_traffic_buckets` writes into the existing `record_node_usages()` success path without any additional Xray polling or accounting counter resets.
2. Use actual collector elapsed time from the existing bandwidth observation path; do not invent rates for warm-up/long-gap samples.
3. Add bounded retention scheduling/config using existing scheduler/config conventions.
4. Extend focused bandwidth/Node Operations tests for collector integration, failed-sample behavior and no-double-poll semantics.
5. Verify PR CI on the resulting HEAD.
6. Then extend Runtime V2 with optional structured lifecycle/health events and add master-side ACK-after-persist ingestion before reconnect observability/API/frontend work.
7. Update this file after every milestone with the last edited/reviewed file, exact verification, failures and the next action.

## Recovery Rule

When resuming this task (including after the user says `ادامه بده`):

1. Fetch `docs/CODEX/STATE.md` from `feat/node-operations-v2`.
2. Fetch and review `Last Work File` before editing anything else.
3. Verify branch HEAD and inspect changes since this checkpoint.
4. Execute `NEXT EXACT TASK`.
5. After each meaningful milestone, record the last source file edited/reviewed, commands or CI actually run, validation results, failures, and the next exact action here.
