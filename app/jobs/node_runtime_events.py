import logging
from concurrent.futures import ThreadPoolExecutor

from app import scheduler, xray
from app.db import GetDB
from app.db.node_runtime_events import persist_runtime_event_batch
from config import XRAY_STATS_MAX_WORKERS


logger = logging.getLogger(__name__)
_CONSUMER_ID = "node-operations"


def _ingest_node_runtime_events(node_id: int, node) -> None:
    handshake = getattr(node, "runtime_handshake", None)
    if (
        handshake is None
        or not getattr(handshake, "supports_structured_events", False)
        or not getattr(node, "_session_id", None)
    ):
        return

    events, highest_seen = node._event_batch(_CONSUMER_ID, 0, limit=100)
    if not events:
        return

    with GetDB() as db:
        persist_runtime_event_batch(
            db,
            node_id=node_id,
            runtime_version=getattr(handshake, "runtime_version", None),
            stream_id=handshake.event_stream_id,
            events=events,
        )
        db.commit()

    # ACK is deliberately after the durable commit. If persistence or commit
    # fails, this line is never reached and the runtime replays the batch.
    if highest_seen > 0:
        node._ack_event_batch(_CONSUMER_ID, highest_seen)


def ingest_node_runtime_events() -> None:
    candidates = [
        (node_id, node)
        for node_id, node in list(xray.nodes.items())
        if getattr(getattr(node, "runtime_handshake", None), "supports_structured_events", False)
        and getattr(node, "_session_id", None)
    ]
    if not candidates:
        return

    workers = max(1, min(len(candidates), int(XRAY_STATS_MAX_WORKERS)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_ingest_node_runtime_events, node_id, node)
            for node_id, node in candidates
        ]
        for future in futures:
            try:
                future.result()
            except Exception as exc:
                logger.warning("Node runtime event ingestion failed: %s", exc)


scheduler.add_job(
    ingest_node_runtime_events,
    "interval",
    seconds=5,
    coalesce=True,
    max_instances=1,
    id="node-runtime-events",
    replace_existing=True,
)
