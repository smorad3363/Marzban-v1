from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.jobs import node_watchdog as watchdog
from app.models.node import NodeStatus
from app.xray import operations


def test_reconnect_backoff_keeps_exponential_delay_bounded_with_jitter():
    first = watchdog.reconnect_backoff_seconds(15, 1, 600, jitter_factor=0.85)
    capped = watchdog.reconnect_backoff_seconds(15, 20, 600, jitter_factor=1.0)
    clamped_low = watchdog.reconnect_backoff_seconds(15, 1, 600, jitter_factor=0.1)

    assert 15 <= first <= 30
    assert capped == 600
    assert 15 <= clamped_low <= 30


def test_transport_replacement_preserves_outage_start_until_real_removal(monkeypatch):
    started = datetime(2026, 9, 9, 10, 0, 0)
    old_node = Mock()
    new_node = SimpleNamespace(node_id=None)
    dbnode = SimpleNamespace(
        id=7,
        address="node.example",
        port=62050,
        api_port=62051,
        usage_coefficient=1.0,
    )

    monkeypatch.setattr(operations.xray, "nodes", {7: old_node})
    monkeypatch.setattr(operations, "_outage_started_at", {7: started})
    monkeypatch.setattr(operations, "get_tls", lambda: {"key": "key", "certificate": "cert"})
    monkeypatch.setattr(operations, "XRayNode", Mock(return_value=new_node))

    assert operations.add_node(dbnode) is new_node
    old_node.disconnect.assert_called_once_with()
    assert operations._outage_started_at[7] == started
    assert operations.xray.nodes[7] is new_node

    operations.remove_node(7)
    assert 7 not in operations._outage_started_at
    assert 7 not in operations.xray.nodes


def test_watchdog_uses_automatic_mode_and_monotonic_attempt_number(monkeypatch):
    settings = SimpleNamespace(
        enabled=True,
        telegram_bot_token="token",
        telegram_chat_id="chat",
        check_interval=15,
        backoff_cap=600,
        remind_every=1800,
    )
    node = SimpleNamespace(
        id=9,
        name="edge-9",
        status=NodeStatus.error,
        message="offline",
        watchdog_enabled=True,
    )
    connect = Mock()

    monkeypatch.setattr(watchdog, "last_check", 0)
    monkeypatch.setattr(watchdog, "fail_count", {})
    monkeypatch.setattr(watchdog, "next_try", {})
    monkeypatch.setattr(watchdog, "last_remind", {})
    monkeypatch.setattr(watchdog, "outage_notified", set())
    monkeypatch.setattr(watchdog, "time", lambda: 1000)
    monkeypatch.setattr(watchdog, "GetDB", lambda: nullcontext(object()))
    monkeypatch.setattr(watchdog.crud, "get_node_watchdog_settings", lambda _db: settings)
    monkeypatch.setattr(watchdog.crud, "get_nodes", lambda _db: [node])
    monkeypatch.setattr(watchdog, "notify", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(watchdog.xray.operations, "connect_node", connect)

    watchdog.node_watchdog()

    connect.assert_called_once_with(
        9,
        reconnect_mode="automatic",
        trigger_reason="watchdog_error",
        reconnect_attempt=1,
    )
    assert watchdog.fail_count[9] == 1
    assert watchdog.next_try[9] > 1000


def test_connection_event_persistence_is_best_effort(monkeypatch):
    db = Mock()
    create = Mock(side_effect=RuntimeError("telemetry database unavailable"))
    monkeypatch.setattr(operations, "GetDB", lambda: nullcontext(db))
    monkeypatch.setattr(operations, "create_node_event", create)

    operations._record_connection_event(
        11,
        "node.connection.failed",
        occurred_at=datetime(2026, 9, 9, 10, 5, 0),
        reconnect_mode="automatic",
        reconnect_attempt=3,
        reconnect_result="failure",
        downtime_seconds=120,
    )

    create.assert_called_once()
    db.commit.assert_not_called()


def test_manual_reconnect_route_marks_operator_trigger_explicitly():
    source = Path("app/routers/node.py").read_text(encoding="utf-8")
    reconnect_block = source[source.index("def reconnect_node("):source.index("@router.delete", source.index("def reconnect_node("))]

    assert 'reconnect_mode="manual"' in reconnect_block
    assert 'trigger_reason="admin_request"' in reconnect_block
    assert "reconnect_attempt=1" in reconnect_block
