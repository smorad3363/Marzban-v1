from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.node_operations_models import NodeEvent, NodeTrafficBucket


_SECRET_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "private_key",
    "private-key",
    "ssl_key",
    "database_url",
    "database_uri",
)
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [^-\n]*PRIVATE KEY-----.*?-----END [^-\n]*PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_INLINE_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[^\s,;]+"
)


def _utc_naive(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is not None:
        current = current.astimezone(timezone.utc).replace(tzinfo=None)
    return current


def sanitize_event_text(value: Any, *, max_length: int = 1024) -> str | None:
    if value is None:
        return None
    text = str(value)
    text = _PRIVATE_KEY_RE.sub("[REDACTED_PRIVATE_KEY]", text)
    text = _BEARER_RE.sub("Bearer [REDACTED]", text)
    text = _INLINE_SECRET_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    return text[:max_length]


def _sensitive_metadata_key(key: str) -> bool:
    lowered = key.lower().replace(" ", "_")
    return any(part in lowered for part in _SECRET_KEY_PARTS)


def sanitize_event_metadata(value: Any, *, _depth: int = 0) -> Any:
    """Return a bounded JSON-safe diagnostic structure with secrets removed."""

    if _depth >= 5:
        return "[TRUNCATED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return sanitize_event_text(value, max_length=2048)
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for index, (raw_key, item) in enumerate(value.items()):
            if index >= 64:
                sanitized["_truncated"] = True
                break
            key = str(raw_key)[:128]
            sanitized[key] = (
                "[REDACTED]"
                if _sensitive_metadata_key(key)
                else sanitize_event_metadata(item, _depth=_depth + 1)
            )
        return sanitized
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        sanitized = [
            sanitize_event_metadata(item, _depth=_depth + 1)
            for item in items[:64]
        ]
        if len(items) > 64:
            sanitized.append("[TRUNCATED]")
        return sanitized
    return sanitize_event_text(value, max_length=2048)


def create_node_event(
    db: Session,
    *,
    node_id: int,
    event_type: str,
    source: str,
    occurred_at: datetime | None = None,
    severity: str = "info",
    reason_code: str | None = None,
    trigger_reason: str | None = None,
    root_cause: str | None = None,
    message: str | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    reconnect_mode: str | None = None,
    reconnect_attempt: int | None = None,
    reconnect_result: str | None = None,
    downtime_seconds: int | None = None,
    runtime_version: str | None = None,
    runtime_stream_id: str | None = None,
    runtime_event_id: int | None = None,
    metadata: Any = None,
) -> tuple[NodeEvent, bool]:
    """Create one sanitized event, returning an existing runtime event on replay."""

    if node_id <= 0:
        raise ValueError("node_id must be positive")
    event_type = str(event_type).strip()[:48]
    source = str(source).strip()[:32]
    severity = str(severity).strip().lower()[:16] or "info"
    if not event_type:
        raise ValueError("event_type is required")
    if not source:
        raise ValueError("source is required")
    if runtime_event_id is not None and runtime_event_id <= 0:
        raise ValueError("runtime_event_id must be positive")
    if runtime_stream_id:
        runtime_stream_id = str(runtime_stream_id).strip()[:64] or None
    if runtime_event_id is not None and not runtime_stream_id:
        raise ValueError("runtime_stream_id is required with runtime_event_id")

    if runtime_stream_id and runtime_event_id is not None:
        existing = (
            db.query(NodeEvent)
            .filter(
                NodeEvent.node_id == node_id,
                NodeEvent.runtime_stream_id == runtime_stream_id,
                NodeEvent.runtime_event_id == runtime_event_id,
            )
            .one_or_none()
        )
        if existing is not None:
            return existing, False

    event = NodeEvent(
        node_id=node_id,
        occurred_at=_utc_naive(occurred_at),
        received_at=_utc_naive(),
        event_type=event_type,
        severity=severity,
        reason_code=(str(reason_code).strip()[:64] if reason_code else None),
        trigger_reason=(str(trigger_reason).strip()[:64] if trigger_reason else None),
        root_cause=(str(root_cause).strip()[:64] if root_cause else None),
        source=source,
        sanitized_message=sanitize_event_text(message),
        previous_state=(str(previous_state).strip()[:32] if previous_state else None),
        new_state=(str(new_state).strip()[:32] if new_state else None),
        reconnect_mode=(str(reconnect_mode).strip()[:16] if reconnect_mode else None),
        reconnect_attempt=(max(1, int(reconnect_attempt)) if reconnect_attempt else None),
        reconnect_result=(str(reconnect_result).strip()[:16] if reconnect_result else None),
        downtime_seconds=(max(0, int(downtime_seconds)) if downtime_seconds is not None else None),
        runtime_version=(str(runtime_version).strip()[:64] if runtime_version else None),
        runtime_stream_id=runtime_stream_id,
        runtime_event_id=runtime_event_id,
        metadata_json=sanitize_event_metadata(metadata),
    )
    db.add(event)
    db.flush()
    return event, True


def list_node_events(
    db: Session,
    *,
    node_id: int,
    offset: int = 0,
    limit: int = 50,
    event_type: str | None = None,
    severity: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> tuple[list[NodeEvent], int]:
    query = db.query(NodeEvent).filter(NodeEvent.node_id == node_id)
    if event_type:
        query = query.filter(NodeEvent.event_type == event_type)
    if severity:
        query = query.filter(NodeEvent.severity == severity)
    if from_time:
        query = query.filter(NodeEvent.occurred_at >= _utc_naive(from_time))
    if to_time:
        query = query.filter(NodeEvent.occurred_at <= _utc_naive(to_time))
    total = query.count()
    rows = (
        query.order_by(NodeEvent.occurred_at.desc(), NodeEvent.id.desc())
        .offset(max(0, int(offset)))
        .limit(max(1, min(int(limit), 200)))
        .all()
    )
    return rows, total


def record_traffic_bucket(
    db: Session,
    *,
    node_id: int,
    sampled_at: datetime,
    uplink_bytes: int,
    downlink_bytes: int,
    sample_seconds: float,
) -> NodeTrafficBucket:
    """Accumulate one authoritative collector sample into a one-minute bucket."""

    if node_id <= 0:
        raise ValueError("node_id must be positive")
    if uplink_bytes < 0 or downlink_bytes < 0:
        raise ValueError("traffic byte counters must not be negative")
    if sample_seconds <= 0:
        raise ValueError("sample_seconds must be positive")

    sample_time = _utc_naive(sampled_at)
    bucket_start = sample_time.replace(second=0, microsecond=0)
    bucket = (
        db.query(NodeTrafficBucket)
        .filter(
            NodeTrafficBucket.node_id == node_id,
            NodeTrafficBucket.bucket_start == bucket_start,
        )
        .one_or_none()
    )
    now = _utc_naive()
    if bucket is None:
        bucket = NodeTrafficBucket(
            node_id=node_id,
            bucket_start=bucket_start,
            uplink_bytes=int(uplink_bytes),
            downlink_bytes=int(downlink_bytes),
            sample_seconds=float(sample_seconds),
            sample_count=1,
            created_at=now,
            updated_at=now,
        )
        db.add(bucket)
    else:
        bucket.uplink_bytes = int(bucket.uplink_bytes or 0) + int(uplink_bytes)
        bucket.downlink_bytes = int(bucket.downlink_bytes or 0) + int(downlink_bytes)
        bucket.sample_seconds = float(bucket.sample_seconds or 0.0) + float(sample_seconds)
        bucket.sample_count = int(bucket.sample_count or 0) + 1
        bucket.updated_at = now
    db.flush()
    return bucket


def traffic_window_average(
    db: Session,
    *,
    node_id: int,
    from_time: datetime,
    to_time: datetime,
) -> dict[str, float | int]:
    row = (
        db.query(
            func.coalesce(func.sum(NodeTrafficBucket.uplink_bytes), 0),
            func.coalesce(func.sum(NodeTrafficBucket.downlink_bytes), 0),
            func.coalesce(func.sum(NodeTrafficBucket.sample_seconds), 0.0),
            func.coalesce(func.sum(NodeTrafficBucket.sample_count), 0),
        )
        .filter(
            NodeTrafficBucket.node_id == node_id,
            NodeTrafficBucket.bucket_start >= _utc_naive(from_time),
            NodeTrafficBucket.bucket_start < _utc_naive(to_time),
        )
        .one()
    )
    uplink_bytes = int(row[0] or 0)
    downlink_bytes = int(row[1] or 0)
    sample_seconds = float(row[2] or 0.0)
    sample_count = int(row[3] or 0)
    if sample_seconds <= 0:
        uplink_bps = downlink_bps = 0.0
    else:
        uplink_bps = uplink_bytes * 8.0 / sample_seconds
        downlink_bps = downlink_bytes * 8.0 / sample_seconds
    return {
        "uplink_bytes": uplink_bytes,
        "downlink_bytes": downlink_bytes,
        "sample_seconds": sample_seconds,
        "sample_count": sample_count,
        "uplink_bps": uplink_bps,
        "downlink_bps": downlink_bps,
        "total_bps": uplink_bps + downlink_bps,
    }


def list_traffic_buckets(
    db: Session,
    *,
    node_id: int,
    from_time: datetime,
    to_time: datetime,
    limit: int = 1440,
) -> list[NodeTrafficBucket]:
    return (
        db.query(NodeTrafficBucket)
        .filter(
            NodeTrafficBucket.node_id == node_id,
            NodeTrafficBucket.bucket_start >= _utc_naive(from_time),
            NodeTrafficBucket.bucket_start < _utc_naive(to_time),
        )
        .order_by(NodeTrafficBucket.bucket_start.asc())
        .limit(max(1, min(int(limit), 10080)))
        .all()
    )


def purge_node_operations_before(
    db: Session,
    *,
    event_before: datetime,
    traffic_before: datetime,
    batch_size: int = 5000,
) -> tuple[int, int]:
    """Delete old telemetry in bounded batches; caller owns commit scheduling."""

    size = max(1, min(int(batch_size), 10000))
    event_ids = [
        row[0]
        for row in (
            db.query(NodeEvent.id)
            .filter(NodeEvent.received_at < _utc_naive(event_before))
            .order_by(NodeEvent.id.asc())
            .limit(size)
            .all()
        )
    ]
    traffic_ids = [
        row[0]
        for row in (
            db.query(NodeTrafficBucket.id)
            .filter(NodeTrafficBucket.bucket_start < _utc_naive(traffic_before))
            .order_by(NodeTrafficBucket.id.asc())
            .limit(size)
            .all()
        )
    ]
    if event_ids:
        db.query(NodeEvent).filter(NodeEvent.id.in_(event_ids)).delete(
            synchronize_session=False
        )
    if traffic_ids:
        db.query(NodeTrafficBucket).filter(NodeTrafficBucket.id.in_(traffic_ids)).delete(
            synchronize_session=False
        )
    db.flush()
    return len(event_ids), len(traffic_ids)
