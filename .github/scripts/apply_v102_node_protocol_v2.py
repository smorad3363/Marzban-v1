from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


protocol_path = Path("app/xray/node_protocol_v2.py")
if protocol_path.exists():
    raise SystemExit("app/xray/node_protocol_v2.py already exists")
protocol_path.write_text('''from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


PROTOCOL_NAME = "marzban-node-v2"
PROTOCOL_VERSION = 2
CAP_CONTROL_V1 = "control_v1"
CAP_EVENT_ACK_V1 = "event_ack_v1"
CAP_CLIENT_IP_DIRECT_V1 = "client_ip_direct_v1"
KNOWN_CAPABILITIES = frozenset({
    CAP_CONTROL_V1,
    CAP_EVENT_ACK_V1,
    CAP_CLIENT_IP_DIRECT_V1,
})
REQUIRED_CAPABILITIES = frozenset({CAP_CONTROL_V1, CAP_EVENT_ACK_V1})
MAX_CAPABILITIES = 64
MAX_EVENTS_PER_BATCH = 256


class RuntimeProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class RuntimeHandshake:
    protocol: str
    protocol_version: int
    runtime_version: str
    capabilities: frozenset[str]

    @property
    def negotiated_capabilities(self) -> frozenset[str]:
        return self.capabilities & KNOWN_CAPABILITIES

    @property
    def supports_reliable_events(self) -> bool:
        return REQUIRED_CAPABILITIES <= self.negotiated_capabilities

    @property
    def supports_direct_client_ip(self) -> bool:
        return CAP_CLIENT_IP_DIRECT_V1 in self.negotiated_capabilities


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: int
    event_type: str
    payload: Mapping[str, Any]
    created_at: str | None = None


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeProtocolError(f"{field} must be an object")
    return value


def parse_runtime_handshake(value: Any) -> RuntimeHandshake:
    data = _require_mapping(value, "handshake")
    if data.get("protocol") != PROTOCOL_NAME:
        raise RuntimeProtocolError("unsupported node runtime protocol")
    if data.get("protocol_version") != PROTOCOL_VERSION:
        raise RuntimeProtocolError("unsupported node runtime protocol version")
    runtime_version = data.get("runtime_version")
    if not isinstance(runtime_version, str) or not runtime_version.strip() or len(runtime_version) > 64:
        raise RuntimeProtocolError("runtime_version must be a non-empty string")
    raw_capabilities = data.get("capabilities")
    if not isinstance(raw_capabilities, list) or len(raw_capabilities) > MAX_CAPABILITIES:
        raise RuntimeProtocolError("capabilities must be a bounded list")
    capabilities: set[str] = set()
    for capability in raw_capabilities:
        if not isinstance(capability, str) or not capability or len(capability) > 64:
            raise RuntimeProtocolError("capability names must be non-empty strings")
        capabilities.add(capability)
    result = RuntimeHandshake(
        protocol=PROTOCOL_NAME,
        protocol_version=PROTOCOL_VERSION,
        runtime_version=runtime_version.strip(),
        capabilities=frozenset(capabilities),
    )
    if not result.supports_reliable_events:
        raise RuntimeProtocolError("node runtime is missing required v2 capabilities")
    return result


def parse_event_batch(value: Any, after_event_id: int) -> tuple[list[RuntimeEvent], int]:
    data = _require_mapping(value, "event batch")
    raw_events = data.get("events")
    if not isinstance(raw_events, list) or len(raw_events) > MAX_EVENTS_PER_BATCH:
        raise RuntimeProtocolError("events must be a bounded list")
    events: list[RuntimeEvent] = []
    highest_seen = max(0, int(after_event_id))
    previous_wire_id = 0
    for raw_event in raw_events:
        item = _require_mapping(raw_event, "event")
        event_id = item.get("id")
        event_type = item.get("type")
        payload = item.get("payload")
        created_at = item.get("created_at")
        if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id <= 0:
            raise RuntimeProtocolError("event id must be a positive integer")
        if event_id < previous_wire_id:
            raise RuntimeProtocolError("event ids must be monotonic")
        previous_wire_id = event_id
        highest_seen = max(highest_seen, event_id)
        if event_id <= after_event_id:
            continue
        if not isinstance(event_type, str) or not event_type or len(event_type) > 96:
            raise RuntimeProtocolError("event type must be a non-empty string")
        if created_at is not None and not isinstance(created_at, str):
            raise RuntimeProtocolError("created_at must be a string when present")
        events.append(RuntimeEvent(
            event_id=event_id,
            event_type=event_type,
            payload=_require_mapping(payload, "event payload"),
            created_at=created_at,
        ))
    return events, highest_seen
''', encoding="utf-8")

replace_once(
    "app/xray/node.py",
    '''from app.xray.config import XRayConfig
from xray_api import XRay as XRayAPI
''',
    '''from app.xray.config import XRayConfig
from app.xray.node_protocol_v2 import RuntimeProtocolError, parse_event_batch, parse_runtime_handshake
from xray_api import XRay as XRayAPI
''',
)
replace_once(
    "app/xray/node.py",
    '''    def connect(self):
        self._node_cert = ssl.get_server_certificate((self.address, self.port))
        self._node_certfile = string_to_temp_file(self._node_cert)
        self.session.verify = self._node_certfile.name

        res = self.make_request("/connect", timeout=3)
        self._session_id = res['session_id']
''',
    '''    def _pin_server_certificate(self):
        self._node_cert = ssl.get_server_certificate((self.address, self.port))
        self._node_certfile = string_to_temp_file(self._node_cert)
        self.session.verify = self._node_certfile.name

    def connect(self):
        self._pin_server_certificate()
        res = self.make_request("/connect", timeout=3)
        self._session_id = res['session_id']
''',
)
replace_once(
    "app/xray/node.py",
    '''

class RPyCXRayNode:
''',
    '''

class V2ReSTXRayNode(ReSTXRayNode):
    """Explicit v2 runtime using acknowledged/replayable event batches."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runtime_handshake = None
        self._last_event_id = 0

    def probe_runtime(self, timeout: int = 2) -> bool:
        try:
            self._pin_server_certificate()
            res = self.session.post(
                self._rest_api_url + "/v2/handshake",
                timeout=timeout,
                json={},
            )
            if res.status_code != 200:
                return False
            self.runtime_handshake = parse_runtime_handshake(res.json())
            return True
        except (RuntimeProtocolError, requests.RequestException, OSError, ssl.SSLError, ValueError):
            return False

    @property
    def capabilities(self):
        if self.runtime_handshake is None:
            return frozenset()
        return self.runtime_handshake.negotiated_capabilities

    def connect(self):
        if self.runtime_handshake is None and not self.probe_runtime():
            raise ConnectionError("Node no longer satisfies the v2 runtime handshake")
        return super().connect()

    def _bg_fetch_logs(self):
        while self._logs_queues:
            if not self._session_id:
                time.sleep(0.2)
                continue
            try:
                data = self.make_request(
                    "/v2/events",
                    timeout=5,
                    after_id=self._last_event_id,
                    limit=100,
                )
                events, highest_seen = parse_event_batch(data, self._last_event_id)
                for event in events:
                    if event.event_type != "xray.log":
                        continue
                    line = event.payload.get("line")
                    if not isinstance(line, str) or not line:
                        continue
                    for buf in list(self._logs_queues):
                        buf.append(line)
                if highest_seen > self._last_event_id:
                    self.make_request(
                        "/v2/events/ack",
                        timeout=3,
                        event_id=highest_seen,
                    )
                    self._last_event_id = highest_seen
                if not events:
                    time.sleep(0.2)
            except (NodeAPIError, RuntimeProtocolError):
                time.sleep(1)


class RPyCXRayNode:
''',
)
replace_once(
    "app/xray/node.py",
    '''        # trying to detect what's the server of node
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
''',
    '''        # Prefer the explicit V2 contract. Legacy nodes retain the historical
        # REST/RPyC detection path below for compatibility.
        v2_candidate = V2ReSTXRayNode(
            address=address,
            port=port,
            api_port=api_port,
            ssl_key=ssl_key,
            ssl_cert=ssl_cert,
            usage_coefficient=usage_coefficient,
        )
        if v2_candidate.probe_runtime():
            return v2_candidate

        # trying to detect what's the server of node
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
''',
)

test_path = Path("tests/test_v102_node_runtime_protocol.py")
if test_path.exists():
    raise SystemExit("tests/test_v102_node_runtime_protocol.py already exists")
test_path.write_text('''from pathlib import Path

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
''', encoding="utf-8")
