from pathlib import Path


def test_access_group_permission_contract_is_enforced_server_side():
    source = Path("app/utils/access_groups.py").read_text(encoding="utf-8")
    assert "AccessGroupAdminAccess" in source
    assert '"access_group_forbidden"' in source
    assert "_require_group_access(db, group, admin_id)" in source
    assert "_replace_admin_access(db, group, values)" in source


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
