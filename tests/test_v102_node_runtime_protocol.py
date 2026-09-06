from pathlib import Path

import pytest

from app.xray.node_protocol_v2 import (
    CAP_CLIENT_IP_DIRECT_V1,
    CAP_CONTROL_V1,
    CAP_EVENT_ACK_V1,
    RuntimeProtocolError,
    parse_event_batch,
    parse_runtime_handshake,
)


def _handshake(**overrides):
    value = {
        "protocol": "marzban-node-v2",
        "protocol_version": 2,
        "runtime_version": "1.0.2",
        "capabilities": [CAP_CONTROL_V1, CAP_EVENT_ACK_V1],
    }
    value.update(overrides)
    return value


def test_v2_handshake_requires_exact_protocol_version_and_reliable_event_capabilities():
    parsed = parse_runtime_handshake(_handshake())
    assert parsed.supports_reliable_events is True
    with pytest.raises(RuntimeProtocolError):
        parse_runtime_handshake(_handshake(protocol_version=3))
    with pytest.raises(RuntimeProtocolError):
        parse_runtime_handshake(_handshake(capabilities=[CAP_CONTROL_V1]))


def test_unknown_capabilities_are_forward_compatible_but_do_not_grant_client_ip_trust():
    parsed = parse_runtime_handshake(_handshake(capabilities=[
        CAP_CONTROL_V1,
        CAP_EVENT_ACK_V1,
        "future_feature_v9",
    ]))
    assert "future_feature_v9" in parsed.capabilities
    assert "future_feature_v9" not in parsed.negotiated_capabilities
    assert parsed.supports_direct_client_ip is False
    trusted = parse_runtime_handshake(_handshake(capabilities=[
        CAP_CONTROL_V1,
        CAP_EVENT_ACK_V1,
        CAP_CLIENT_IP_DIRECT_V1,
    ]))
    assert trusted.supports_direct_client_ip is True


def test_event_batch_is_monotonic_bounded_and_deduplicates_replay_cursor():
    events, highest = parse_event_batch({"events": [
        {"id": 5, "type": "xray.log", "payload": {"line": "old"}},
        {"id": 6, "type": "xray.log", "payload": {"line": "new"}},
        {"id": 6, "type": "xray.log", "payload": {"line": "retry"}},
        {"id": 7, "type": "runtime.health", "payload": {"ok": True}},
    ]}, after_event_id=5)
    assert [event.event_id for event in events] == [6, 6, 7]
    assert highest == 7
    with pytest.raises(RuntimeProtocolError):
        parse_event_batch({"events": [
            {"id": 8, "type": "xray.log", "payload": {}},
            {"id": 7, "type": "xray.log", "payload": {}},
        ]}, after_event_id=5)


def test_node_factory_prefers_explicit_v2_before_legacy_detection():
    source = Path("app/xray/node.py").read_text(encoding="utf-8")
    v2_probe = source.index("if v2_candidate.probe_runtime():")
    legacy_probe = source.index("s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)")
    assert v2_probe < legacy_probe
    assert '"/v2/events/ack"' in source
    assert "parse_event_batch(data, self._last_event_id)" in source
