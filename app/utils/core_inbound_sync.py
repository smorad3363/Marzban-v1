"""Synchronize explicit network grants when the Xray inbound inventory changes.

This module intentionally does not touch Plans, balances, traffic or user status.
New inbounds are never assigned to an Access Group.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import (
    AccessGroupHost, AccessGroupInbound, MarzhelpAdminInboundPermission,
    MarzhelpAdminSettings, Proxy, ProxyHost, ProxyInbound, User,
    excluded_inbounds_association, template_inbounds_association,
)


def synchronize_inbounds(
    db: Session,
    previous: dict[str, dict],
    proposed: dict[str, dict],
    *,
    rename: tuple[str, str] | None = None,
) -> dict:
    """Stage the change in the caller's DB transaction; never commit here."""
    old_tags, new_tags = set(previous), set(proposed)
    removed = old_tags - new_tags
    if rename:
        old_tag, new_tag = rename
        if (old_tag not in removed or new_tag not in new_tags - old_tags
                or previous[old_tag]["protocol"] != proposed[new_tag]["protocol"]):
            raise ValueError("Rename requires one existing tag and one unused tag of the same protocol")
        # A stale DB identity with the destination name must not be silently merged.
        if db.query(ProxyInbound.id).filter(ProxyInbound.tag == new_tag).first():
            raise ValueError("Destination inbound identity already exists")
        if db.query(AccessGroupInbound).filter(AccessGroupInbound.inbound_tag == new_tag).first():
            raise ValueError("Destination inbound already belongs to an Access Group")
        if db.query(MarzhelpAdminInboundPermission).filter(
            MarzhelpAdminInboundPermission.inbound_tag == new_tag
        ).first():
            raise ValueError("Destination inbound has pre-existing Admin permissions")
        removed.remove(old_tag)

    # Persist identities before making exclusion rows refer to them.
    for tag in sorted(new_tags):
        if db.query(ProxyInbound.id).filter(ProxyInbound.tag == tag).first() is None:
            db.add(ProxyInbound(tag=tag))
    db.flush()

    if rename:
        old_tag, new_tag = rename
        db.query(AccessGroupInbound).filter(
            AccessGroupInbound.inbound_tag == old_tag
        ).update({AccessGroupInbound.inbound_tag: new_tag}, synchronize_session=False)
        db.query(AccessGroupHost).filter(
            AccessGroupHost.inbound_tag == old_tag
        ).update({AccessGroupHost.inbound_tag: new_tag}, synchronize_session=False)
        db.query(ProxyHost).filter(
            ProxyHost.inbound_tag == old_tag
        ).update({ProxyHost.inbound_tag: new_tag}, synchronize_session=False)
        db.query(MarzhelpAdminInboundPermission).filter(
            MarzhelpAdminInboundPermission.inbound_tag == old_tag
        ).update({MarzhelpAdminInboundPermission.inbound_tag: new_tag}, synchronize_session=False)
        for association in (excluded_inbounds_association, template_inbounds_association):
            db.execute(
                association.update()
                .where(association.c.inbound_tag == old_tag)
                .values(inbound_tag=new_tag)
            )

    if removed:
        db.query(AccessGroupHost).filter(
            AccessGroupHost.inbound_tag.in_(removed)
        ).delete(synchronize_session=False)
        db.query(AccessGroupInbound).filter(
            AccessGroupInbound.inbound_tag.in_(removed)
        ).delete(synchronize_session=False)
        db.query(MarzhelpAdminInboundPermission).filter(
            MarzhelpAdminInboundPermission.inbound_tag.in_(removed)
        ).delete(synchronize_session=False)
        # Retain the old Host records for auditing/restore, but never offer them
        # as active new selections when the tag is later independently re-added.
        db.query(ProxyHost).filter(ProxyHost.inbound_tag.in_(removed)).update(
            {ProxyHost.is_legacy: True}, synchronize_session=False
        )
        db.execute(
            template_inbounds_association.delete().where(
                template_inbounds_association.c.inbound_tag.in_(removed)
            )
        )

    # Flush and clear bulk-update identity-map state before reading associations.
    db.flush()
    db.expire_all()

    group_tags: dict[int, set[str]] = {}
    for group_id, tag in db.query(
        AccessGroupInbound.access_group_id, AccessGroupInbound.inbound_tag
    ).all():
        group_tags.setdefault(group_id, set()).add(tag)
    host_counts: dict[tuple[int, str], int] = {}
    for group_id, tag in db.query(
        AccessGroupHost.access_group_id, AccessGroupHost.inbound_tag
    ).all():
        key = (group_id, tag)
        host_counts[key] = host_counts.get(key, 0) + 1
    inbound_rows = {
        row.tag: row for row in db.query(ProxyInbound).filter(ProxyInbound.tag.in_(new_tags)).all()
    }
    protocols = {tag: details["protocol"] for tag, details in proposed.items()}
    touched_users = 0
    # Explicit exclusion records are necessary for the main core and additional
    # device slots; filtering nodes alone does not protect the main core.
    for user in db.query(User).filter(User.access_group_id.isnot(None)).all():
        allowed = group_tags.get(user.access_group_id, set())
        if (not allowed or not allowed <= new_tags
                or any(not host_counts.get((user.access_group_id, tag)) for tag in allowed)):
            allowed = set()
        policy = db.get(MarzhelpAdminSettings, user.admin_id) if user.admin_id else None
        if not policy or (not policy.all_inbounds and not allowed <= set(policy.allowed_inbounds)):
            allowed = set()
        for proxy in user.proxies:
            proxy_protocol = getattr(proxy.type, "value", proxy.type)
            proxy.excluded_inbounds = [
                inbound_rows[tag] for tag in sorted(new_tags)
                if protocols[tag] == proxy_protocol and tag not in allowed
            ]
        touched_users += 1

    db.flush()
    return {
        "removed_tags": sorted(removed),
        "renamed": list(rename) if rename else None,
        "grouped_users_reconciled": touched_users,
        "groups_without_network": sorted(
            group_id for group_id in {
                row[0] for row in db.query(AccessGroupInbound.access_group_id).distinct()
            } if not group_tags.get(group_id)
        ),
    }
