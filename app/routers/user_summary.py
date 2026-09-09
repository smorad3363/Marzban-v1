"""Authorization-scoped aggregate metrics for the Users management surface."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, exists, func

from app.db import Session, crud, get_db
from app.db.models import AdminHierarchy, User
from app.models.admin import Admin
from app.utils import admin_hierarchy, marzhelp_policy, responses
from config import NOTIFY_DAYS_LEFT, NOTIFY_REACHED_USAGE_PERCENT


router = APIRouter(
    tags=["User"],
    prefix="/api",
    responses={401: responses._401},
)


class UsersSummaryResponse(BaseModel):
    total_users: int = Field(ge=0)
    online_users: int = Field(ge=0)
    expiring_users: int = Field(ge=0)
    high_usage_users: int = Field(ge=0)
    online_window_hours: int = Field(ge=1)
    expiring_within_days: int = Field(ge=1)
    high_usage_threshold_percent: int = Field(ge=1, le=100)


def _attention_days() -> int:
    """Use the widest configured expiry notification window for attention UX."""
    configured = [int(value) for value in NOTIFY_DAYS_LEFT if int(value) > 0]
    return max(configured) if configured else 7


def _high_usage_percent() -> int:
    """Use the earliest configured usage notification threshold for attention UX."""
    configured = [
        max(1, min(int(value), 100))
        for value in NOTIFY_REACHED_USAGE_PERCENT
        if int(value) > 0
    ]
    return min(configured) if configured else 80


def _user_scope(db: Session, admin: Admin):
    dbadmin = crud.get_admin(db, admin.username)
    effective_admin = dbadmin or admin
    hierarchy_on = dbadmin is not None and admin_hierarchy.hierarchy_enabled(db)
    owner_role = admin_hierarchy.is_owner(db, effective_admin)
    allowed_inbounds = marzhelp_policy.allowed_inbound_tags(db, effective_admin)
    scope_admin_id = dbadmin.id if hierarchy_on and not owner_role else None
    legacy_admin = dbadmin if not hierarchy_on and not admin.is_sudo else None
    return allowed_inbounds, scope_admin_id, legacy_admin


def _scoped_query(
    db: Session,
    *,
    allowed_inbounds: set[str] | None,
    scope_admin_id: int | None,
    legacy_admin,
):
    query = crud.apply_inbound_access_filter(db.query(User), allowed_inbounds)
    if scope_admin_id is not None:
        query = query.filter(
            exists().where(
                and_(
                    AdminHierarchy.ancestor_id == scope_admin_id,
                    AdminHierarchy.descendant_id == User.admin_id,
                )
            )
        )
    elif legacy_admin is not None:
        query = query.filter(User.admin_id == legacy_admin.id)
    return query


@router.get("/users/summary", response_model=UsersSummaryResponse)
def get_users_summary(
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.get_current),
):
    """Return bounded User-management metrics without downloading User rows."""

    online_window_hours = 24
    expiring_within_days = _attention_days()
    high_usage_threshold_percent = _high_usage_percent()
    allowed_inbounds, scope_admin_id, legacy_admin = _user_scope(db, admin)

    base_query = _scoped_query(
        db,
        allowed_inbounds=allowed_inbounds,
        scope_admin_id=scope_admin_id,
        legacy_admin=legacy_admin,
    )
    total_users = base_query.order_by(None).with_entities(func.count(User.id)).scalar() or 0

    now_ts = int(datetime.now(timezone.utc).timestamp())
    expiry_ceiling = now_ts + expiring_within_days * 86400
    expiring_users = (
        base_query.filter(
            User.expire.is_not(None),
            User.expire > now_ts,
            User.expire <= expiry_ceiling,
        )
        .order_by(None)
        .with_entities(func.count(User.id))
        .scalar()
        or 0
    )

    high_usage_users = (
        base_query.filter(
            User.data_limit.is_not(None),
            User.data_limit > 0,
            User.used_traffic.is_not(None),
            User.used_traffic * 100
            >= User.data_limit * high_usage_threshold_percent,
        )
        .order_by(None)
        .with_entities(func.count(User.id))
        .scalar()
        or 0
    )

    online_users = crud.count_online_users(
        db,
        online_window_hours,
        admin=legacy_admin,
        allowed_inbounds=allowed_inbounds,
        scope_admin_id=scope_admin_id,
    )

    return UsersSummaryResponse(
        total_users=int(total_users),
        online_users=int(online_users),
        expiring_users=int(expiring_users),
        high_usage_users=int(high_usage_users),
        online_window_hours=online_window_hours,
        expiring_within_days=expiring_within_days,
        high_usage_threshold_percent=high_usage_threshold_percent,
    )
