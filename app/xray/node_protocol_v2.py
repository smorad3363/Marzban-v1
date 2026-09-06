from __future__ import annotations

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
    seen_ids: set[int] = set()
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
        if event_id <= after_event_id or event_id in seen_ids:
            continue
        seen_ids.add(event_id)
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
