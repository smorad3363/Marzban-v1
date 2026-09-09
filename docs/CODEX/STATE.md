# V1 Continuation State

## Active Task: Node Operations V2

- Working branch: `feat/node-operations-v2`
- Base/main SHA at task start: `59bdb0dd2b65435a5e3f774b5ebd4f8186217906`
- Stable release invariant: `v1.1.6` MUST remain at `b6056e3e3f91828a18c39ea71df8252608562216`; do not move or recreate the tag.
- Release workflow already verified before this task: `34339151023` succeeded.
- Latest main CI verified before this task: `34339215039` succeeded.
- Task source: end-to-end Node Operations audit and implementation across backend, database, API, Node Runtime V2, traffic/telemetry, reconnect/error observability, frontend, installer/updater, documentation, and tests.
- Release policy for this task: do not create a Git tag, GitHub Release, or publish a new stable version unless the user explicitly requests publication.

## Status

AUDIT IN PROGRESS. No production code has been modified yet.

## Verified Architecture Findings

- Node API models live in `app/models/node.py`.
- Node REST/WebSocket routes live in `app/routers/node.py`.
- Existing node routes include `/nodes`, `/nodes/bandwidth`, `/nodes/usage`, `/node/{node_id}/reconnect`, node settings/watchdog endpoints, and a privileged node-log WebSocket.
- Live bandwidth is served from the existing bounded `bandwidth_store`; do not add a parallel collector.
- Node Runtime V2 protocol lives in `app/xray/node_protocol_v2.py`.
- Runtime V2 already has protocol/version handshake validation, bounded capability negotiation, reliable-event capability requirements, monotonic event IDs, duplicate filtering, and bounded event batches. Extend this protocol rather than creating a second runtime/event subsystem.
- Current runtime capabilities include `control_v1`, `event_ack_v1`, and `client_ip_direct_v1`.
- Prompt names `NodeBandwidthPanel` and `onShowingNodesUsage` were not found on current HEAD; use actual repository names before removing any legacy UI.

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

`app/xray/node_protocol_v2.py`

Before resuming after any interruption, fetch and review this file first, then read this state file again if HEAD moved.

## NEXT EXACT TASK

1. Review `app/xray/node.py` and `app/xray/operations.py` to map heartbeat/event delivery/reconnect and current error/status transitions.
2. Then inspect Node DB models/CRUD/migrations and bandwidth storage to identify the smallest compatible persistence design for structured events and historical traffic.
3. Update this state after the audit milestone before starting schema changes.

## Recovery Rule

When resuming this task (including after the user says `ادامه بده`):

1. Fetch `docs/CODEX/STATE.md` from `feat/node-operations-v2`.
2. Fetch and review `Last Work File` before editing anything else.
3. Verify branch HEAD and inspect any changes since this checkpoint.
4. Execute `NEXT EXACT TASK`.
5. After each meaningful milestone, record the last source file edited/reviewed, commands or CI actually run, validation results, failures, and the next exact action here.
