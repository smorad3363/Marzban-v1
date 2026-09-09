from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from node_runtime.config import RuntimeSettings
from node_runtime.core import prepare_xray_config
from node_runtime.events import EventSpool
from node_runtime.service import create_app
from app.device_limit.engine import DeviceLimitEngine
from app.xray.node import V2ReSTXRayNode


def _settings(tmp_path: Path, *, max_events: int = 1000) -> RuntimeSettings:
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
        max_events=max_events,
    )


def test_event_spool_persists_independent_consumer_offsets(tmp_path):
    path = tmp_path / "events.sqlite3"
    spool = EventSpool(path, max_events=1000)
    ids = [spool.append("xray.log", {"line": f"line-{index}"}) for index in range(1, 4)]
    assert ids == [1, 2, 3]
    assert [item["id"] for item in spool.read("device-limit")] == [1, 2, 3]
    assert spool.ack("device-limit", 2) == 2

    reopened = EventSpool(path, max_events=1000)
    assert [item["id"] for item in reopened.read("device-limit")] == [3]
    assert [item["id"] for item in reopened.read("panel-logs")] == [1, 2, 3]
    with pytest.raises(ValueError):
        reopened.ack("device-limit", 99)


def test_event_spool_is_bounded_without_blocking_new_events(tmp_path):
    spool = EventSpool(tmp_path / "bounded.sqlite3", max_events=1000)
    for index in range(1005):
        spool.append("xray.log", {"line": str(index)})
    stats = spool.stats()
    assert stats["event_count"] == 1000
    assert stats["dropped_events_total"] == 5
    assert stats["oldest_event_id"] == 6
    assert stats["latest_event_id"] == 1005


def test_prepare_xray_config_replaces_api_scope_with_current_panel_peer(tmp_path):
    settings = _settings(tmp_path)
    raw = '{"api":{"tag":"OLD_API"},"inbounds":[{"tag":"API_INBOUND","protocol":"dokodemo-door"},{"tag":"public","protocol":"vless"}],"routing":{"rules":[{"outboundTag":"OLD_API"},{"outboundTag":"direct"}]},"log":{"logLevel":"none"}}'
    prepared = prepare_xray_config(raw, "203.0.113.10", settings)
    assert prepared["inbounds"][0]["tag"] == "API_INBOUND"
    assert prepared["inbounds"][0]["port"] == 62051
    assert prepared["inbounds"][1]["tag"] == "public"
    assert prepared["routing"]["rules"][0]["source"] == ["127.0.0.1", "203.0.113.10"]
    assert all(rule.get("outboundTag") != "OLD_API" for rule in prepared["routing"]["rules"])
    assert prepared["log"]["logLevel"] == "warning"


class FakeCore:
    version = "26.7.28"

    def __init__(self):
        self.started = False
        self.calls = []

    def start(self, config, peer_ip):
        self.calls.append(("start", config, peer_ip))
        self.started = True

    def stop(self):
        self.calls.append(("stop",))
        self.started = False

    def restart(self, config, peer_ip):
        self.calls.append(("restart", config, peer_ip))
        self.started = True


def test_runtime_api_requires_session_and_persists_ack_cursor(tmp_path):
    settings = _settings(tmp_path)
    spool = EventSpool(settings.event_db_path, settings.max_events)
    core = FakeCore()
    client = TestClient(create_app(settings, spool=spool, core=core))
    handshake = client.post("/v2/handshake", json={})
    assert handshake.status_code == 200
    assert handshake.json()["protocol_version"] == 2
    assert "event_ack_v1" in handshake.json()["capabilities"]

    connected = client.post("/connect", json={})
    session_id = connected.json()["session_id"]
    assert client.post("/ping", json={"session_id": session_id}).status_code == 200
    assert client.post("/ping", json={"session_id": "00000000-0000-0000-0000-000000000000"}).status_code == 403

    first = spool.append("xray.log", {"line": "one"})
    second = spool.append("xray.log", {"line": "two"})
    response = client.post("/v2/events", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "after_id": 0,
        "limit": 100,
    })
    events = response.json()["events"]
    log_events = [item for item in events if item["type"] == "xray.log"]
    assert [item["id"] for item in log_events] == [first, second]
    assert any(item["type"] == "runtime.session.connected" for item in events)
    assert client.post("/v2/events/ack", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "event_id": second,
    }).status_code == 200
    replay = client.post("/v2/events", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "after_id": 0,
        "limit": 100,
    })
    assert replay.json()["events"] == []


def test_v2_client_ack_happens_only_after_callback_success():
    node = object.__new__(V2ReSTXRayNode)
    node._session_id = "session"
    requests = []
    callback_lines = []

    def make_request(path, timeout, **params):
        requests.append((path, params.copy()))
        if path == "/v2/events":
            return {"events": [
                {"id": 1, "type": "xray.log", "payload": {"line": "one"}},
                {"id": 2, "type": "xray.log", "payload": {"line": "two"}},
            ]}
        return {"acked_event_id": params["event_id"]}

    node.make_request = make_request
    node.consume_events("device-limit", callback_lines.append, lambda: len(callback_lines) >= 2)
    assert callback_lines == ["one", "two"]
    assert requests[-1] == ("/v2/events/ack", {"consumer_id": "device-limit", "event_id": 2})

    node2 = object.__new__(V2ReSTXRayNode)
    node2._session_id = "session"
    requests2 = []
    node2.make_request = lambda path, timeout, **params: (
        requests2.append((path, params.copy())) or
        ({"events": [{"id": 1, "type": "xray.log", "payload": {"line": "boom"}}]} if path == "/v2/events" else {})
    )
    with pytest.raises(RuntimeError):
        node2.consume_events("device-limit", lambda _line: (_ for _ in ()).throw(RuntimeError("fail")), lambda: False)
    assert all(path != "/v2/events/ack" for path, _params in requests2)


def test_device_limit_missing_runtime_handshake_is_ip_untrusted(monkeypatch):
    from app import xray

    class Source:
        _session_id = "legacy-session"
        process = None
        runtime_handshake = None

        def consume_events(self, consumer_id, callback, should_stop):
            assert consumer_id == "device-limit"
            callback("2026/09/06 12:00:00 8.8.8.8:51000 accepted tcp:example.com:443 [vless >> direct] email: 42.demo.slot1")

    source = Source()
    monkeypatch.setattr(xray, "nodes", {8: source})
    tracker = DeviceLimitEngine()
    tracker.configure(True, "hybrid", True)
    tracker._limited_user_ids = {42}
    tracker._collect(source, "node:8")
    addresses, sources, slots = tracker.live_snapshot(42, 300, 1)
    assert addresses == set()
    assert sources == set()
    assert slots == {}
    assert "node:8" in tracker.diagnostics()["untrusted_ip_sources"]


def test_device_limit_collector_prefers_durable_v2_consumer(monkeypatch):
    from app import xray

    class Source:
        _session_id = "session"
        process = None
        runtime_handshake = SimpleNamespace(supports_direct_client_ip=True)

        def consume_events(self, consumer_id, callback, should_stop):
            assert consumer_id == "device-limit"
            assert should_stop() is False
            callback("2026/09/06 12:00:00 8.8.8.8:51000 accepted tcp:example.com:443 [vless >> direct] email: 42.demo.slot1")

    source = Source()
    monkeypatch.setattr(xray, "nodes", {7: source})
    tracker = DeviceLimitEngine()
    tracker.configure(True, "hybrid", True)
    tracker._limited_user_ids = {42}
    tracker._collect(source, "node:7")
    addresses, sources, slots = tracker.live_snapshot(42, 300, 1)
    assert addresses == {"8.8.8.8"}
    assert sources == {"node:7"}
    assert slots == {1: {"8.8.8.8"}}
    assert "node:7" not in tracker.diagnostics()["untrusted_ip_sources"]
