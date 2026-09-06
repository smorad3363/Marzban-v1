from datetime import datetime
from enum import Enum
from ipaddress import ip_network
from typing import List, Optional

from pydantic import ConfigDict, BaseModel, Field, field_validator, model_validator


class NodeStatus(str, Enum):
    connected = "connected"
    connecting = "connecting"
    error = "error"
    disabled = "disabled"


class NodeIPSourceMode(str, Enum):
    direct = "direct"
    trusted_xff = "trusted_xff"
    proxy_protocol = "proxy_protocol"


class NodeCDNProvider(str, Enum):
    cloudflare = "cloudflare"
    custom = "custom"


MAX_TRUSTED_PROXY_CIDRS = 128


def _validate_complete_ip_source_policy(
    mode: NodeIPSourceMode,
    provider: Optional[NodeCDNProvider],
    cidrs: Optional[List[str]],
) -> None:
    networks = cidrs or []
    if mode is NodeIPSourceMode.direct:
        if provider is not None or networks:
            raise ValueError("direct IP source mode cannot define a CDN provider or trusted proxy CIDRs")
        return
    if mode is NodeIPSourceMode.trusted_xff:
        if provider is None:
            raise ValueError("trusted_xff requires a CDN provider")
        if provider is NodeCDNProvider.custom and not networks:
            raise ValueError("custom trusted_xff requires at least one trusted proxy CIDR")
        return
    if mode is NodeIPSourceMode.proxy_protocol:
        if provider is not None:
            raise ValueError("proxy_protocol does not accept a CDN provider")
        if not networks:
            raise ValueError("proxy_protocol requires at least one trusted proxy CIDR")


class NodeSettings(BaseModel):
    min_node_version: str = "v0.2.0"
    certificate: str


class Node(BaseModel):
    name: str
    address: str
    port: int = 62050
    api_port: int = 62051
    usage_coefficient: float = Field(gt=0, default=1.0)
    watchdog_enabled: bool = True
    ip_source_mode: NodeIPSourceMode = NodeIPSourceMode.direct
    cdn_provider: Optional[NodeCDNProvider] = None
    trusted_proxy_cidrs: Optional[List[str]] = None

    @field_validator("trusted_proxy_cidrs")
    @classmethod
    def canonicalize_trusted_proxy_cidrs(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        if len(value) > MAX_TRUSTED_PROXY_CIDRS:
            raise ValueError(f"at most {MAX_TRUSTED_PROXY_CIDRS} trusted proxy CIDRs are allowed")
        normalized = []
        seen = set()
        for raw in value:
            candidate = str(raw).strip()
            if not candidate:
                continue
            try:
                canonical = str(ip_network(candidate, strict=False))
            except ValueError as exc:
                raise ValueError(f"invalid trusted proxy CIDR: {candidate}") from exc
            if canonical not in seen:
                seen.add(canonical)
                normalized.append(canonical)
        return normalized or None


class NodeCreate(Node):
    add_as_new_host: bool = True

    @model_validator(mode="after")
    def validate_ip_source_policy(self):
        _validate_complete_ip_source_policy(
            self.ip_source_mode, self.cdn_provider, self.trusted_proxy_cidrs
        )
        return self

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "DE node",
            "address": "192.168.1.1",
            "port": 62050,
            "api_port": 62051,
            "add_as_new_host": True,
            "usage_coefficient": 1
        }
    })


class NodeModify(Node):
    name: Optional[str] = Field(None, nullable=True)
    address: Optional[str] = Field(None, nullable=True)
    port: Optional[int] = Field(None, nullable=True)
    api_port: Optional[int] = Field(None, nullable=True)
    status: Optional[NodeStatus] = Field(None, nullable=True)
    usage_coefficient: Optional[float] = Field(None, nullable=True)
    watchdog_enabled: Optional[bool] = Field(None, nullable=True)
    ip_source_mode: Optional[NodeIPSourceMode] = Field(None, nullable=True)
    cdn_provider: Optional[NodeCDNProvider] = Field(None, nullable=True)
    trusted_proxy_cidrs: Optional[List[str]] = Field(None, nullable=True)

    @model_validator(mode="after")
    def validate_complete_ip_source_update(self):
        fields = {"ip_source_mode", "cdn_provider", "trusted_proxy_cidrs"}
        if fields & self.model_fields_set:
            if not fields.issubset(self.model_fields_set):
                raise ValueError("ip source policy updates must include mode, provider, and trusted proxy CIDRs together")
            if self.ip_source_mode is None:
                raise ValueError("ip_source_mode cannot be null when updating the IP source policy")
            _validate_complete_ip_source_policy(
                self.ip_source_mode, self.cdn_provider, self.trusted_proxy_cidrs
            )
        return self

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "DE node",
            "address": "192.168.1.1",
            "port": 62050,
            "api_port": 62051,
            "status": "disabled",
            "usage_coefficient": 1.0
        }
    })


class NodeResponse(Node):
    id: int
    xray_version: Optional[str] = None
    status: NodeStatus
    message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class NodeUsageResponse(BaseModel):
    node_id: Optional[int] = None
    node_name: str
    uplink: int
    downlink: int


class NodesUsageResponse(BaseModel):
    usages: List[NodeUsageResponse]


class NodeBandwidthResponse(BaseModel):
    node_id: Optional[int] = None
    node_name: str
    state: str
    sampled_at: Optional[datetime] = None
    sample_age_seconds: Optional[float] = None
    uplink_bps: float = 0
    downlink_bps: float = 0
    total_bps: float = 0
    peak_5m_uplink_bps: float = 0
    peak_5m_downlink_bps: float = 0


class NodesBandwidthResponse(BaseModel):
    nodes: List[NodeBandwidthResponse]
    total_uplink_bps: float = 0
    total_downlink_bps: float = 0
    total_bps: float = 0
    online_nodes: int = 0
    total_nodes: int = 0


class NodeWatchdogSettingsUpdate(BaseModel):
    enabled: bool = False
    telegram_bot_token: Optional[str] = Field(None, min_length=1, max_length=256)
    telegram_chat_id: Optional[str] = Field(None, max_length=64)
    check_interval: int = Field(15, ge=5, le=3600)
    backoff_cap: int = Field(600, ge=30, le=86400)
    remind_every: int = Field(1800, ge=60, le=604800)


class NodeWatchdogSettingsResponse(BaseModel):
    enabled: bool
    telegram_bot_token_configured: bool
    telegram_chat_id: Optional[str] = None
    check_interval: int
    backoff_cap: int
    remind_every: int
