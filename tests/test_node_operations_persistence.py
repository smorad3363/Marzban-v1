from datetime import datetime, timedelta
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Node
from app.db.node_operations import (
    create_node_event,
    purge_node_operations_before,
    record_traffic_bucket,
    sanitize_event_metadata,
    sanitize_event_text,
    traffic_window_average,
)
from app.db.node_operations_models import NodeEvent, NodeTrafficBucket
from app.models.node import NodeStatus


def _session():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    node = Node(
        name="node-ops-test",
        address="127.0.0.2",
        port=62050,
        api_port=62051,
        status=NodeStatus.connected,
    )
    db.add(node)
    db.commit()
    return engine, db, node


def test_node_event_runtime_identity_deduplicates_replays_and_sanitizes():
    engine, db, node = _session()
    try:
        occurred_at = datetime(2026, 9, 9, 12, 0, 0)
        event, created = create_node_event(
            db,
            node_id=node.id,
            event_type="reconnect_failed",
            source="runtime",
            occurred_at=occurred_at,
            severity="error",
            reason_code="connection_refused",
            trigger_reason="heartbeat_timeout",
            message="Bearer very-secret-token password=hunter2",
            runtime_stream_id="stream-1",
            runtime_event_id=12,
            metadata={
                "attempt": 2,
                "api_token": "must-not-survive",
                "nested": {"private_key": "must-not-survive"},
            },
        )
        replay, replay_created = create_node_event(
            db,
            node_id=node.id,
            event_type="reconnect_failed",
            source="runtime",
            occurred_at=occurred_at,
            runtime_stream_id="stream-1",
            runtime_event_id=12,
        )
        db.commit()

        assert created is True
        assert replay_created is False
        assert replay.id == event.id
        assert db.query(NodeEvent).count() == 1
        assert "very-secret-token" not in event.sanitized_message
        assert "hunter2" not in event.sanitized_message
        assert event.metadata_json["api_token"] == "[REDACTED]"
        assert event.metadata_json["nested"]["private_key"] == "[REDACTED]"
    finally:
        db.close()
        engine.dispose()


def test_sanitizers_bound_diagnostic_data_without_exposing_private_material():
    private_pem = (
        "-----BEGIN PRIVATE KEY-----\nsecret-material\n"
        "-----END PRIVATE KEY-----"
    )
    assert "secret-material" not in sanitize_event_text(private_pem)
    sanitized = sanitize_event_metadata(
        {
            "certificate_fingerprint": "AA:BB:CC",
            "authorization": "Bearer abc",
            "values": list(range(80)),
        }
    )
    assert sanitized["certificate_fingerprint"] == "AA:BB:CC"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["values"][-1] == "[TRUNCATED]"


def test_traffic_samples_accumulate_in_minute_bucket_and_average_by_sample_time():
    engine, db, node = _session()
    try:
        first = datetime(2026, 9, 9, 12, 0, 5)
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=first,
            uplink_bytes=1_000,
            downlink_bytes=2_000,
            sample_seconds=10.0,
        )
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=first + timedelta(seconds=30),
            uplink_bytes=3_000,
            downlink_bytes=4_000,
            sample_seconds=30.0,
        )
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=first + timedelta(minutes=1),
            uplink_bytes=5_000,
            downlink_bytes=6_000,
            sample_seconds=20.0,
        )
        db.commit()

        rows = (
            db.query(NodeTrafficBucket)
            .filter(NodeTrafficBucket.node_id == node.id)
            .order_by(NodeTrafficBucket.bucket_start.asc())
            .all()
        )
        assert len(rows) == 2
        assert rows[0].uplink_bytes == 4_000
        assert rows[0].downlink_bytes == 6_000
        assert rows[0].sample_seconds == 40.0
        assert rows[0].sample_count == 2

        window = traffic_window_average(
            db,
            node_id=node.id,
            from_time=datetime(2026, 9, 9, 11, 0, 0),
            to_time=datetime(2026, 9, 9, 13, 0, 0),
        )
        assert window["uplink_bytes"] == 9_000
        assert window["downlink_bytes"] == 12_000
        assert window["sample_seconds"] == 60.0
        assert window["sample_count"] == 3
        assert window["uplink_bps"] == 1_200.0
        assert window["downlink_bps"] == 1_600.0
        assert window["total_bps"] == 2_800.0
    finally:
        db.close()
        engine.dispose()


def test_retention_cleanup_is_bounded():
    engine, db, node = _session()
    try:
        old = datetime(2026, 1, 1, 0, 0, 0)
        for event_id in range(1, 4):
            create_node_event(
                db,
                node_id=node.id,
                event_type="error",
                source="master",
                occurred_at=old,
                runtime_stream_id="old-stream",
                runtime_event_id=event_id,
            )
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=old,
            uplink_bytes=100,
            downlink_bytes=200,
            sample_seconds=30,
        )
        db.commit()

        deleted_events, deleted_traffic = purge_node_operations_before(
            db,
            event_before=datetime(2027, 2, 1),
            traffic_before=datetime(2026, 2, 1),
            batch_size=2,
        )
        db.commit()
        assert deleted_events == 2
        assert deleted_traffic == 1
        assert db.query(NodeEvent).count() == 1
        assert db.query(NodeTrafficBucket).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_node_operations_migration_chains_from_verified_head_and_has_required_indexes():
    migration = Path(
        "app/db/migrations/versions/a4c2e1f8b7d9_add_node_operations_telemetry.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "a4c2e1f8b7d9"' in migration
    assert 'down_revision = "e7b1c4d9a213"' in migration
    for index_name in (
        "ix_node_events_node_occurred",
        "ix_node_events_type_occurred",
        "ix_node_events_severity_occurred",
        "ix_node_events_received",
        "ix_node_traffic_node_bucket",
        "ix_node_traffic_bucket_start",
    ):
        assert index_name in migration
