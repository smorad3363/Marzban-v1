"""Scoped, pagination-safe query helpers for the dedicated Users management UI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from app.db import crud
from app.db.models import (
    Admin as DBAdmin,
    AdminHierarchy,
    AdminUserPlan,
    AdminUserPlanVersion,
    DeviceLimitUserState,
    Proxy,
    User,
    UserPlanAssignment,
)
from app.models.admin import Admin
from app.models.user import UserStatus
from app.models.user_management import UserPlanMeta
from app.utils import admin_hierarchy, marzhelp_policy
from config import NOTIFY_DAYS_LEFT, NOTIFY_REACHED_USAGE_PERCENT


def attention_days() -> int:
    configured = [int(value) for value in NOTIFY_DAYS_LEFT if int(value) > 0]
    return max(configured) if configured else 7


def high_usage_percent() -> int:
    configured = [
        max(1, min(int(value), 100))
        for value in NOTIFY_REACHED_USAGE_PERCENT
        if int(value) > 0
    ]
    return min(configured) if configured else 80


def _latest_assignment_id():
    return (
        select(func.max(UserPlanAssignment.id))
        .where(UserPlanAssignment.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )


def _latest_assignment_matches(*criteria):
    latest_assignment_id = _latest_assignment_id()
    return exists().where(
        and_(
            UserPlanAssignment.id == latest_assignment_id,
            *criteria,
        )
    )


def scoped_query(
    db,
    admin: Admin,
    *,
    usernames: list[str] | None = None,
    search: str | None = None,
    owners: list[str] | None = None,
    status: UserStatus | None = None,
    plan_id: int | None = None,
    without_plan: bool = False,
    trial: bool = False,
    attention: bool = False,
    expires_within_days: int | None = None,
    usage_percent_min: int | None = None,
    has_device_limit: bool | None = None,
    unlimited_traffic: bool = False,
    inactive_hours: int | None = None,
):
    """Build the same authorization scope as the canonical `/api/users` query."""

    dbadmin = crud.get_admin(db, admin.username)
    effective_admin = dbadmin or admin
    hierarchy_on = dbadmin is not None and admin_hierarchy.hierarchy_enabled(db)
    owner_role = dbadmin is not None and admin_hierarchy.is_owner(db, dbadmin)

    if hierarchy_on or admin.is_sudo:
        selected_admins = owners
    else:
        selected_admins = (
            [admin.username]
            if owners is None or admin.username in owners
            else []
        )

    query = db.query(User)
    query = crud.apply_inbound_access_filter(
        query,
        marzhelp_policy.allowed_inbound_tags(db, effective_admin),
    )
    if hierarchy_on and not owner_role:
        query = query.filter(
            exists().where(
                and_(
                    AdminHierarchy.ancestor_id == dbadmin.id,
                    AdminHierarchy.descendant_id == User.admin_id,
                )
            )
        )

    if search:
        value = f"%{search.strip()}%"
        query = query.filter(or_(User.username.ilike(value), User.note.ilike(value)))
    if usernames:
        query = query.filter(User.username.in_(usernames))
    if status is not None:
        query = query.filter(User.status == status)
    if selected_admins is not None:
        query = query.filter(User.admin.has(DBAdmin.username.in_(selected_admins)))

    if without_plan:
        query = query.filter(
            ~exists().where(UserPlanAssignment.user_id == User.id)
        )
    elif plan_id is not None:
        query = query.filter(
            _latest_assignment_matches(UserPlanAssignment.plan_id == plan_id)
        )
    if trial:
        query = query.filter(
            _latest_assignment_matches(UserPlanAssignment.is_trial.is_(True))
        )

    now = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    if expires_within_days is not None:
        query = query.filter(
            User.expire.is_not(None),
            User.expire > now_ts,
            User.expire <= now_ts + expires_within_days * 86400,
        )
    if usage_percent_min is not None:
        query = query.filter(
            User.data_limit.is_not(None),
            User.data_limit > 0,
            User.used_traffic.is_not(None),
            User.used_traffic * 100 >= User.data_limit * usage_percent_min,
        )
    if has_device_limit is True:
        query = query.filter(User.concurrent_user_limit.is_not(None))
    elif has_device_limit is False:
        query = query.filter(User.concurrent_user_limit.is_(None))
    if unlimited_traffic:
        query = query.filter(or_(User.data_limit.is_(None), User.data_limit == 0))
    if inactive_hours is not None:
        cutoff = (now - timedelta(hours=inactive_hours)).replace(tzinfo=None)
        query = query.filter(or_(User.online_at.is_(None), User.online_at < cutoff))

    if attention:
        expiry_days = attention_days()
        usage_threshold = high_usage_percent()
        device_attention = exists().where(
            and_(
                DeviceLimitUserState.user_id == User.id,
                DeviceLimitUserState.penalty_status != "clear",
            )
        )
        query = query.filter(
            or_(
                User.status.in_([UserStatus.expired, UserStatus.limited]),
                and_(
                    User.expire.is_not(None),
                    User.expire > now_ts,
                    User.expire <= now_ts + expiry_days * 86400,
                ),
                and_(
                    User.data_limit.is_not(None),
                    User.data_limit > 0,
                    User.used_traffic.is_not(None),
                    User.used_traffic * 100 >= User.data_limit * usage_threshold,
                ),
                device_attention,
            )
        )

    return query


def page_users(
    query,
    *,
    offset: int,
    limit: int,
    sort_options,
):
    total = query.order_by(None).with_entities(func.count(User.id)).scalar() or 0

    if sort_options:
        query = query.order_by(*(option.value for option in sort_options))
        primary_descending = sort_options[0].name.startswith("-")
        query = query.order_by(User.id.desc() if primary_descending else User.id.asc())
    else:
        query = query.order_by(User.created_at.desc(), User.id.desc())

    query = query.offset(offset).limit(limit)
    query = query.options(
        joinedload(User.admin),
        joinedload(User.next_plan),
        selectinload(User.proxies).selectinload(Proxy.excluded_inbounds),
        selectinload(User.usage_logs),
        selectinload(User.device_limit_state),
    )
    return query.all(), int(total)


def plan_meta_for_users(db, users: list[User]) -> dict[str, UserPlanMeta | None]:
    """Resolve only the latest immutable Plan assignment for the bounded page."""

    if not users:
        return {}
    user_ids = [user.id for user in users]
    latest = (
        db.query(
            UserPlanAssignment.user_id.label("user_id"),
            func.max(UserPlanAssignment.id).label("assignment_id"),
        )
        .filter(UserPlanAssignment.user_id.in_(user_ids))
        .group_by(UserPlanAssignment.user_id)
        .subquery()
    )
    rows = (
        db.query(
            UserPlanAssignment,
            AdminUserPlan.name,
            AdminUserPlanVersion.version_number,
        )
        .join(latest, UserPlanAssignment.id == latest.c.assignment_id)
        .join(AdminUserPlan, AdminUserPlan.id == UserPlanAssignment.plan_id)
        .join(AdminUserPlanVersion, AdminUserPlanVersion.id == UserPlanAssignment.version_id)
        .all()
    )
    username_by_id = {user.id: user.username for user in users}
    result: dict[str, UserPlanMeta | None] = {
        user.username: None for user in users
    }
    for assignment, plan_name, version_number in rows:
        username = username_by_id.get(assignment.user_id)
        if username is None:
            continue
        result[username] = UserPlanMeta(
            plan_id=int(assignment.plan_id),
            plan_name=plan_name,
            version_id=int(assignment.version_id),
            version_number=int(version_number),
            is_trial=bool(assignment.is_trial),
            operation_type=assignment.operation_type,
            assigned_at=assignment.created_at,
        )
    return result
