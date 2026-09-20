"""R08.a RED tests for Product assignment and new-selection authorization.

These tests define the backend contract implemented by R08.b and R08.c. Product
access is fail-closed: an active Admin may select an active Product only through
an explicit billing-mode grant or an exact Admin-ID grant, and the Product's
live network must remain inside that Admin's inbound ceiling.
"""

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app import xray
from app.db.base import Base
from app.db.models import (
    Admin,
    AdminAccountStatus,
    AdminHierarchy,
    AdminHierarchySettings,
    AdminRole,
    AdminUserCreationMode,
    MarzhelpAdminInboundPermission,
    MarzhelpAdminSettings,
    Product,
    ProxyHost,
    ProxyInbound,
    SystemOwner,
)
from app.models.product import ProductInput
from app.utils import admin_hierarchy, products
from app.utils.admin_billing import BillingMode


INBOUND = "VLESS TCP"


def _required_policy_api():
    replace = getattr(products, "replace_access_policy", None)
    require = getattr(products, "require_selectable", None)
    available = getattr(products, "list_selectable", None)
    assert replace is not None, "R08.b must implement products.replace_access_policy"
    assert require is not None, "R08.b must implement products.require_selectable"
    assert available is not None, "R08.b must implement products.list_selectable"
    return replace, require, available


def _add_admin(db, owner, username: str, mode: BillingMode, *, status_id: int = 1):
    admin = Admin(
        username=username,
        hashed_password="x",
        is_sudo=False,
        role_id=admin_hierarchy.ROLE_IDS[admin_hierarchy.ADMIN],
    )
    db.add(admin)
    db.flush()
    db.add_all(
        [
            AdminHierarchy(ancestor_id=owner.id, descendant_id=admin.id, depth=1),
            AdminHierarchy(ancestor_id=admin.id, descendant_id=admin.id, depth=0),
            MarzhelpAdminSettings(
                admin_id=admin.id,
                billing_mode=mode.value,
                account_status_id=status_id,
                all_inbounds=True,
            ),
        ]
    )
    db.flush()
    return admin


@pytest.fixture()
def assignment_db(monkeypatch):
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all(
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
    db.flush()

    owner = Admin(
        username="owner",
        hashed_password="x",
        is_sudo=True,
        role_id=admin_hierarchy.ROLE_IDS[admin_hierarchy.OWNER],
    )
    db.add(owner)
    db.flush()
    db.add_all(
        [
            SystemOwner(id=1, admin_id=owner.id),
            AdminHierarchy(ancestor_id=owner.id, descendant_id=owner.id, depth=0),
            MarzhelpAdminSettings(
                admin_id=owner.id,
                billing_mode=BillingMode.LEGACY_COMPAT.value,
                account_status_id=1,
                all_inbounds=True,
            ),
        ]
    )
    used = _add_admin(db, owner, "used", BillingMode.USED_TRAFFIC)
    allocated = _add_admin(db, owner, "allocated", BillingMode.ALLOCATED_TRAFFIC)
    explicit = _add_admin(db, owner, "explicit", BillingMode.USER_CREDIT)
    peer = _add_admin(db, owner, "peer", BillingMode.USER_CREDIT)

    inbound_config = {
        "tag": INBOUND,
        "protocol": "vless",
        "network": "tcp",
        "tls": "none",
        "port": 443,
    }
    monkeypatch.setattr(xray.config, "inbounds_by_tag", {INBOUND: inbound_config})
    inbound = ProxyInbound(tag=INBOUND)
    db.add(inbound)
    db.flush()
    host = ProxyHost(
        remark="selected",
        address="selected.example",
        inbound=inbound,
        is_legacy=False,
        is_disabled=False,
    )
    db.add(host)
    db.commit()
    product = products.create(
        db,
        owner,
        ProductInput(
            name="R08 Product",
            inbounds=[INBOUND],
            hosts={INBOUND: [host.id]},
        ),
    )
    try:
        yield db, owner, used, allocated, explicit, peer, product, host
    finally:
        db.close()


def _set_policy(db, actor, product, *, modes=(), admin_ids=()):
    replace, _, _ = _required_policy_api()
    return replace(
        db,
        actor,
        product,
        allowed_billing_modes=[
            mode.value if isinstance(mode, BillingMode) else str(mode) for mode in modes
        ],
        allowed_admin_ids=list(admin_ids),
    )


def _require_selectable(db, product, admin):
    _, require, _ = _required_policy_api()
    return require(db, product, admin)


def test_product_access_schema_is_explicit_and_separate_from_legacy_permissions():
    tables = Base.metadata.tables
    assert "product_billing_mode_access" in tables
    assert "product_admin_access" in tables
    assert set(tables["product_billing_mode_access"].primary_key.columns.keys()) == {
        "product_id",
        "billing_mode",
    }
    assert set(tables["product_admin_access"].primary_key.columns.keys()) == {
        "product_id",
        "admin_id",
    }
    assert "access_group_admin_access" in tables


def test_product_without_access_rows_is_not_public_compatible(assignment_db):
    db, _, used, _, _, _, product, _ = assignment_db
    with pytest.raises(admin_hierarchy.HierarchyError) as denied:
        _require_selectable(db, product, used)
    assert denied.value.code == "product_forbidden"


def test_billing_mode_grant_covers_current_and_future_matching_admins(assignment_db):
    db, owner, used, allocated, _, _, product, _ = assignment_db
    _set_policy(db, owner, product, modes=[BillingMode.USED_TRAFFIC])

    assert _require_selectable(db, product, used).id == product.id
    with pytest.raises(admin_hierarchy.HierarchyError) as wrong_mode:
        _require_selectable(db, product, allocated)
    assert wrong_mode.value.code == "product_forbidden"

    future = _add_admin(db, owner, "future-used", BillingMode.USED_TRAFFIC)
    db.commit()
    assert _require_selectable(db, product, future).id == product.id


def test_exact_admin_grant_does_not_leak_to_same_mode_peer(assignment_db):
    db, owner, _, _, explicit, peer, product, _ = assignment_db
    _set_policy(db, owner, product, admin_ids=[explicit.id])

    assert _require_selectable(db, product, explicit).id == product.id
    with pytest.raises(admin_hierarchy.HierarchyError) as peer_denied:
        _require_selectable(db, product, peer)
    assert peer_denied.value.code == "product_forbidden"


def test_only_owner_can_change_product_access_policy(assignment_db):
    db, owner, used, _, _, _, product, _ = assignment_db
    with pytest.raises(admin_hierarchy.HierarchyError) as denied:
        _set_policy(db, used, product, modes=[BillingMode.USED_TRAFFIC])
    assert denied.value.code == "product_management_forbidden"

    _set_policy(db, owner, product, modes=[BillingMode.USED_TRAFFIC])
    assert _require_selectable(db, product, used).id == product.id


@pytest.mark.parametrize("legacy_mode", [BillingMode.LEGACY_COMPAT, BillingMode.SEAT_CREDIT])
def test_new_product_policy_rejects_legacy_billing_modes(assignment_db, legacy_mode):
    db, owner, _, _, _, _, product, _ = assignment_db
    with pytest.raises(admin_hierarchy.HierarchyError) as invalid:
        _set_policy(db, owner, product, modes=[legacy_mode])
    assert invalid.value.code == "product_billing_mode_invalid"


def test_explicit_grant_rejects_unknown_owner_and_inactive_targets(assignment_db):
    db, owner, _, _, explicit, _, product, _ = assignment_db
    settings = db.get(MarzhelpAdminSettings, explicit.id)
    settings.account_status_id = admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.SUSPENDED]
    db.commit()

    for admin_id, expected_code in (
        (999_999, "product_admin_invalid"),
        (owner.id, "product_admin_role_invalid"),
        (explicit.id, "product_admin_inactive"),
    ):
        with pytest.raises(admin_hierarchy.HierarchyError) as invalid:
            _set_policy(db, owner, product, admin_ids=[admin_id])
        assert invalid.value.code == expected_code
        db.rollback()


def test_product_selection_rechecks_admin_inbound_ceiling(assignment_db):
    db, owner, used, _, _, _, product, _ = assignment_db
    _set_policy(db, owner, product, modes=[BillingMode.USED_TRAFFIC])
    settings = db.get(MarzhelpAdminSettings, used.id)
    settings.all_inbounds = False
    db.commit()

    with pytest.raises(admin_hierarchy.HierarchyError) as denied:
        _require_selectable(db, product, used)
    assert denied.value.code == "product_scope_forbidden"

    db.add(MarzhelpAdminInboundPermission(admin_id=used.id, inbound_tag=INBOUND))
    db.commit()
    assert _require_selectable(db, product, used).id == product.id


def test_archived_or_invalid_live_product_is_not_selectable_but_grants_survive_restore(
    assignment_db,
):
    db, owner, used, _, _, _, product, host = assignment_db
    _set_policy(db, owner, product, modes=[BillingMode.USED_TRAFFIC])

    products.archive(db, owner, product)
    with pytest.raises(admin_hierarchy.HierarchyError) as archived:
        _require_selectable(db, product, used)
    assert archived.value.code == "product_archived"

    products.restore(db, owner, product)
    assert _require_selectable(db, product, used).id == product.id

    host.is_disabled = True
    db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError) as invalid_network:
        _require_selectable(db, product, used)
    assert invalid_network.value.code == "product_host_invalid"


def test_revocation_blocks_new_selection_and_available_list_is_scoped(assignment_db):
    db, owner, used, allocated, _, _, product, _ = assignment_db
    _set_policy(db, owner, product, modes=[BillingMode.USED_TRAFFIC])
    _, _, available = _required_policy_api()
    assert [row.id for row in available(db, used)] == [product.id]
    assert available(db, allocated) == []

    _set_policy(db, owner, product)
    assert available(db, used) == []
    with pytest.raises(admin_hierarchy.HierarchyError) as revoked:
        _require_selectable(db, product, used)
    assert revoked.value.code == "product_forbidden"
    assert db.get(Product, product.id) is not None
