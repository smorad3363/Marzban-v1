from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SystemStats(BaseModel):
    version: str
    mem_total: int
    mem_used: int
    cpu_cores: int
    cpu_usage: float
    total_user: int
    online_users: int
    users_active: int
    users_on_hold: int
    users_disabled: int
    users_expired: int
    users_limited: int
    incoming_bandwidth: int
    outgoing_bandwidth: int
    incoming_bandwidth_speed: int
    outgoing_bandwidth_speed: int


class DashboardWeekTrend(BaseModel):
    current: int
    previous: int
    change_percent: float | None = None


class DashboardBillingModeMetric(BaseModel):
    billing_mode: Literal[
        "LEGACY_COMPAT", "SEAT_CREDIT", "USED_TRAFFIC", "ALLOCATED_TRAFFIC", "USER_CREDIT"
    ]
    admin_count: int = 0
    user_count: int = 0
    active_users: int = 0
    current_used_traffic: int | None = 0
    allocated_quota: int = 0


class DashboardTrafficPoint(BaseModel):
    timestamp: datetime
    total_traffic: int = 0


class DashboardAttentionUser(BaseModel):
    username: str
    status: str
    priority: Literal["critical", "high", "warning"]
    reason_code: Literal[
        "expired", "limited", "traffic_exhausted", "traffic_near_limit", "expires_soon", "device_limit"
    ]
    used_traffic: int = 0
    data_limit: int | None = None
    usage_percent: float | None = None
    expire: int | None = None


class DashboardUserSummary(BaseModel):
    username: str
    status: str
    used_traffic: int = 0
    data_limit: int | None = None
    created_at: datetime


class DashboardNodeSummary(BaseModel):
    total: int = 0
    healthy: int = 0
    reconnecting: int = 0
    error: int = 0
    disabled: int = 0


class DashboardAdminSummary(BaseModel):
    total: int = 0
    active: int = 0
    suspended: int = 0
    disabled: int = 0


class DashboardOverview(BaseModel):
    generated_at: datetime
    timezone_offset_minutes: int = Field(ge=-840, le=840)
    current_week_start: datetime
    previous_week_start: datetime
    role: Literal["OWNER", "ADMIN"]
    online_window_seconds: int
    traffic_range: Literal["24h", "7d", "30d"]
    total_users: int
    active_users: int
    online_users: int
    disabled_users: int
    expired_users: int
    limited_users: int
    on_hold_users: int
    current_used_traffic: int | None
    allocated_quota: int
    today_traffic: int = 0
    traffic_history_available: bool = False
    traffic_history: list[DashboardTrafficPoint] = []
    attention_count: int = 0
    attention_users: list[DashboardAttentionUser] = []
    top_consumers: list[DashboardUserSummary] = []
    recent_users: list[DashboardUserSummary] = []
    node_summary: DashboardNodeSummary | None = None
    admin_summary: DashboardAdminSummary | None = None
    new_users: DashboardWeekTrend
    billing_modes: list[DashboardBillingModeMetric]
