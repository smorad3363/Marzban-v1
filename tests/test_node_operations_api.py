from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Node
from app.db.node_operations import create_node_event, record_traffic_bucket
from app.models.node import NodeStatus
from app.routers import node as node_router


def _session():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    node = Node(
        name="ops-api-node",
        address="127.0.0.2",
        port=62050,
        api_port=62051,
        status=NodeStatus.connected,
        xray_version="26.7.28",
    )
    db.add(node)
    db.commit()
    return engine, db, node


def _live_snapshot():
    return {
        "state": "online",
        "sampled_at": datetime.now(timezone.utc),
        "sample_age_seconds": 1.0,
        "uplink_bps": 4_000.0,
        "downlink_bps": 8_000.0,
        "peak_5m_uplink_bps": 5_000.0,
        "peak_5m_downlink_bps": 9_000.0,
    }


def test_nodes_operations_summary_uses_live_cache_and_persisted_averages_only(monkeypatch):
    engine, db, node = _session()
    try:
        now = datetime.now(timezone.utc)
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=now - timedelta(minutes=20),
            uplink_bytes=1_000,
            downlink_bytes=2_000,
            sample_seconds=10,
        )
        record_traffic_bucket(
            db,
            node_id=node.id,
            sampled_at=now - timedelta(hours=2),
            uplink_bytes=9_000,
            downlink_bytes=9_000,
            sample_seconds=90,
        )
        db.commit()

        snapshot_calls = []
        monkeypatch.setattr(
            node_router.bandwidth_store,
            "snapshot",
            lambda node_id: snapshot_calls.append(node_id) or _live_snapshot(),
        )

        response = node_router.get_nodes_operations(db=db, _=object())

        assert snapshot_calls == [node.id]
        assert len(response.nodes) == 1
        row = response.nodes[0]
        assert row.operational_state == "healthy"
        assert row.live.total_bps == 12_000.0
        assert row.average_1h.uplink_bps == 800.0
        assert row.average_1h.downlink_bps == 1_600.0
        assert row.average_24h.uplink_bps == 800.0
        assert row.average_24h.downlink_bps == 880.0
    finally:
        db.close()
        engine.dispose()


def test_history_is_bounded_and_keeps_first_and_latest_persisted_samples():
    engine, db, node = _session()
    try:
        now = datetime.now(timezone.utc)
        for minutes, uplink in ((150, 1_000), (90, 2_000), (30, 3_000)):
            record_traffic_bucket(
                db,
                node_id=node.id,
                sampled_at=now - timedelta(minutes=minutes),
                uplink_bytes=uplink,
                downlink_bytes=uplink * 2,
                sample_seconds=10,
            )
        db.commit()

        response = node_router.get_node_operations_history(
            dbnode=node,
            minutes=180,
            max_points=2,
            db=db,
            _=object(),
        )

        assert response.node_id == node.id
        assert len(response.points) == 2
        assert response.points[0].bucket_start < response.points[-1].bucket_start
        assert response.points[0].uplink_bps == 800.0
        assert response.points[-1].uplink_bps == 2_400.0
    finally:
        db.close()
        engine.dispose()


def test_event_timeline_returns_sanitized_reconnect_diagnostics():
    engine, db, node = _session()
    try:
        event, _created = create_node_event(
            db,
            node_id=node.id,
            event_type="node.connection.failed",
            source="master",
            severity="error",
            trigger_reason="watchdog_error",
            root_cause="ConnectionError",
            message="Bearer super-secret password=hunter2",
            reconnect_mode="automatic",
            reconnect_attempt=3,
            reconnect_result="failure",
            downtime_seconds=120,
            metadata={"token": "hidden", "endpoint": "node.example:62050"},
        )
        db.commit()

        response = node_router.get_node_events(
            dbnode=node,
            offset=0,
            limit=50,
            event_type=None,
            severity=None,
            from_time=None,
            to_time=None,
            db=db,
            _=object(),
        )

        assert response.total == 1
        assert response.events[0].id == event.id
        assert response.events[0].reconnect_mode == "automatic"
        assert response.events[0].reconnect_attempt == 3
        assert response.events[0].downtime_seconds == 120
        assert "super-secret" not in (response.events[0].message or "")
        assert "hunter2" not in (response.events[0].message or "")
        assert response.events[0].metadata["token"] == "[REDACTED]"
    finally:
        db.close()
        engine.dispose()


def test_operational_state_is_derived_without_new_transport_status():
    assert node_router._operational_state(NodeStatus.connecting, "offline") == "reconnecting"
    assert node_router._operational_state(NodeStatus.connected, "stale") == "degraded"
    assert node_router._operational_state(NodeStatus.error, "offline") == "offline"
    assert node_router._operational_state(NodeStatus.disabled, "offline") == "disabled"
