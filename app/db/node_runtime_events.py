from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.db.node_operations import create_node_event


def _parse_runtime_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def persist_runtime_event_batch(
    db: Session,
    *,
    node_id: int,
    runtime_version: str | None,
    stream_id: str,
    events: Iterable[Any],
) -> int:
    """Persist one replayable runtime batch; caller owns commit and ACK ordering."""

    persisted = 0
    for event in events:
        if getattr(event, "event_type", None) == "xray.log":
            continue
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            payload = dict(payload or {})
        _event, created = create_node_event(
            db,
            node_id=node_id,
            event_type=str(getattr(event, "event_type", "runtime.unknown")),
            source="runtime",
            occurred_at=_parse_runtime_time(getattr(event, "created_at", None)),
            severity=payload.get("severity") or "info",
            reason_code=payload.get("reason_code"),
            trigger_reason=payload.get("trigger_reason"),
            root_cause=payload.get("root_cause"),
            message=payload.get("message"),
            previous_state=payload.get("previous_state"),
            new_state=payload.get("new_state"),
            reconnect_mode=payload.get("reconnect_mode"),
            reconnect_attempt=payload.get("reconnect_attempt"),
            reconnect_result=payload.get("reconnect_result"),
            downtime_seconds=payload.get("downtime_seconds"),
            runtime_version=runtime_version,
            runtime_stream_id=stream_id,
            runtime_event_id=int(getattr(event, "event_id")),
            metadata=payload.get("metadata"),
        )
        persisted += int(created)
    return persisted
