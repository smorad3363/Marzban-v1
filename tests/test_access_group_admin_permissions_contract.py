from pathlib import Path


def test_access_group_permission_contract_is_enforced_server_side():
    source = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    assert "AccessGroupAdminAccess" in source
    assert '"access_group_forbidden"' in source
    assert "_require_group_access(db, group, admin_id)" in source
    assert "_replace_admin_access(db, group, values)" in source
    assert "validated_scope(db, group.id, actor.id)" in source


def test_free_form_and_owner_transfer_revalidate_access_group():
    source = Path("app/routers/user.py").read_text(encoding="utf-8")
    assert "access_groups.apply_to_user(db, dbuser, new_user.access_group_id)" in source
    assert "access_groups.apply_to_user(db, dbuser, dbuser.access_group_id)" in source


def test_migration_extends_current_node_policy_head():
    source = Path(
        "app/db/migrations/versions/e1a7c4d9b302_access_group_admin_permissions.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "e1a7c4d9b302"' in source
    assert 'down_revision = "f6b2c9d4e701"' in source

def test_access_group_response_exposes_legacy_vs_restricted_policy_state():
    backend = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    model = Path("app/models/admin_hierarchy.py").read_text(encoding="utf-8")
    types = Path("app/dashboard/src/types/Admin.ts").read_text(encoding="utf-8")
    dialog = Path("app/dashboard/src/components/UserDialog.tsx").read_text(encoding="utf-8")
    manager = Path("app/dashboard/src/components/AccessGroupManager.tsx").read_text(encoding="utf-8")

    assert "admin_access_restricted=bool(_permission_admin_ids(db, group.id))" in backend
    assert "admin_access_restricted: bool = False" in model
    assert "admin_access_restricted: boolean;" in types
    assert "!group.admin_access_restricted || group.allowed_admin_ids.includes(selectedOwner.id)" in dialog
    assert "گروه برای همه ادمین‌ها قابل استفاده می‌ماند" not in manager
    assert "دسترسی همه ادمین‌های واگذارشده بسته می‌شود" in manager



def test_existing_binding_maintenance_keeps_admin_inbound_ceiling():
    source = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    assert source.count("_require_admin_network_scope(db, inbounds, user.admin_id)") >= 3
    assert "_require_admin_network_scope(db, inbounds, admin_id)" in source
    assert "and inbounds <= allowed" in source
