from datetime import date, timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.access_group_models import AccessGroupAdminAccess
from app.db.base import Base
from app.db.models import (
    AccessGroup,
    Admin,
    AdminAccountStatus,
    AdminHierarchy,
    AdminHierarchySettings,
    AdminRole,
    AdminSuspensionReason,
    AdminUserCreationMode,
    MarzhelpAdminSettings,
    SystemOwner,
)
from app.utils import access_groups, admin_hierarchy


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
            AdminUserCreationMode(id=3, code="BOTH"),
            AdminAccountStatus(id=1, code="ACTIVE"),
            AdminAccountStatus(id=2, code="SUSPENDED"),
            AdminAccountStatus(id=3, code="DISABLED"),
            AdminSuspensionReason(id=1, code="MANUAL"),
            AdminHierarchySettings(id=1, enabled=False, max_depth=64),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()


def _depth(db, ancestor_id: int, descendant_id: int) -> int | None:
    return db.query(AdminHierarchy.depth).filter(
        AdminHierarchy.ancestor_id == ancestor_id,
        AdminHierarchy.descendant_id == descendant_id,
    ).scalar()


def test_owner_transfer_preserves_hierarchy_and_hardens_policies_and_access_groups(db):
    old_owner = Admin(username="old-owner", hashed_password="x", is_sudo=True)
    heir = Admin(username="heir", hashed_password="x", is_sudo=False)
    leaf = Admin(username="leaf", hashed_password="x", is_sudo=False)
    db.add_all([old_owner, heir, leaf])
    db.flush()
    leaf.parent_admin_id = old_owner.id
    db.add_all(
        [
            MarzhelpAdminSettings(
                admin_id=old_owner.id,
                total_traffic=0,
                calculate_volume="created_traffic",
                account_status_id=1,
            ),
            MarzhelpAdminSettings(
                admin_id=heir.id,
                total_traffic=100,
                calculate_volume="created_traffic",
                account_status_id=1,
            ),
            MarzhelpAdminSettings(
                admin_id=leaf.id,
                total_traffic=100,
                calculate_volume="created_traffic",
                account_status_id=1,
            ),
        ]
    )
    db.commit()

    # Initial legacy cutover remains compatible.
    admin_hierarchy.set_owner(db, old_owner.username)
    db.refresh(old_owner)
    db.refresh(heir)
    db.refresh(leaf)
    assert admin_hierarchy.is_owner(db, old_owner)
    assert heir.parent_admin_id == old_owner.id
    assert leaf.parent_admin_id == old_owner.id

    restricted = AccessGroup(owner_admin_id=old_owner.id, name="restricted")
    legacy_public = AccessGroup(owner_admin_id=old_owner.id, name="legacy-public")
    db.add_all([restricted, legacy_public])
    db.flush()
    # Persist a Stage-4 restricted policy without invoking network-scope validation;
    # this fixture is testing owner/sentinel transfer, not network selection.
    db.execute(
        sa.insert(AccessGroupAdminAccess),
        [
            {"access_group_id": restricted.id, "admin_id": old_owner.id},
            {"access_group_id": restricted.id, "admin_id": leaf.id},
        ],
    )

    old_policy = db.get(MarzhelpAdminSettings, old_owner.id)
    old_policy.used_traffic = 40
    old_policy.delegated_traffic = 10
    assert old_policy.total_traffic is None

    heir_policy = db.get(MarzhelpAdminSettings, heir.id)
    heir_policy.account_status_id = admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.SUSPENDED]
    heir_policy.suspended_reason_id = 1
    heir_policy.suspended_at = admin_hierarchy.utc_now_naive()
    heir_policy.suspended_by_admin_id = old_owner.id
    heir_policy.expiry_date = date.today() - timedelta(days=1)
    heir_policy.all_inbounds = False
    heir_policy.all_user_limits = False
    heir_policy.prevent_user_creation = True

    # Canonical zero must stay finite across a repeated set_owner/Owner transfer.
    leaf_policy = db.get(MarzhelpAdminSettings, leaf.id)
    leaf_policy.total_traffic = 0
    db.commit()

    report = admin_hierarchy.set_owner(db, heir.username)
    db.refresh(old_owner)
    db.refresh(heir)
    db.refresh(leaf)
    db.refresh(restricted)
    db.refresh(legacy_public)
    old_policy = db.get(MarzhelpAdminSettings, old_owner.id)
    heir_policy = db.get(MarzhelpAdminSettings, heir.id)
    leaf_policy = db.get(MarzhelpAdminSettings, leaf.id)

    assert report["owner"] == heir.username
    assert db.get(SystemOwner, 1).admin_id == heir.id
    assert admin_hierarchy.is_owner(db, heir)
    assert not admin_hierarchy.is_owner(db, old_owner)
    assert heir.role_id == admin_hierarchy.ROLE_IDS[admin_hierarchy.OWNER]
    assert heir.is_sudo is True
    assert heir.parent_admin_id is None
    assert old_owner.role_id == admin_hierarchy.ROLE_IDS[admin_hierarchy.ADMIN]
    assert old_owner.is_sudo is False
    assert old_owner.parent_admin_id == heir.id
    assert leaf.parent_admin_id == old_owner.id

    # Closure is rebuilt from the new root, preserving descendants of the old Owner.
    assert _depth(db, heir.id, heir.id) == 0
    assert _depth(db, heir.id, old_owner.id) == 1
    assert _depth(db, heir.id, leaf.id) == 2
    assert _depth(db, old_owner.id, leaf.id) == 1
    assert _depth(db, old_owner.id, heir.id) is None

    # New Owner cannot inherit a suspended/expired/restricted Admin account policy.
    assert heir_policy.account_status_id == admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.ACTIVE]
    assert heir_policy.suspended_reason_id is None
    assert heir_policy.suspended_at is None
    assert heir_policy.suspended_by_admin_id is None
    assert heir_policy.suspension_event_id is None
    assert heir_policy.expiry_date is None
    assert heir_policy.renewal_enabled is True
    assert heir_policy.total_traffic is None
    assert heir_policy.all_inbounds is True
    assert heir_policy.all_user_limits is True
    assert heir_policy.prevent_user_creation is False

    # The demoted Owner no longer keeps NULL/unlimited credit. Its finite ceiling
    # equals already-consumed + delegated credit, leaving no accidental headroom.
    assert old_policy.total_traffic == 50
    assert admin_hierarchy.available_credit(db, old_policy) == 0
    assert leaf_policy.total_traffic == 0
    assert admin_hierarchy.available_credit(db, leaf_policy) == 0

    # Restricted Access Groups follow the new Owner and swap only the internal
    # sentinel. The old Owner does not keep access through the former sentinel.
    assert restricted.owner_admin_id == heir.id
    assert access_groups._permission_admin_ids(db, restricted.id) == sorted([heir.id, leaf.id])
    assert access_groups._allowed_admin_ids(db, restricted.id) == [leaf.id]
    with pytest.raises(admin_hierarchy.HierarchyError) as denied:
        access_groups._require_group_access(db, restricted, old_owner.id)
    assert denied.value.code == "access_group_forbidden"
    access_groups._require_group_access(db, restricted, heir.id)
    access_groups._require_group_access(db, restricted, leaf.id)

    # Legacy zero-row groups remain public-compatible, but ownership still moves.
    assert legacy_public.owner_admin_id == heir.id
    assert access_groups._permission_admin_ids(db, legacy_public.id) == []
    access_groups._require_group_access(db, legacy_public, old_owner.id)
