import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.access_group_models import AccessGroupAdminAccess
from app.db.base import Base
from app.db.models import (
    AccessGroup,
    AccessGroupInbound,
    Admin,
    AdminAccountStatus,
    AdminHierarchy,
    AdminHierarchySettings,
    AdminRole,
    AdminUserCreationMode,
    MarzhelpAdminInboundPermission,
    MarzhelpAdminSettings,
    SystemOwner,
    User,
)
from app.models.admin_hierarchy import AccessGroupInput
from app.models.user import UserStatus
from app.utils import access_groups, admin_hierarchy


INBOUND = "VLESS TCP"


@pytest.fixture()
def db():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all(
        [
            AdminRole(id=1, code="OWNER"),
            AdminRole(id=2, code="SUPER_ADMIN"),
            AdminRole(id=3, code="ADMIN"),
            AdminUserCreationMode(id=1, code="FREE_FORM"),
            AdminUserCreationMode(id=2, code="PLAN_ONLY"),
            AdminAccountStatus(id=1, code="ACTIVE"),
            AdminAccountStatus(id=2, code="SUSPENDED"),
            AdminAccountStatus(id=3, code="DISABLED"),
            AdminHierarchySettings(id=1, enabled=True, max_depth=64),
        ]
    )
    session.flush()

    owner = Admin(
        username="owner",
        hashed_password="x",
        is_sudo=True,
        role_id=admin_hierarchy.ROLE_IDS[admin_hierarchy.OWNER],
    )
    target = Admin(
        username="target",
        hashed_password="x",
        is_sudo=False,
        role_id=admin_hierarchy.ROLE_IDS[admin_hierarchy.ADMIN],
    )
    session.add_all([owner, target])
    session.flush()
    session.add_all(
        [
            SystemOwner(id=1, admin_id=owner.id),
            AdminHierarchy(ancestor_id=owner.id, descendant_id=owner.id, depth=0),
            AdminHierarchy(ancestor_id=owner.id, descendant_id=target.id, depth=1),
            AdminHierarchy(ancestor_id=target.id, descendant_id=target.id, depth=0),
            MarzhelpAdminSettings(
                admin_id=owner.id,
                account_status_id=1,
                all_inbounds=True,
            ),
            MarzhelpAdminSettings(
                admin_id=target.id,
                account_status_id=1,
                all_inbounds=True,
            ),
        ]
    )
    session.flush()
    group = AccessGroup(owner_admin_id=owner.id, name="restricted-network")
    session.add(group)
    session.flush()
    session.add(AccessGroupInbound(access_group_id=group.id, inbound_tag=INBOUND))
    session.commit()

    try:
        yield session, owner, target, group
    finally:
        session.close()


def _grant(db, group, admin_id: int) -> None:
    db.add(AccessGroupAdminAccess(access_group_id=group.id, admin_id=admin_id))
    db.flush()


def _values(group, allowed_admin_ids: list[int]) -> AccessGroupInput:
    return AccessGroupInput(
        name=group.name,
        inbounds=[INBOUND],
        hosts={INBOUND: [1]},
        allowed_admin_ids=allowed_admin_ids,
    )


def _legacy_values(group) -> AccessGroupInput:
    return AccessGroupInput(
        name=group.name,
        inbounds=[INBOUND],
        hosts={INBOUND: [1]},
    )


def _assert_grant_error(db, group, admin_id: int, code: str) -> None:
    with pytest.raises(admin_hierarchy.HierarchyError) as raised:
        _grant(db, group, admin_id)
    assert raised.value.code == code
    db.rollback()


def test_access_group_management_remains_owner_only(db):
    session, _, target, _ = db
    with pytest.raises(admin_hierarchy.HierarchyError) as raised:
        access_groups._require_owner(session, target)
    assert raised.value.code == "access_group_management_forbidden"


def test_legacy_group_without_permission_rows_remains_public_compatible(db):
    session, _, target, group = db
    assert access_groups._permission_admin_ids(session, group.id) == []
    assert access_groups._allowed_admin_ids(session, group.id) == []
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == []
    assert response.admin_access_restricted is False
    access_groups._require_group_access(session, group, target.id)


def test_omitted_allowlist_preserves_legacy_public_persistence(db):
    session, _, target, group = db
    values = _legacy_values(group)
    assert "allowed_admin_ids" not in values.model_fields_set

    access_groups._replace_admin_access(session, group, values)
    session.flush()

    assert access_groups._permission_admin_ids(session, group.id) == []
    access_groups._require_group_access(session, group, target.id)


def test_explicit_empty_allowlist_persists_owner_sentinel_and_denies_admins(db):
    session, owner, target, group = db
    values = _values(group, [])
    assert "allowed_admin_ids" in values.model_fields_set

    access_groups._replace_admin_access(session, group, values)
    session.flush()

    assert access_groups._permission_admin_ids(session, group.id) == [owner.id]
    assert access_groups._allowed_admin_ids(session, group.id) == []
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == []
    assert response.admin_access_restricted is True
    access_groups._require_group_access(session, group, owner.id)
    with pytest.raises(admin_hierarchy.HierarchyError) as raised:
        access_groups._require_group_access(session, group, target.id)
    assert raised.value.code == "access_group_forbidden"


def test_explicit_allowlist_persists_sentinel_but_exposes_only_admin_grants(db):
    session, owner, target, group = db
    access_groups._replace_admin_access(session, group, _values(group, [target.id]))
    session.flush()

    assert access_groups._permission_admin_ids(session, group.id) == sorted([owner.id, target.id])
    assert access_groups._allowed_admin_ids(session, group.id) == [target.id]
    response = access_groups.response(session, group)
    assert response.allowed_admin_ids == [target.id]
    assert response.admin_access_restricted is True
    access_groups._require_group_access(session, group, target.id)


def test_unknown_admin_id_fails_closed(db):
    session, _, _, group = db
    _assert_grant_error(session, group, 999_999, "access_group_admin_invalid")


def test_owner_role_cannot_be_added_as_explicit_admin_permission(db):
    session, _, target, group = db
    target.role_id = admin_hierarchy.ROLE_IDS[admin_hierarchy.OWNER]
    session.commit()
    _assert_grant_error(session, group, target.id, "access_group_admin_role_invalid")


def test_suspended_admin_cannot_receive_access_group_permission(db):
    session, _, target, group = db
    settings = session.get(MarzhelpAdminSettings, target.id)
    settings.account_status_id = admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.SUSPENDED]
    session.commit()
    _assert_grant_error(session, group, target.id, "access_group_admin_inactive")


def test_admin_without_policy_cannot_receive_access_group_permission(db):
    session, _, target, group = db
    session.delete(session.get(MarzhelpAdminSettings, target.id))
    session.commit()
    _assert_grant_error(session, group, target.id, "access_group_admin_policy_missing")


def test_admin_outside_active_hierarchy_cannot_receive_permission(db):
    session, _, target, group = db
    session.query(AdminHierarchy).filter(
        AdminHierarchy.ancestor_id == target.id,
        AdminHierarchy.descendant_id == target.id,
    ).delete(synchronize_session=False)
    session.commit()
    _assert_grant_error(session, group, target.id, "access_group_admin_scope_forbidden")


def test_admin_network_scope_must_cover_access_group(db):
    session, _, target, group = db
    settings = session.get(MarzhelpAdminSettings, target.id)
    settings.all_inbounds = False
    session.commit()
    _assert_grant_error(session, group, target.id, "access_group_admin_scope_forbidden")


def test_explicit_matching_network_scope_is_allowed(db):
    session, _, target, group = db
    settings = session.get(MarzhelpAdminSettings, target.id)
    settings.all_inbounds = False
    session.add(MarzhelpAdminInboundPermission(admin_id=target.id, inbound_tag=INBOUND))
    session.commit()

    _grant(session, group, target.id)
    session.commit()
    assert (
        session.query(AccessGroupAdminAccess)
        .filter(
            AccessGroupAdminAccess.access_group_id == group.id,
            AccessGroupAdminAccess.admin_id == target.id,
        )
        .count()
        == 1
    )


def test_active_admin_with_unrestricted_network_scope_is_allowed(db):
    session, _, target, group = db
    _grant(session, group, target.id)
    session.commit()
    assert session.get(AccessGroupAdminAccess, (group.id, target.id)) is not None


def test_revoking_admin_permission_preserves_existing_user_binding(db):
    session, _, target, group = db
    access_groups._replace_admin_access(session, group, _values(group, [target.id]))
    session.flush()
    user = User(
        username="existing-binding",
        admin_id=target.id,
        access_group_id=group.id,
        status=UserStatus.active,
    )
    session.add(user)
    session.commit()

    access_groups._replace_admin_access(session, group, _values(group, []))
    session.commit()

    assert user.access_group_id == group.id
    with pytest.raises(admin_hierarchy.HierarchyError) as raised:
        access_groups._require_group_access(session, group, target.id)
    assert raised.value.code == "access_group_forbidden"
