"""Association models and persistence guards for Access Group permissions."""

from sqlalchemy import BigInteger, Column, ForeignKey, Index, Integer, event
from sqlalchemy.orm import Session as OrmSession

from app.db.base import Base


class AccessGroupAdminAccess(Base):
    """Restrict an Access Group to explicit Admin IDs when rows exist."""

    __tablename__ = "access_group_admin_access"
    __table_args__ = (
        Index("ix_access_group_admin_access_admin_group", "admin_id", "access_group_id"),
    )

    access_group_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("access_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    admin_id = Column(
        Integer,
        ForeignKey("admins.id", ondelete="CASCADE"),
        primary_key=True,
    )


def _pending_or_persisted(session: OrmSession, model, identity: int):
    for value in session.new:
        if isinstance(value, model) and getattr(value, "id", None) == identity:
            return value
    return session.get(model, identity)


def _group_inbounds(session: OrmSession, group_id: int) -> set[str]:
    from app.db.models import AccessGroupInbound

    pending = {
        value.inbound_tag
        for value in session.new
        if isinstance(value, AccessGroupInbound) and value.access_group_id == group_id
    }
    if pending:
        return pending
    return {
        row[0]
        for row in session.query(AccessGroupInbound.inbound_tag)
        .filter(AccessGroupInbound.access_group_id == group_id)
        .all()
    }


def _validate_admin_assignment(session: OrmSession, row: AccessGroupAdminAccess) -> None:
    """Fail closed before an Access Group permission row can be persisted."""
    from app.db.models import Admin, AdminHierarchy, MarzhelpAdminSettings
    from app.utils import admin_hierarchy

    target = _pending_or_persisted(session, Admin, int(row.admin_id))
    if target is None:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_invalid",
            f"Unknown administrator: {row.admin_id}",
        )

    if admin_hierarchy.role_code(target) != admin_hierarchy.ADMIN:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_role_invalid",
            "Access Group permissions can only be assigned to Admin accounts",
        )

    settings = next(
        (
            value
            for value in session.new
            if isinstance(value, MarzhelpAdminSettings) and value.admin_id == target.id
        ),
        None,
    ) or session.get(MarzhelpAdminSettings, target.id)
    if settings is None:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_policy_missing",
            "Administrator policy is missing",
        )

    active_status_id = admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.ACTIVE]
    status_id = getattr(settings, "account_status_id", None)
    if status_id is not None:
        is_active = int(status_id) == active_status_id
    else:
        is_active = admin_hierarchy.account_status_code(session, target.id) == admin_hierarchy.ACTIVE
    if not is_active:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_inactive",
            "Access Group permissions require an active Admin account",
        )

    if admin_hierarchy.hierarchy_enabled(session):
        pending_self_link = any(
            isinstance(value, AdminHierarchy)
            and value.ancestor_id == target.id
            and value.descendant_id == target.id
            and value.depth == 0
            for value in session.new
        )
        persisted_self_link = (
            session.query(AdminHierarchy.ancestor_id)
            .filter(
                AdminHierarchy.ancestor_id == target.id,
                AdminHierarchy.descendant_id == target.id,
                AdminHierarchy.depth == 0,
            )
            .first()
            is not None
        )
        if not pending_self_link and not persisted_self_link:
            raise admin_hierarchy.HierarchyError(
                "access_group_admin_scope_forbidden",
                "Administrator is outside the active Admin hierarchy",
            )

    inbounds = _group_inbounds(session, int(row.access_group_id))
    if not inbounds:
        raise admin_hierarchy.HierarchyError(
            "access_group_admin_scope_forbidden",
            "Access Group network scope is unavailable",
        )
    if not settings.all_inbounds:
        forbidden = inbounds - set(settings.allowed_inbounds or [])
        if forbidden:
            raise admin_hierarchy.HierarchyError(
                "access_group_admin_scope_forbidden",
                f"Access Group exceeds target Admin scope: {sorted(forbidden)}",
            )


@event.listens_for(OrmSession, "before_flush")
def _validate_new_access_group_admin_permissions(session, _flush_context, _instances) -> None:
    """Enforce target Admin role/account/hierarchy/network policy at persistence time."""
    for value in tuple(session.new):
        if isinstance(value, AccessGroupAdminAccess):
            _validate_admin_assignment(session, value)
