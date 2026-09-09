# V1 Continuation State

## Active Task: Node Operations V2

- Working branch: `feat/node-operations-v2`
- Base/main SHA at task start: `59bdb0dd2b65435a5e3f774b5ebd4f8186217906`
- Stable release invariant: `v1.1.6` MUST remain at `b6056e3e3f91828a18c39ea71df8252608562216`; do not move or recreate the tag.
- Release workflow verified before this task: `34339151023` succeeded.
- Latest main CI verified before this task: `34339215039` succeeded.
- Release policy: do not create a Git tag, GitHub Release, or publish a new stable version unless the user explicitly requests publication.

## Status

AUDIT COMPLETE — BACKEND PERSISTENCE IS THE NEXT IMPLEMENTATION MILESTONE.

No production source code has been modified yet. Only this continuation state has been committed on the task branch.

## Verified Architecture Findings

### Transport and reconnect

- Node REST/WebSocket routes live in `app/routers/node.py` and already expose `/nodes`, `/nodes/bandwidth`, `/nodes/usage`, `/node/{id}/reconnect`, settings/watchdog endpoints, and privileged log streaming.
- `app/xray/operations.py` is the single connection/reconnect control path. Do not create a second reconnect engine.
- `app/jobs/node_watchdog.py` already performs automatic reconnect with bounded exponential backoff; it lacks persisted attempts/results/downtime and jitter.
- Node transport status remains the existing `connected|connecting|error|disabled` model. Operational health/reconnecting/degraded views must be derived from this transport state plus recent persisted events/telemetry rather than creating a contradictory second status column.

### Runtime V2 and reliable delivery

- `app/xray/node_protocol_v2.py` owns protocol/version handshake validation and capability negotiation.
- Current capabilities are `control_v1`, `event_ack_v1`, and `client_ip_direct_v1`.
- Existing V2 delivery already uses monotonic event IDs, duplicate filtering, bounded batches, and ACK-after-success semantics.
- `node_runtime/events.py` provides a durable bounded SQLite/WAL event spool with independent consumer cursors and dropped-event accounting.
- `node_runtime/service.py` exposes V2 handshake/session/control/events/ack endpoints.
- `node_runtime/core.py` currently emits raw `xray.log` spool events only; structured lifecycle/service-health events are the missing extension point.
- New runtime capabilities must be optional so old Node runtimes continue to connect and provide basic status.

### Traffic

- `app/jobs/record_usages.py` is the authoritative reset-counter collector. `get_outbounds_stats(reset=True)` must remain the only reset-counter collection path.
- The existing collector feeds `app/utils/bandwidth.py`, whose in-memory cache is bounded to a short live window and is suitable for instantaneous rates but not durable 1h/24h averages/history.
- Existing `NodeUsage` stores hourly byte totals and must remain compatible.
- Durable Node Operations traffic buckets, if added, must be written from `record_node_usages()` after the existing successful sample is collected; never poll Xray separately.
- Current collection interval defaults to 30 seconds through `JOB_RECORD_NODE_USAGES_INTERVAL`.

### Database and migrations

- Existing Node, NodeUsage, NodeUserUsage and NodeWatchdogSettings models are in `app/db/models.py`.
- `app/db/models.py` is large; focused Node Operations models should use a small dedicated module rather than rewriting unrelated model code.
- Existing architecture already has split model modules such as `app/db/access_group_models.py`.
- Last migration-changing commit on the branch added only revision `e7b1c4d9a213` (`Revises: e1a7c4d9b302`), so `e7b1c4d9a213` is the verified current migration head for the next revision.
- MySQL 8.0 and MySQL 26.7.0 migration, partial-DDL recovery and rollback gates remain mandatory.

### Frontend

- Actual Node frontend files include `NodesManagementWorkspace.tsx`, `NodeBandwidthPanel.tsx`, `NodesUsage.tsx`, `Header.tsx`, `NodesContext.tsx`, and `DashboardContext.tsx`.
- `NodesManagementWorkspace` already has a compact list, summary, search/status filter, refresh, Add Node, client-side pagination, and a temporary in-session sparkline.
- Missing required capabilities are durable history/sparkline, real 1h/24h averages, sort, operational health/error/reconnect detail, event timeline, and a real Details Drawer.
- `NodesUsage.tsx` remains a separate modal backed by `/nodes/usage` and `DashboardContext.isShowingNodesUsage`.
- `Header.tsx` still exposes separate Node Settings and Nodes Usage actions. These must collapse into one Node Operations surface after the merged UI is functional.
- Keep the old `/nodes/usage` endpoint temporarily for API compatibility unless later evidence shows it is safe to remove.

### Installer and certificate model

- Panel paths and Node paths are already isolated: `/opt/marzban` vs `/opt/marzban-node`, `/var/lib/marzban` vs `/var/lib/marzban-node`, and Node CLI `/usr/local/bin/marzban-node`.
- The installer already preserves Panel/Node separation, validates pasted PEM with `openssl x509`, stores only the Panel public client certificate on the Node, and never installs a Panel private key there.
- Existing Node CLI supports `install|update|status|logs`; `doctor` does not exist yet.
- Node update already preserves configuration and a backup on failed health/version verification.

### Tests

- Extend existing Node test families rather than creating a parallel test stack: `test_v102_node_runtime.py`, `test_v102_node_runtime_protocol.py`, `test_v102_resource_bandwidth.py`, `test_node_deployment_contract.py`, `test_node_log_interval.py`, `test_xray_node_state.py`, and `node_panel_e2e.sh`.

## Persistence Design Chosen For First Milestone

Add two focused tables via a new Node Operations models module plus one Alembic revision:

1. `node_events`: structured, sanitized operational events with indexed node/time, type/time and severity/time access; optional runtime session/event identity for deduplication; reconnect fields; trigger/root-cause separation; downtime; safe JSON metadata.
2. `node_traffic_buckets`: lightweight durable traffic samples written only from the existing reset-counter collector. Store bucket time/duration plus uplink/downlink bytes and derived rates. Keep this table bounded with configurable retention and indexed node/time access.

The first API milestone will query these tables additively; existing Node endpoints remain intact for compatibility.

## Invariants To Preserve

- v1.1.6 Dashboard/Users split and Admin self-information privacy.
- v1.1.5 safe Admin retirement/delete behavior.
- Plan and Access Group authorization/network ownership behavior.
- MySQL 8.0 and 26.7.0 migration/rollback gates.
- Installer, dashboard source/build parity, release-image runtime contract, and Panel-to-Node mTLS gates.
- Existing Node Runtime V2, certificate model, bandwidth collector, reconnect path, and authorization patterns unless a verified defect requires a scoped change.

## Tests Run For This Branch

- None yet. Audit only.

## Last Work File

`app/jobs/record_usages.py`

Before resuming after any interruption, fetch and review this file first, then read this state file again if HEAD moved.

## NEXT EXACT TASK

1. Create the focused Node Operations database models module for `node_events` and `node_traffic_buckets`.
2. Create one Alembic migration revising `e7b1c4d9a213`, with MySQL-safe indexes/constraints and a clean downgrade.
3. Add focused persistence/query helpers without rewriting `app/db/crud.py`.
4. Add regression tests for schema/index/dedupe behavior and run/confirm the branch CI triggered by the milestone commit.
5. Update this state with the exact last edited file and next action before moving to collector/event ingestion.

## Recovery Rule

When resuming this task (including after the user says `ادامه بده`):

1. Fetch `docs/CODEX/STATE.md` from `feat/node-operations-v2`.
2. Fetch and review `Last Work File` before editing anything else.
3. Verify branch HEAD and inspect changes since this checkpoint.
4. Execute `NEXT EXACT TASK`.
5. After each meaningful milestone, record the last source file edited/reviewed, commands or CI actually run, validation results, failures, and the next exact action here.
