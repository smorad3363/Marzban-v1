"""Impact analysis for transactional proxy-host changes."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    AccessGroup,
    AccessGroupHost,
    ProxyHost,
    User,
)
from app.models.proxy import HostUpdateImpact, ProxyHost as ProxyHostModify
from app.models.user import UserStatus


_HOST_FIELDS = (
    "remark", "address", "port", "path", "sni", "host", "security", "alpn",
    "fingerprint", "allowinsecure", "is_disabled", "mux_enable",
    "fragment_setting", "noise_setting", "random_user_agent", "use_sni_as_host",
)


def _changed(existing: ProxyHost, proposed: ProxyHostModify) -> bool:
    return any(getattr(existing, field) != getattr(proposed, field) for field in _HOST_FIELDS)


def analyze_host_update(
    db: Session,
    modified_hosts: dict[str, list[ProxyHostModify]],
) -> HostUpdateImpact:
    tags = sorted(modified_hosts)
    existing = (
        db.query(ProxyHost)
        .filter(ProxyHost.inbound_tag.in_(tags))
        .order_by(ProxyHost.inbound_tag, ProxyHost.id)
        .all()
        if tags
        else []
    )
    existing_by_id = {host.id: host for host in existing}
    proposed_ids = {
        host.id
        for hosts in modified_hosts.values()
        for host in hosts
        if host.id is not None
    }
    removed_ids = sorted(set(existing_by_id) - proposed_ids)
    changed_ids = sorted(
        host.id
        for hosts in modified_hosts.values()
        for host in hosts
        if host.id is not None
        and host.id in existing_by_id
        and _changed(existing_by_id[host.id], host)
    )
    affected_host_ids = sorted(set(removed_ids) | set(changed_ids))
    if not affected_host_ids:
        return HostUpdateImpact(
            affected_access_group_count=0,
            active_user_count=0,
            affected_access_group_ids=[],
            invalid_access_group_ids=[],
            changed_host_ids=changed_ids,
            removed_host_ids=removed_ids,
        )

    group_rows = (
        db.query(AccessGroupHost.access_group_id)
        .join(AccessGroup, AccessGroup.id == AccessGroupHost.access_group_id)
        .filter(
            AccessGroupHost.host_id.in_(affected_host_ids),
            AccessGroup.archived_at.is_(None),
        )
        .distinct()
        .all()
    )
    group_ids = sorted(row[0] for row in group_rows)
    active_user_count = (
        db.query(func.count(User.id))
        .filter(
            User.status == UserStatus.active,
            User.access_group_id.in_(group_ids),
        )
        .scalar()
        or 0
        if group_ids
        else 0
    )

    unavailable_ids = set(removed_ids) | {
        host.id
        for hosts in modified_hosts.values()
        for host in hosts
        if host.id is not None and (host.is_disabled or not host.address.strip())
    }
    hosts_by_group: dict[int, dict[str, set[int]]] = {
        group_id: {} for group_id in group_ids
    }
    if group_ids:
        for group_id, inbound_tag, host_id in (
            db.query(
                AccessGroupHost.access_group_id,
                AccessGroupHost.inbound_tag,
                AccessGroupHost.host_id,
            )
            .filter(AccessGroupHost.access_group_id.in_(group_ids))
            .all()
        ):
            hosts_by_group[group_id].setdefault(inbound_tag, set()).add(host_id)
    invalid_group_ids = sorted(
        group_id
        for group_id, by_tag in hosts_by_group.items()
        if any(not (host_ids - unavailable_ids) for host_ids in by_tag.values())
    )
    return HostUpdateImpact(
        affected_access_group_count=len(group_ids),
        active_user_count=int(active_user_count),
        affected_access_group_ids=group_ids,
        invalid_access_group_ids=invalid_group_ids,
        changed_host_ids=changed_ids,
        removed_host_ids=removed_ids,
    )
