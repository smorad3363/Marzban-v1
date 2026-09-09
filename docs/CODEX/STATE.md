# V1 Continuation State

## Active Task: Node Operations V2

- Working branch: `feat/node-operations-v2`
- Base/main SHA at task start: `59bdb0dd2b65435a5e3f774b5ebd4f8186217906`
- Stable release invariant: `v1.1.6` MUST remain at `b6056e3e3f91828a18c39ea71df8252608562216`; do not move or recreate the tag.
- Draft PR: `#37` (`feat: Node Operations V2`).
- Release policy: do not tag/release/publish a new stable version unless explicitly requested by the user.

## Status

AUDIT, PERSISTENCE, AUTHORITATIVE TRAFFIC COLLECTOR, STRUCTURED RUNTIME V2 EVENTS, AND RECONNECT OBSERVABILITY ARE VERIFIED. ADDITIVE NODE OPERATIONS READ API IS IMPLEMENTED IN THE CHECKPOINT COMMIT CONTAINING THIS FILE; CI FOR THAT API MILESTONE MUST BE VERIFIED NEXT.

## Verified Milestones

### Persistence

- Commit family through `0b08dfd33b1e1edd406497673bac65438d34e4b8`.
- Added `node_events`, `node_traffic_buckets`, migration `a4c2e1f8b7d9`, sanitization, replay dedupe, traffic aggregation/history, bounded retention, and focused tests.
- PR CI `34342797216`: completed / success on MySQL 8.0, MySQL 26.7.0, dashboard parity, installer/image/mTLS gates.

### Authoritative traffic collector

- Commit `effc46ce1edc92f718e6b792948808fc66ca6bcd`.
- `app/jobs/record_usages.py` remains the sole Xray `get_outbounds_stats(reset=True)` collection path.
- Durable Node Operations traffic uses the same successful samples and actual elapsed time from `BandwidthStore.observe`; no extra polling and no invented warm-up/long-gap rates.
- Zero-traffic successful intervals are retained for correct durable average denominators.
- Legacy accounting writes happen before isolated telemetry persistence so telemetry failures cannot lose already-reset accounting deltas.
- PR CI `34345274081`: completed / success on all primary gates.

### Structured Runtime V2 events

- Production commit `777ab79ca913b690a01a8a8f4012063c8c1936a7`; compatibility-test fix `b1072e5da4986821f9e8a7ed13bbfbb420422cb4`; prior state commit `089a97184427f9386e30508d8bef0d770cb9fa3d`.
- `structured_events_v1` is optional; required V2 capabilities remain unchanged for old-runtime compatibility.
- Stable persisted runtime stream identity plus monotonic event IDs provide replay dedupe.
- Lifecycle/session events use the existing bounded durable spool; `xray.log` delivery remains intact.
- Master consumer persists/dedupes, commits, then ACKs; failed persistence means no ACK/replay remains possible.
- CI `34346476158`: completed / success across MySQL 8.0, MySQL 26.7.0, dashboard parity, installer/image runtime and Panel-to-Node mTLS.

### Reconnect observability

- Commit `dea535fac615f5d68fa27d852174309d2f2c019d`.
- `app/xray/operations.py` remains the only connection/reconnect engine.
- Attempt/success/failure events persist best-effort reconnect mode, attempt number, trigger/reason, state transition, root cause and best-known downtime.
- Manual Admin reconnect is explicitly `manual`; watchdog retries are `automatic`; internal fallback stays `system`.
- Existing exponential watchdog backoff remains owner; bounded jitter was added without introducing a second scheduler/engine.
- Transport replacement during retry preserves outage start; actual Node removal clears it.
- Telemetry persistence failure cannot block reconnect.
- Added `tests/test_node_reconnect_observability.py` for jitter bounds, outage preservation, automatic/manual call sites and best-effort persistence.
- CI `34347738056` initially failed only because the external Xray `releases/latest` download returned a truncated/non-zip 157 KB payload during release-image build. No Dockerfile/code change was made for this transient failure.
- The failed installer job was rerun on the exact same commit. The rerun completed success, including release-image build, runtime contract and Panel-to-Node mTLS; MySQL 8.0/26.7.0 and dashboard parity were also success. Final workflow conclusion: success.

## Additive Node Operations Read API: Implemented, CI Pending

Files in this checkpoint:

- `app/models/node.py`
  - additive response models for traffic averages, unified Node operations summary, bounded history points and sanitized event timeline.
- `app/routers/node.py`
  - `GET /api/nodes/operations`: Node list summaries from DB telemetry plus the existing `bandwidth_store` only, including derived operational state and persisted 1h/24h averages.
  - `GET /api/node/{node_id}/operations/history`: bounded/downsampled persisted traffic history; no Xray call.
  - `GET /api/node/{node_id}/events`: paginated/filterable sanitized event timeline.
  - existing `/api/nodes`, `/api/nodes/bandwidth`, `/api/nodes/usage`, reconnect and Node CRUD routes remain available.
  - richer `healthy|degraded|reconnecting|offline|disabled` state is derived at response time; DB transport status remains unchanged.
- `tests/test_node_operations_api.py`
  - summary uses live cache + persisted averages,
  - history is bounded and keeps time ordering/endpoints,
  - event diagnostics remain sanitized,
  - richer operational state is derived without a new transport status.

No additional reset-counter polling, Node network requests, Plan/Access Group changes, Admin-accounting changes, or release/version changes are part of this API milestone.

## Verified Architecture / Invariants

- `app/xray/operations.py` remains the single connection/reconnect control path.
- `app/jobs/node_watchdog.py` owns automatic reconnect/backoff.
- DB transport status remains `connected|connecting|error|disabled`; richer health is derived from transport state plus telemetry/live cache.
- `app/jobs/record_usages.py` stays the authoritative reset-counter collector; `app/utils/bandwidth.py` stays the only live bandwidth cache.
- Preserve v1.1.6 Dashboard/Users split and Admin self-accounting privacy, v1.1.5 safe Admin retirement, Plan/Access Group behavior, both MySQL gates, dashboard parity, installer/image runtime, and Panel-to-Node mTLS.
- Keep `/nodes/usage` for API compatibility until the unified frontend is complete.
- Node installer already isolates Panel/Node credentials and validates PEM; add diagnostics/doctor rather than redesigning certificate ownership.

## Last Work File

`tests/test_node_operations_api.py`

On resume, fetch and review this file first, then verify branch HEAD and the CI run attached to the checkpoint commit containing this state file before editing more production code.

## NEXT EXACT TASK

1. Verify CI for the additive Node Operations API checkpoint to completion.
2. If it fails, inspect the exact failing job/log and fix only that regression; update this state at the failure/fix boundary.
3. If it succeeds, mark the API milestone verified.
4. Re-discover and fetch the exact unified frontend `NodesManagementWorkspace` path from the current tree.
5. Update the existing Node workspace to consume `/nodes/operations`, lazy-load persisted history/events for the details surface, add real 1h/24h averages/sorting/operational detail, and remove the separate Nodes Usage UI action only after the unified surface is functional. Keep the backend `/nodes/usage` route for compatibility.
6. Verify dashboard source build and committed build parity before moving to installer `doctor`/diagnostics.
7. Then add installer `doctor`/diagnostics, docs and final full regression/CI gates.

## Recovery Rule

When the user says `ادامه بده` or work resumes after interruption:

1. Fetch `docs/CODEX/STATE.md` from `feat/node-operations-v2`.
2. Fetch and review `Last Work File` before editing anything else.
3. Verify branch HEAD and any CI/run named or implied by the current checkpoint.
4. Execute `NEXT EXACT TASK` from the first incomplete item.
5. After every meaningful milestone or failure/fix boundary, record the exact last file, commit/run IDs, verified results, failures, and next exact action here.
