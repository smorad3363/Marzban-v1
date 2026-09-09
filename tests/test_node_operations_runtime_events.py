from pathlib import Path
from types import SimpleNamespace

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Node
from app.db.node_operations_models import NodeEvent
from app.db.node_runtime_events import persist_runtime_event_batch
from app.models.node import NodeStatus
from app.xray.node_protocol_v2 import (
    CAP_CONTROL_V1,
    CAP_EVENT_ACK_V1,
    CAP_STRUCTURED_EVENTS_V1,
    RuntimeEvent,
    parse_runtime_handshake,
)
from node_runtime.config import RuntimeSettings
from node_runtime.events import EventSpool
from node_runtime.service import create_app


def _settings(tmp_path: Path) -> RuntimeSettings:
    return RuntimeSettings(
        service_host="127.0.0.1",
        service_port=62050,
        api_host="0.0.0.0",
        api_port=62051,
        xray_executable="/usr/local/bin/xray",
        xray_assets_path="/usr/local/share/xray",
        ssl_cert_file=tmp_path / "server.crt",
        ssl_key_file=tmp_path / "server.key",
        ssl_client_cert_file=tmp_path / "panel.crt",
        event_db_path=tmp_path / "events.sqlite3",
        runtime_version="v1.0.2",
        inbounds=(),
        max_events=1000,
    )


class _FakeCore:
    version = "26.7.28"
    started = False

    def start(self, config, peer_ip):
        self.started = True

    def stop(self):
        self.started = False

    def restart(self, config, peer_ip):
        self.started = True


def test_structured_event_capability_is_optional_for_old_v2_nodes():
    legacy = parse_runtime_handshake(
        {
            "protocol": "marzban-node-v2",
            "protocol_version": 2,
            "runtime_version": "1.0.2",
            "capabilities": [CAP_CONTROL_V1, CAP_EVENT_ACK_V1],
        }
    )
    assert legacy.supports_reliable_events is True
    assert legacy.supports_structured_events is False

    current = parse_runtime_handshake(
        {
            "protocol": "marzban-node-v2",
            "protocol_version": 2,
            "runtime_version": "1.0.3",
            "event_stream_id": "stream-abc",
            "capabilities": [
                CAP_CONTROL_V1,
                CAP_EVENT_ACK_V1,
                CAP_STRUCTURED_EVENTS_V1,
            ],
        }
    )
    assert current.supports_structured_events is True
    assert current.event_stream_id == "stream-abc"


def test_event_spool_stream_identity_is_stable_and_advertised(tmp_path):
    path = tmp_path / "events.sqlite3"
    first = EventSpool(path, max_events=1000)
    first_id = first.stream_id
    assert first_id
    reopened = EventSpool(path, max_events=1000)
    assert reopened.stream_id == first_id

    client = TestClient(create_app(_settings(tmp_path), spool=reopened, core=_FakeCore()))
    handshake = client.post("/v2/handshake", json={})
    assert handshake.status_code == 200
    payload = handshake.json()
    assert payload["event_stream_id"] == first_id
    assert CAP_STRUCTURED_EVENTS_V1 in payload["capabilities"]


def test_runtime_event_persistence_deduplicates_replay_by_stream_identity():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        node = Node(
            name="runtime-events-test",
            address="127.0.0.3",
            port=62050,
            api_port=62051,
            status=NodeStatus.connected,
        )
        db.add(node)
        db.commit()

        handshake = SimpleNamespace(runtime_version="1.0.3", event_stream_id="stream-1")
        events = [
            RuntimeEvent(
                event_id=7,
                event_type="runtime.core.start_failed",
                payload={
                    "severity": "error",
                    "reason_code": "RuntimeError",
                    "message": "Bearer secret-token password=hunter2",
                    "previous_state": "starting",
                    "new_state": "stopped",
                    "metadata": {"return_code": 1},
                },
                created_at="2026-09-09T11:30:00+00:00",
            )
        ]
        assert persist_runtime_event_batch(
            db,
            node_id=node.id,
            runtime_version=handshake.runtime_version,
            stream_id=handshake.event_stream_id,
            events=events,
        ) == 1
        db.commit()
        assert persist_runtime_event_batch(
            db,
            node_id=node.id,
            runtime_version=handshake.runtime_version,
            stream_id=handshake.event_stream_id,
            events=events,
        ) == 0
        db.commit()

        row = db.query(NodeEvent).one()
        assert row.runtime_event_id == 7
        assert row.runtime_stream_id == "stream-1"
        assert row.reason_code == "RuntimeError"
        assert "secret-token" not in row.sanitized_message
        assert "hunter2" not in row.sanitized_message
    finally:
        db.close()
        engine.dispose()


def test_master_ack_is_after_commit_and_runtime_emits_lifecycle_events():
    job = Path("app/jobs/node_runtime_events.py").read_text(encoding="utf-8")
    commit_index = job.index("db.commit()")
    ack_index = job.index("node._ack_event_batch")
    assert commit_index < ack_index
    assert "persist_runtime_event_batch(" in job
    assert 'id="node-runtime-events"' in job
    assert "max_instances=1" in job

    core = Path("node_runtime/core.py").read_text(encoding="utf-8")
    for event_type in (
        "runtime.core.starting",
        "runtime.core.started",
        "runtime.core.start_failed",
        "runtime.core.stopping",
        "runtime.core.stopped",
        "runtime.core.restarting",
        "runtime.core.restarted",
        "runtime.core.restart_failed",
        "runtime.core.exited",
    ):
        assert event_type in core
