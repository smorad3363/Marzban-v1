from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.db.base import Base


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class NodeEvent(Base):
    __tablename__ = "node_events"
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "runtime_stream_id",
            "runtime_event_id",
            name="uq_node_events_runtime_identity",
        ),
        Index("ix_node_events_node_occurred", "node_id", "occurred_at", "id"),
        Index("ix_node_events_type_occurred", "event_type", "occurred_at", "id"),
        Index(
            "ix_node_events_severity_occurred",
            "severity",
            "occurred_at",
            "id",
        ),
        Index("ix_node_events_received", "received_at", "id"),
    )

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    node_id = Column(
        Integer,
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, nullable=False, default=utc_now_naive)
    event_type = Column(String(48), nullable=False)
    severity = Column(String(16), nullable=False, default="info")
    reason_code = Column(String(64), nullable=True)
    trigger_reason = Column(String(64), nullable=True)
    root_cause = Column(String(64), nullable=True)
    source = Column(String(32), nullable=False)
    sanitized_message = Column(String(1024), nullable=True)
    previous_state = Column(String(32), nullable=True)
    new_state = Column(String(32), nullable=True)
    reconnect_mode = Column(String(16), nullable=True)
    reconnect_attempt = Column(Integer, nullable=True)
    reconnect_result = Column(String(16), nullable=True)
    downtime_seconds = Column(Integer, nullable=True)
    runtime_version = Column(String(64), nullable=True)
    runtime_stream_id = Column(String(64), nullable=True)
    runtime_event_id = Column(BigInteger, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)


class NodeTrafficBucket(Base):
    __tablename__ = "node_traffic_buckets"
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "bucket_start",
            name="uq_node_traffic_node_bucket",
        ),
        Index(
            "ix_node_traffic_node_bucket",
            "node_id",
            "bucket_start",
            "id",
        ),
        Index("ix_node_traffic_bucket_start", "bucket_start", "id"),
    )

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    node_id = Column(
        Integer,
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    bucket_start = Column(DateTime, nullable=False)
    uplink_bytes = Column(BigInteger, nullable=False, default=0)
    downlink_bytes = Column(BigInteger, nullable=False, default=0)
    sample_seconds = Column(Float, nullable=False, default=0.0)
    sample_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=utc_now_naive,
        onupdate=utc_now_naive,
    )
