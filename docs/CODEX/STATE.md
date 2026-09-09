# V1 Continuation State

## Active Task: Node Operations V2

- Working branch: `feat/node-operations-v2`
- Base/main SHA at task start: `59bdb0dd2b65435a5e3f774b5ebd4f8186217906`
- Stable release invariant: `v1.1.6` MUST remain at `b6056e3e3f91828a18c39ea71df8252608562216`; do not move or recreate the tag.
- Draft PR: `#37` (`feat: Node Operations V2`).
- Release policy: do not tag/release/publish a new stable version unless explicitly requested by the user.

## Status

AUDIT, PERSISTENCE, AND AUTHORITATIVE TRAFFIC COLLECTOR MILESTONES ARE VERIFIED. STRUCTURED RUNTIME V2 EVENTS ARE IMPLEMENTED; ONE COMPATIBILITY TEST FAILURE WAS FIXED AND CI RUN 179 IS CURRENTLY EXECUTING.

Current branch HEAD after the compatibility fix: `b1072e5da4986821f9e8a7ed13bbfbb420422cb4`.

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
- Added bounded/configurable Node Operations retention job/config.
- PR CI `34345274081`: completed / success on all four checkpoint jobs, including both MySQL versions, dashboard parity, installer, release-image runtime, and Panel-to-Node mTLS.

## Structured Runtime V2 Milestone: Implemented, Reverification Pending

Implementation commit: `777ab79ca913b690a01a8a8f4012063c8c1936a7`.

Implemented:

- `structured_events_v1` is an OPTIONAL capability; existing required V2 capabilities remain unchanged so old V2 runtimes remain compatible.
- Runtime event spool now has a stable persisted `event_stream_id` used with monotonic event IDs for master-side replay dedupe.
- Runtime handshake advertises the optional structured-events capability and stream identity.
- Runtime emits structured lifecycle/session events on the existing bounded durable spool; existing `xray.log` delivery remains intact.
- Master-side `app/jobs/node_runtime_events.py` uses a separate consumer ID, persists/dedupes a batch, commits, and only then ACKs. Persistence/commit failure means no ACK and the runtime replays.
- Structured runtime payloads flow through the existing sanitization layer before DB storage.

Verification history:

- CI `34345964590` on `777ab79c...` failed only in the backend regression suite on both MySQL matrix jobs; dashboard and installer/image/mTLS were successful.
- Exact failure: `tests/test_v102_node_runtime.py::test_runtime_api_requires_session_and_persists_ack_cursor` assumed the general typed V2 event endpoint contained only two `xray.log` rows. The new `runtime.session.connected` event correctly appeared before them, producing `[1,2,3]` instead of `[2,3]`.
- Production code was not changed for this failure. Commit `b1072e5da4986821f9e8a7ed13bbfbb420422cb4` changed only `tests/test_v102_node_runtime.py` (+4/-1) so the legacy test filters typed events and still verifies both log IDs plus the structured session event.
- CI run `34346374172` (run 179) is executing for `b1072e5d...`; do not call this milestone verified until it completes success.

## Verified Architecture / Invariants

- `app/xray/operations.py` remains the single connection/reconnect control path; do not create another reconnect engine.
- `app/jobs/node_watchdog.py` owns automatic reconnect/backoff. Add observability/jitter there rather than replacing it.
- Existing DB transport status remains `connected|connecting|error|disabled`; derive richer operational health from events/telemetry, not a contradictory second status column.
- `app/jobs/record_usages.py` stays the authoritative reset-counter collector; `app/utils/bandwidth.py` stays the only live bandwidth cache.
- Preserve v1.1.6 Dashboard/Users split and Admin self-accounting privacy, v1.1.5 safe Admin retirement, Plan/Access Group behavior, both MySQL gates, dashboard parity, installer/image runtime, and Panel-to-Node mTLS.
- Keep `/nodes/usage` temporarily for API compatibility until the unified frontend is complete.
- Node installer already isolates Panel/Node credentials and validates PEM; add diagnostics/doctor rather than redesigning certificate ownership.

## Last Work File

`tests/test_v102_node_runtime.py`

On resume, fetch and review this file first, then verify branch HEAD and CI run `34346374172` before editing new production code.

## NEXT EXACT TASK

1. Verify CI run `34346374172` for HEAD `b1072e5da4986821f9e8a7ed13bbfbb420422cb4` to completion.
2. If it fails, inspect the failing job log and fix only that regression; update this state again.
3. If it succeeds, mark structured Runtime V2 milestone verified.
4. Re-review `app/xray/operations.py` and `app/jobs/node_watchdog.py` and implement reconnect observability on the existing engine:
   - persist attempt/success/failure events,
   - distinguish manual vs automatic/system trigger,
   - record attempt number, trigger/reason, state transition, root cause, and downtime when known,
   - add bounded jitter to the existing exponential backoff without changing its ownership model,
   - instrumentation must be best-effort and must never block reconnect.
5. Add focused reconnect tests and verify CI.
6. Then add additive Node Operations API models/routes for unified status, history, averages and event timeline; preserve old endpoints during compatibility window.
7. Then update the unified frontend, installer `doctor`/diagnostics, docs and final regression/CI gates.

## Recovery Rule

When the user says `ادامه بده` or work resumes after interruption:

1. Fetch `docs/CODEX/STATE.md` from `feat/node-operations-v2`.
2. Fetch and review `Last Work File` before editing anything else.
3. Verify branch HEAD and any CI/run named above.
4. Execute `NEXT EXACT TASK` from the first incomplete item.
5. After every meaningful milestone or failure/fix boundary, record the exact last file, commit/run IDs, verified results, failures, and next exact action here.
