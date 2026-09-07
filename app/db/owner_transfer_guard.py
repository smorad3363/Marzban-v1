"""Transactional invariants for switching the canonical System Owner."""

from __future__ import annotations

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session as OrmSession


_CONTEXT_KEY = "owner_transfer_hardening"


def _transfer_context(session: OrmSession) -> dict | None:
    """Detect a persisted SystemOwner switch and keep context until commit/rollback."""
    existing = session.info.get(_CONTEXT_KEY)
    if existing:
        return existing

    from app.db.models import SystemOwner

    for value in tuple(session.dirty):
        if not isinstance(value, SystemOwner) or int(value.id or 0) != 1:
            continue
        history = inspect(value).attrs.admin_id.history
        old_owner_id = int(history.deleted[0]) if history.deleted else None
        new_owner_id = int(value.admin_id) if value.admin_id is not None else None
        if old_owner_id and new_owner_id and old_owner_id != new_owner_id:
            context = {
                "old_owner_id": old_owner_id,
                "new_owner_id": new_owner_id,
                "resources_migrated": False,
            }
            session.info[_CONTEXT_KEY] = context
            return context
    return None


def _restore_finite_zero_traffic(session: OrmSession, new_owner_id: int) -> None:
    """Do not let repeated set_owner convert canonical finite zero back to NULL/unlimited."""
    from app.db.models import MarzhelpAdminSettings

    for policy in tuple(session.dirty):
        if not isinstance(policy, MarzhelpAdminSettings) or policy.admin_id == new_owner_id:
            continue
        history = inspect(policy).attrs.total_traffic.history
        if not history.deleted or not history.added:
            continue
        previous = history.deleted[0]
        current = history.added[0]
        if previous is not None and int(previous) <= 0 and current is None:
            policy.total_traffic = int(previous)


def _normalize_new_owner_policy(session: OrmSession, new_owner_id: int) -> None:
    from app.db.models import MarzhelpAdminSettings
    from app.utils import admin_hierarchy

    policy = session.get(MarzhelpAdminSettings, new_owner_id)
    if policy is None:
        policy = MarzhelpAdminSettings(admin_id=new_owner_id)
        session.add(policy)

    policy.account_status_id = admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.ACTIVE]
    policy.suspended_reason_id = None
    policy.suspended_at = None
    policy.suspended_by_admin_id = None
    policy.suspension_event_id = None
    policy.expiry_date = None
    policy.renewal_enabled = True
    policy.total_traffic = None
    policy.all_inbounds = True
    policy.all_user_limits = True
    policy.prevent_user_creation = False
    policy.prevent_user_deletion = False
    policy.prevent_user_reset = False
    policy.prevent_revoke_subscription = False
    policy.prevent_unlimited_traffic = False


def _bound_previous_owner_credit(session: OrmSession, old_owner_id: int) -> None:
    """A demoted Owner must not keep an unlimited commercial resource by accident."""
    from app.db.models import MarzhelpAdminSettings
    from app.utils import admin_billing, admin_hierarchy

    policy = session.get(MarzhelpAdminSettings, old_owner_id)
    if policy is None:
        return
    mode = admin_billing.billing_mode(policy)
    if mode == admin_billing.BillingMode.SEAT_CREDIT:
        field = "device_capacity_limit"
    elif mode == admin_billing.BillingMode.USER_CREDIT:
        field = "max_users"
    else:
        field = "total_traffic"
    if getattr(policy, field) is not None:
        return

    spend = int(admin_hierarchy.own_credit_spend(session, policy))
    delegated = (
        0
        if mode == admin_billing.BillingMode.USED_TRAFFIC
        else int(policy.delegated_traffic or 0)
    )
    setattr(policy, field, spend + delegated)


def _transfer_access_groups(session: OrmSession, old_owner_id: int, new_owner_id: int) -> None:
    """Move Access Group ownership and replace Stage-4 Owner sentinels atomically."""
    from app.db.access_group_models import AccessGroupAdminAccess
    from app.db.models import AccessGroup

    groups = (
        session.query(AccessGroup)
        .filter(AccessGroup.owner_admin_id == old_owner_id)
        .order_by(AccessGroup.id)
        .with_for_update()
        .all()
    )
    for group in groups:
        persisted_ids = {
            int(row[0])
            for row in session.query(AccessGroupAdminAccess.admin_id)
            .filter(AccessGroupAdminAccess.access_group_id == group.id)
            .all()
        }
        restricted = bool(persisted_ids)
        session.query(AccessGroupAdminAccess).filter(
            AccessGroupAdminAccess.access_group_id == group.id,
            AccessGroupAdminAccess.admin_id == old_owner_id,
        ).delete(synchronize_session=False)
        group.owner_admin_id = new_owner_id
        if restricted and new_owner_id not in persisted_ids:
            session.add(
                AccessGroupAdminAccess(
                    access_group_id=group.id,
                    admin_id=new_owner_id,
                )
            )


@event.listens_for(OrmSession, "before_flush")
def _enforce_owner_transfer_invariants(session, _flush_context, _instances) -> None:
    context = _transfer_context(session)
    if not context:
        return

    old_owner_id = int(context["old_owner_id"])
    new_owner_id = int(context["new_owner_id"])
    _restore_finite_zero_traffic(session, new_owner_id)

    if not context["resources_migrated"]:
        _normalize_new_owner_policy(session, new_owner_id)
        _bound_previous_owner_credit(session, old_owner_id)
        _transfer_access_groups(session, old_owner_id, new_owner_id)
        context["resources_migrated"] = True


@event.listens_for(OrmSession, "after_commit")
@event.listens_for(OrmSession, "after_rollback")
def _clear_owner_transfer_context(session) -> None:
    session.info.pop(_CONTEXT_KEY, None)
