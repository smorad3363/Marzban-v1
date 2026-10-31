"""Synchronize explicit network grants when the Xray inbound inventory changes.

This module intentionally does not touch Plans, balances, traffic or user status.
New inbounds are never assigned to an Access Group.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AccessGroup, AccessGroupHost, AccessGroupInbound, MarzhelpAdminInboundPermission,
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
    new_identity_tags = set()
    for tag in sorted(new_tags):
        if db.query(ProxyInbound.id).filter(ProxyInbound.tag == tag).first() is None:
            db.add(ProxyInbound(tag=tag))
            new_identity_tags.add(tag)
    db.flush()
    # Preserve the existing default Host behavior for independent new inbounds.
    # Renames move their original Host identities and must not create a Host.
    rename_target = rename[1] if rename else None
    for tag in sorted(new_identity_tags - {rename_target}):
        db.add(ProxyHost(
            inbound_tag=tag,
            remark="🚀 Marz ({USERNAME}) [{PROTOCOL} - {TRANSPORT}]",
            address="{SERVER_IP}",
        ))
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
            row[0] for row in db.query(AccessGroup.id).filter(
                AccessGroup.archived_at.is_(None)
            ).all() if not group_tags.get(row[0])
        ),
    }


# The rollback snapshot is limited to network metadata. Neither commercial
# records nor usage-history tables are read or written by reconciliation.
_STATE_TABLES = (
    AccessGroupInbound.__table__,
    AccessGroupHost.__table__,
    MarzhelpAdminInboundPermission.__table__,
    excluded_inbounds_association,
    template_inbounds_association,
)


def capture_network_state(db: Session) -> dict:
    return {
        "tables": [
            (table, [dict(row) for row in db.execute(select(table)).mappings()])
            for table in _STATE_TABLES
        ],
        "hosts": [
            (row.id, row.inbound_tag, row.is_legacy)
            for row in db.query(ProxyHost).all()
        ],
        "inbound_tags": {
            row[0] for row in db.query(ProxyInbound.tag).all()
        },
    }


def restore_network_state(db: Session, snapshot: dict) -> None:
    # Repair an already-committed DB change if writing/restarting runtime fails.
    # Child rows are restored before removing newly created inbound identities.
    for table, _ in snapshot["tables"]:
        db.execute(table.delete())
    for table, rows in snapshot["tables"]:
        if rows:
            db.execute(table.insert(), rows)
    for host_id, tag, legacy in snapshot["hosts"]:
        db.query(ProxyHost).filter(ProxyHost.id == host_id).update(
            {"inbound_tag": tag, "is_legacy": legacy}, synchronize_session=False
        )
    created_tags = {
        row[0] for row in db.query(ProxyInbound.tag).all()
    } - snapshot["inbound_tags"]
    if created_tags:
        db.query(ProxyHost).filter(ProxyHost.inbound_tag.in_(created_tags)).delete(
            synchronize_session=False
        )
        db.query(ProxyInbound).filter(ProxyInbound.tag.in_(created_tags)).delete(
            synchronize_session=False
        )
    db.flush()
