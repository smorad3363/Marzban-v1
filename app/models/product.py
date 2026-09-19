from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProductInput(BaseModel):
    """Owner-editable Product fields; commercial entitlement lives elsewhere."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=512)
    traffic_price_multiplier: Decimal = Field(
        default=Decimal("1"),
        gt=0,
        max_digits=18,
        decimal_places=6,
    )
    inbounds: list[str] = Field(min_length=1)
    hosts: dict[str, list[int]]

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Product name is required")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("inbounds")
    @classmethod
    def normalize_inbounds(cls, value: list[str]) -> list[str]:
        normalized = sorted({tag.strip() for tag in value if tag.strip()})
        if not normalized:
            raise ValueError("At least one Product inbound is required")
        return normalized

    @model_validator(mode="after")
    def require_explicit_hosts(self):
        normalized_hosts = {
            tag.strip(): sorted({int(host_id) for host_id in host_ids})
            for tag, host_ids in self.hosts.items()
            if tag.strip()
        }
        if (
            set(normalized_hosts) != set(self.inbounds)
            or any(not normalized_hosts[tag] for tag in self.inbounds)
        ):
            raise ValueError("Every Product inbound requires at least one explicit host")
        if any(host_id <= 0 for host_ids in normalized_hosts.values() for host_id in host_ids):
            raise ValueError("Product host identifiers must be positive")
        self.hosts = normalized_hosts
        return self


class ProductResponse(BaseModel):
    id: int
    owner_admin_id: int
    name: str
    description: Optional[str]
    traffic_price_multiplier: Decimal
    inbounds: list[str]
    hosts: dict[str, list[int]]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
