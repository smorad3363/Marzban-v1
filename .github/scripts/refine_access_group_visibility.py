from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected one match in {path}, got {text.count(old)}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "app/utils/access_groups.py",
    '''def list_groups(db: Session, actor: Admin) -> list[AccessGroup]:
    query = db.query(AccessGroup).filter(AccessGroup.archived_at.is_(None))
    if not admin_hierarchy.is_owner(db, actor):
        group_ids = [row[0] for row in query.with_entities(AccessGroup.id).all()]
        restricted = {
            row[0]
            for row in db.query(AccessGroupAdminAccess.access_group_id)
            .filter(AccessGroupAdminAccess.access_group_id.in_(group_ids))
            .distinct()
            .all()
        }
        allowed = {
            row[0]
            for row in db.query(AccessGroupAdminAccess.access_group_id)
            .filter(
                AccessGroupAdminAccess.access_group_id.in_(group_ids),
                AccessGroupAdminAccess.admin_id == actor.id,
            )
            .all()
        }
        visible = (set(group_ids) - restricted) | allowed
        if not visible:
            return []
        query = query.filter(AccessGroup.id.in_(visible))
    return query.order_by(AccessGroup.name, AccessGroup.id).all()
''',
    '''def list_groups(db: Session, actor: Admin) -> list[AccessGroup]:
    query = db.query(AccessGroup).filter(AccessGroup.archived_at.is_(None))
    groups = query.order_by(AccessGroup.name, AccessGroup.id).all()
    if admin_hierarchy.is_owner(db, actor):
        return groups

    # Selection endpoints should expose only groups that can actually be used by
    # this Admin. validated_scope applies both the explicit group permission and
    # the Admin's inbound ceiling, and also hides stale/invalid Host scopes.
    visible: list[AccessGroup] = []
    for group in groups:
        try:
            validated_scope(db, group.id, actor.id)
        except admin_hierarchy.HierarchyError:
            continue
        visible.append(group)
    return visible
''',
)

replace_once(
    "app/dashboard/src/components/UserDialog.tsx",
    '''  const visibleAccessGroups = (accessGroupsQuery.data || []).filter((group) => {
    if (!userData.is_sudo || !selectedOwner) return true;
    return group.allowed_admin_ids.length === 0 || group.allowed_admin_ids.includes(selectedOwner.id);
  });
''',
    '''  const visibleAccessGroups = (accessGroupsQuery.data || []).filter((group) => {
    if (!userData.is_sudo || !selectedOwner) return true;
    const groupPermissionAllowed =
      group.allowed_admin_ids.length === 0 || group.allowed_admin_ids.includes(selectedOwner.id);
    const inboundScopeAllowed =
      selectedOwner.policy.all_inbounds ||
      group.inbounds.every((tag) => selectedOwner.policy.allowed_inbounds.includes(tag));
    return groupPermissionAllowed && inboundScopeAllowed;
  });
''',
)

replace_once(
    "app/dashboard/scripts/test-access-groups.cjs",
    '''assert.ok(freeFormModal.includes("group.allowed_admin_ids.length === 0"));
''',
    '''assert.ok(freeFormModal.includes("group.allowed_admin_ids.length === 0"));
assert.ok(freeFormModal.includes("group.inbounds.every"));
''',
)

replace_once(
    "tests/test_access_group_admin_permissions_contract.py",
    '''    assert "_require_group_access(db, group, admin_id)" in source
    assert "_replace_admin_access(db, group, values)" in source
''',
    '''    assert "_require_group_access(db, group, admin_id)" in source
    assert "_replace_admin_access(db, group, values)" in source
    assert "validated_scope(db, group.id, actor.id)" in source
''',
)

print("Access Group visibility refinement applied")
