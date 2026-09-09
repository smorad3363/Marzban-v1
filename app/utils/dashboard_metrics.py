"""Bounded, scope-aware aggregate queries for the role-based dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Query, Session

from app.db import crud
from app.db.models import (
    Admin,
    AdminAccountStatus,
    AdminHierarchy,
    DeviceLimitUserState,
    MarzhelpAdminSettings,
    Node,
    NodeUserUsage,
    User,
)
from app.device_limit.constants import PenaltyStatus
from app.models.node import NodeStatus
from app.models.system import (
    DashboardAdminSummary,
    DashboardAttentionUser,
    DashboardBillingModeMetric,
    DashboardNodeSummary,
    DashboardOverview,
    DashboardTrafficPoint,
    DashboardUserSummary,
    DashboardWeekTrend,
)
from app.models.user import UserStatus
from app.utils import admin_hierarchy, marzhelp_policy
from app.utils.admin_billing import BillingMode
from config import JOB_RECORD_USER_USAGES_INTERVAL, NOTIFY_DAYS_LEFT, NOTIFY_REACHED_USAGE_PERCENT


MODES = tuple(mode.value for mode in BillingMode)
TRAFFIC_RANGES = {"24h", "7d", "30d"}


def _week_bounds(now: datetime, offset_minutes: int) -> tuple[datetime, datetime, datetime]:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    local_now = now + timedelta(minutes=offset_minutes)
    local_week_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=local_now.weekday()
    )
    current = (local_week_start - timedelta(minutes=offset_minutes)).replace(tzinfo=None)
    previous = current - timedelta(days=7)
    following = current + timedelta(days=7)
    return previous, current, following


def _visible_users(
    db: Session,
    actor: Admin,
    *,
    hierarchy_on: bool,
    actor_is_owner: bool,
    allowed_inbounds: set[str] | None,
) -> Query:
    query = db.query(User)
    if hierarchy_on and not actor_is_owner:
        query = query.filter(
            exists().where(
                and_(
                    AdminHierarchy.ancestor_id == actor.id,
                    AdminHierarchy.descendant_id == User.admin_id,
                )
            )
        )
    elif not hierarchy_on and not actor.is_sudo:
        query = query.filter(User.admin_id == actor.id)
    return crud.apply_inbound_access_filter(query, allowed_inbounds)


def _visible_admins(
    db: Session,
    actor: Admin,
    *,
    hierarchy_on: bool,
    actor_is_owner: bool,
) -> Query:
    query = db.query(Admin)
    if hierarchy_on and not actor_is_owner:
        query = query.filter(
            exists().where(
                and_(
                    AdminHierarchy.ancestor_id == actor.id,
                    AdminHierarchy.descendant_id == Admin.id,
                )
            )
        )
    elif not hierarchy_on and not actor.is_sudo:
        query = query.filter(Admin.id == actor.id)
    return query


def _status_value(status: UserStatus | str) -> str:
    return status.value if isinstance(status, UserStatus) else str(status)


def _traffic_window_start(now: datetime, local_day_start_utc: datetime, traffic_range: str) -> datetime:
    if traffic_range == "24h":
        return now - timedelta(hours=24)
    if traffic_range == "7d":
        return local_day_start_utc - timedelta(days=6)
    return local_day_start_utc - timedelta(days=29)


def _traffic_history(
    db: Session,
    visible: Query,
    *,
    normalized_now: datetime,
    timezone_offset_minutes: int,
    traffic_range: str,
) -> tuple[int, bool, list[DashboardTrafficPoint]]:
    local_now = normalized_now + timedelta(minutes=timezone_offset_minutes)
    local_day_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_day_start_utc = (local_day_start - timedelta(minutes=timezone_offset_minutes)).replace(tzinfo=None)
    range_start = _traffic_window_start(normalized_now, local_day_start_utc.replace(tzinfo=timezone.utc), traffic_range)
    range_start_naive = range_start.astimezone(timezone.utc).replace(tzinfo=None)
    query_start = min(range_start_naive, local_day_start_utc)

    visible_ids = visible.with_entities(User.id).order_by(None).subquery()
    rows = (
        db.query(
            NodeUserUsage.created_at,
            func.coalesce(func.sum(NodeUserUsage.used_traffic), 0),
        )
        .filter(
            NodeUserUsage.created_at >= query_start,
            NodeUserUsage.user_id.in_(select(visible_ids.c.id)),
        )
        .group_by(NodeUserUsage.created_at)
        .order_by(NodeUserUsage.created_at)
        .all()
    )
    today_traffic = sum(int(total or 0) for sampled_at, total in rows if sampled_at >= local_day_start_utc)
    chart_rows = [(sampled_at, int(total or 0)) for sampled_at, total in rows if sampled_at >= range_start_naive]
    if traffic_range == "24h":
        points = [DashboardTrafficPoint(timestamp=sampled_at, total_traffic=total) for sampled_at, total in chart_rows]
        return today_traffic, bool(rows), points

    daily: dict[datetime, int] = defaultdict(int)
    for sampled_at, total in chart_rows:
        local_sample = sampled_at.replace(tzinfo=timezone.utc) + timedelta(minutes=timezone_offset_minutes)
        local_bucket = local_sample.replace(hour=0, minute=0, second=0, microsecond=0)
        utc_bucket = (local_bucket - timedelta(minutes=timezone_offset_minutes)).replace(tzinfo=None)
        daily[utc_bucket] += total
    points = [
        DashboardTrafficPoint(timestamp=bucket, total_traffic=daily[bucket])
        for bucket in sorted(daily)
    ]
    return today_traffic, bool(rows), points


def _attention(
    db: Session,
    visible: Query,
    *,
    normalized_now: datetime,
) -> tuple[int, list[DashboardAttentionUser]]:
    usage_thresholds = sorted({int(value) for value in NOTIFY_REACHED_USAGE_PERCENT if 0 < int(value) <= 100})
    expiry_thresholds = sorted({int(value) for value in NOTIFY_DAYS_LEFT if int(value) > 0})
    now_epoch = int(normalized_now.timestamp())
    warning_usage = usage_thresholds[0] if usage_thresholds else None
    high_usage = usage_thresholds[-1] if len(usage_thresholds) > 1 else None
    max_expiry_days = expiry_thresholds[-1] if expiry_thresholds else None
    high_expiry_days = expiry_thresholds[0] if len(expiry_thresholds) > 1 else None

    conditions = [User.status.in_([UserStatus.expired, UserStatus.limited])]
    if warning_usage is not None:
        conditions.append(
            and_(
                User.data_limit.is_not(None),
                User.data_limit > 0,
                User.used_traffic * 100 >= User.data_limit * warning_usage,
            )
        )
    if max_expiry_days is not None:
        conditions.append(
            and_(
                User.expire.is_not(None),
                User.expire > now_epoch,
                User.expire <= now_epoch + max_expiry_days * 86400,
            )
        )
    conditions.append(DeviceLimitUserState.penalty_status != PenaltyStatus.clear.value)

    candidates = (
        visible.outerjoin(DeviceLimitUserState, DeviceLimitUserState.user_id == User.id)
        .filter(or_(*conditions))
        .with_entities(User, DeviceLimitUserState.penalty_status)
        .order_by(User.used_traffic.desc(), User.id.asc())
        .limit(100)
        .all()
    )
    attention_count = int(
        visible.outerjoin(DeviceLimitUserState, DeviceLimitUserState.user_id == User.id)
        .filter(or_(*conditions))
        .with_entities(func.count(func.distinct(User.id)))
        .scalar()
        or 0
    )

    priority_order = {"critical": 0, "high": 1, "warning": 2}
    items: list[DashboardAttentionUser] = []
    for user, penalty_status in candidates:
        status = _status_value(user.status)
        usage_percent = (
            (float(user.used_traffic or 0) * 100.0 / float(user.data_limit))
            if user.data_limit and user.data_limit > 0
            else None
        )
        priority = "warning"
        reason_code = None
        if status == UserStatus.expired.value:
            priority, reason_code = "critical", "expired"
        elif status == UserStatus.limited.value:
            priority, reason_code = "critical", "limited"
        elif usage_percent is not None and usage_percent >= 100:
            priority, reason_code = "critical", "traffic_exhausted"
        elif penalty_status and penalty_status != PenaltyStatus.clear.value:
            priority, reason_code = "high", "device_limit"
        elif high_usage is not None and usage_percent is not None and usage_percent >= high_usage:
            priority, reason_code = "high", "traffic_near_limit"
        elif high_expiry_days is not None and user.expire and user.expire <= now_epoch + high_expiry_days * 86400:
            priority, reason_code = "high", "expires_soon"
        elif warning_usage is not None and usage_percent is not None and usage_percent >= warning_usage:
            priority, reason_code = "warning", "traffic_near_limit"
        elif max_expiry_days is not None and user.expire and user.expire <= now_epoch + max_expiry_days * 86400:
            priority, reason_code = "warning", "expires_soon"
        if reason_code is None:
            continue
        items.append(
            DashboardAttentionUser(
                username=user.username,
                status=status,
                priority=priority,
                reason_code=reason_code,
                used_traffic=int(user.used_traffic or 0),
                data_limit=user.data_limit,
                usage_percent=round(usage_percent, 1) if usage_percent is not None else None,
                expire=user.expire,
            )
        )

    def sort_key(item: DashboardAttentionUser):
        expire = item.expire or 2**63 - 1
        usage = -(item.usage_percent or 0)
        return (priority_order[item.priority], expire, usage, item.username)

    items.sort(key=sort_key)
    return attention_count, items[:7]


def _compact_user(user: User) -> DashboardUserSummary:
    return DashboardUserSummary(
        username=user.username,
        status=_status_value(user.status),
        used_traffic=int(user.used_traffic or 0),
        data_limit=user.data_limit,
        created_at=user.created_at,
    )


def _owner_node_summary(db: Session) -> DashboardNodeSummary:
    counts = {
        status: int(count)
        for status, count in db.query(Node.status, func.count(Node.id)).group_by(Node.status).all()
    }
    return DashboardNodeSummary(
        total=sum(counts.values()),
        healthy=counts.get(NodeStatus.connected, 0),
        reconnecting=counts.get(NodeStatus.connecting, 0),
        error=counts.get(NodeStatus.error, 0),
        disabled=counts.get(NodeStatus.disabled, 0),
    )


def _owner_admin_summary(db: Session, actor: Admin) -> DashboardAdminSummary:
    rows = (
        db.query(AdminAccountStatus.code, func.count(Admin.id))
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
        .join(AdminAccountStatus, AdminAccountStatus.id == MarzhelpAdminSettings.account_status_id)
        .filter(Admin.id != actor.id, Admin.deleted_at.is_(None))
        .group_by(AdminAccountStatus.code)
        .all()
    )
    counts = {str(code): int(count) for code, count in rows}
    return DashboardAdminSummary(
        total=sum(counts.values()),
        active=counts.get(admin_hierarchy.ACTIVE, 0),
        suspended=counts.get(admin_hierarchy.SUSPENDED, 0),
        disabled=counts.get(admin_hierarchy.DISABLED, 0),
    )


def overview(
    db: Session,
    actor: Admin,
    *,
    timezone_offset_minutes: int,
    traffic_range: str = "24h",
    now: datetime | None = None,
) -> DashboardOverview:
    if traffic_range not in TRAFFIC_RANGES:
        raise ValueError("Unsupported dashboard traffic range")
    generated_at = now or datetime.now(timezone.utc)
    normalized_now = (
        generated_at.replace(tzinfo=timezone.utc)
        if generated_at.tzinfo is None
        else generated_at.astimezone(timezone.utc)
    )
    previous_week, current_week, next_week = _week_bounds(normalized_now, timezone_offset_minutes)
    hierarchy_on = admin_hierarchy.hierarchy_enabled(db)
    actor_is_owner = (
        bool(actor.is_sudo)
        if not hierarchy_on
        else (
            admin_hierarchy.role_code(actor) == admin_hierarchy.OWNER
            and actor.id == admin_hierarchy.owner_id(db)
        )
    )
    allowed_inbounds = marzhelp_policy.allowed_inbound_tags(db, actor)
    visible = _visible_users(
        db,
        actor,
        hierarchy_on=hierarchy_on,
        actor_is_owner=actor_is_owner,
        allowed_inbounds=allowed_inbounds,
    )
    online_window_seconds = max(60, int(JOB_RECORD_USER_USAGES_INTERVAL) * 6)
    online_cutoff = normalized_now.replace(tzinfo=None) - timedelta(seconds=online_window_seconds)
    actor_billing_mode = (
        db.query(MarzhelpAdminSettings.billing_mode)
        .filter(MarzhelpAdminSettings.admin_id == actor.id)
        .scalar()
    )
    usage_visible = bool(
        actor_is_owner
        or actor_billing_mode is None
        or BillingMode(actor_billing_mode or BillingMode.LEGACY_COMPAT.value)
        not in {BillingMode.SEAT_CREDIT, BillingMode.USER_CREDIT}
    )
    aggregate = visible.with_entities(
        func.count(User.id),
        func.coalesce(func.sum(case((User.status == UserStatus.active, 1), else_=0)), 0),
        func.coalesce(func.sum(case((User.status == UserStatus.disabled, 1), else_=0)), 0),
        func.coalesce(func.sum(case((User.status == UserStatus.expired, 1), else_=0)), 0),
        func.coalesce(func.sum(case((User.status == UserStatus.limited, 1), else_=0)), 0),
        func.coalesce(func.sum(case((User.status == UserStatus.on_hold, 1), else_=0)), 0),
        func.coalesce(
            func.sum(case((and_(User.online_at.is_not(None), User.online_at >= online_cutoff), 1), else_=0)),
            0,
        ),
        func.coalesce(func.sum(User.used_traffic), 0),
        func.coalesce(func.sum(User.data_limit), 0),
        func.coalesce(
            func.sum(case((and_(User.created_at >= current_week, User.created_at < next_week), 1), else_=0)),
            0,
        ),
        func.coalesce(
            func.sum(case((and_(User.created_at >= previous_week, User.created_at < current_week), 1), else_=0)),
            0,
        ),
    ).one()

    mode_expression = func.coalesce(MarzhelpAdminSettings.billing_mode, BillingMode.LEGACY_COMPAT.value)
    admin_rows = (
        _visible_admins(db, actor, hierarchy_on=hierarchy_on, actor_is_owner=actor_is_owner)
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
        .with_entities(mode_expression.label("mode"), func.count(Admin.id))
        .group_by(mode_expression)
        .all()
    )
    admin_counts = {str(mode): int(count) for mode, count in admin_rows}

    user_rows = (
        _visible_users(
            db,
            actor,
            hierarchy_on=hierarchy_on,
            actor_is_owner=actor_is_owner,
            allowed_inbounds=allowed_inbounds,
        )
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == User.admin_id)
        .with_entities(
            mode_expression.label("mode"),
            func.count(User.id),
            func.coalesce(func.sum(case((User.status == UserStatus.active, 1), else_=0)), 0),
            func.coalesce(func.sum(User.used_traffic), 0),
            func.coalesce(func.sum(User.data_limit), 0),
        )
        .group_by(mode_expression)
        .all()
    )
    user_by_mode = {
        str(mode): (int(count), int(active), int(used), int(allocated))
        for mode, count, active, used, allocated in user_rows
    }

    today_traffic, traffic_available, traffic_history = _traffic_history(
        db,
        visible,
        normalized_now=normalized_now,
        timezone_offset_minutes=timezone_offset_minutes,
        traffic_range=traffic_range,
    )
    attention_count, attention_users = _attention(db, visible, normalized_now=normalized_now)
    top_consumers = [
        _compact_user(user)
        for user in visible.order_by(User.used_traffic.desc(), User.id.asc()).limit(5).all()
    ]
    recent_users = [
        _compact_user(user)
        for user in visible.order_by(User.created_at.desc(), User.id.desc()).limit(5).all()
    ]

    current_new = int(aggregate[9])
    previous_new = int(aggregate[10])
    change_percent = (
        round(((current_new - previous_new) * 100) / previous_new, 2)
        if previous_new
        else (0.0 if current_new == 0 else None)
    )
    generated = generated_at
    if generated.tzinfo is not None:
        generated = generated.astimezone(timezone.utc).replace(tzinfo=None)
    return DashboardOverview(
        generated_at=generated,
        timezone_offset_minutes=timezone_offset_minutes,
        current_week_start=current_week,
        previous_week_start=previous_week,
        role=admin_hierarchy.OWNER if actor_is_owner else admin_hierarchy.ADMIN,
        online_window_seconds=online_window_seconds,
        traffic_range=traffic_range,
        total_users=int(aggregate[0]),
        active_users=int(aggregate[1]),
        disabled_users=int(aggregate[2]),
        expired_users=int(aggregate[3]),
        limited_users=int(aggregate[4]),
        on_hold_users=int(aggregate[5]),
        online_users=int(aggregate[6]),
        current_used_traffic=int(aggregate[7]) if usage_visible else None,
        allocated_quota=int(aggregate[8]),
        today_traffic=today_traffic,
        traffic_history_available=traffic_available,
        traffic_history=traffic_history,
        attention_count=attention_count,
        attention_users=attention_users,
        top_consumers=top_consumers,
        recent_users=recent_users,
        node_summary=_owner_node_summary(db) if actor_is_owner else None,
        admin_summary=_owner_admin_summary(db, actor) if actor_is_owner else None,
        new_users=DashboardWeekTrend(
            current=current_new,
            previous=previous_new,
            change_percent=change_percent,
        ),
        billing_modes=[
            DashboardBillingModeMetric(
                billing_mode=mode,
                admin_count=admin_counts.get(mode, 0),
                user_count=user_by_mode.get(mode, (0, 0, 0, 0))[0],
                active_users=user_by_mode.get(mode, (0, 0, 0, 0))[1],
                current_used_traffic=(
                    user_by_mode.get(mode, (0, 0, 0, 0))[2] if usage_visible else None
                ),
                allocated_quota=user_by_mode.get(mode, (0, 0, 0, 0))[3],
            )
            for mode in MODES
        ],
    )
