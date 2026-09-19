from decimal import Decimal

import pytest
import sqlalchemy as sa
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker

from app import xray
from app.db.base import Base
from app.db.models import Admin, Product, ProxyHost, ProxyInbound
from app.models.product import ProductInput
from app.routers import api_router
from app.utils import admin_hierarchy, products


@pytest.fixture()
def product_db(monkeypatch):
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    owner = Admin(username="owner", hashed_password="x", is_sudo=True)
    child = Admin(username="child", hashed_password="x", is_sudo=False)
    db.add_all([owner, child])
    db.flush()
    tag = "VLESS TCP"
    inbound_config = {
        "tag": tag,
        "protocol": "vless",
        "network": "tcp",
        "tls": "none",
        "port": 443,
    }
    monkeypatch.setattr(xray.config, "inbounds_by_tag", {tag: inbound_config})
    inbound = ProxyInbound(tag=tag)
    db.add(inbound)
    db.flush()
    selected = ProxyHost(
        remark="selected",
        address="selected.example",
        inbound=inbound,
        is_legacy=False,
        is_disabled=False,
    )
    disabled = ProxyHost(
        remark="disabled",
        address="disabled.example",
        inbound=inbound,
        is_legacy=False,
        is_disabled=True,
    )
    db.add_all([selected, disabled])
    db.commit()
    try:
        yield db, owner, child, tag, selected, disabled
    finally:
        db.close()


def _values(tag: str, host_id: int, **changes) -> ProductInput:
    payload = {
        "name": "Primary Product",
        "description": "Owner managed network",
        "traffic_price_multiplier": "1.250000",
        "inbounds": [tag],
        "hosts": {tag: [host_id]},
    }
    payload.update(changes)
    return ProductInput(**payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("price_toman", 1000),
        ("data_limit", 20 * 1024**3),
        ("duration_days", 30),
        ("concurrent_user_limit", 2),
        ("node_ids", [1]),
    ],
)
def test_product_input_rejects_legacy_commercial_and_node_fields(field, value):
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProductInput(
            name="Invalid",
            inbounds=["VLESS TCP"],
            hosts={"VLESS TCP": [1]},
            **{field: value},
        )


def test_product_input_requires_normalized_explicit_network():
    with pytest.raises(ValidationError, match="explicit host"):
        ProductInput(name="Missing host", inbounds=["VLESS TCP"], hosts={})
    with pytest.raises(ValidationError, match="greater than 0"):
        ProductInput(
            name="Bad multiplier",
            traffic_price_multiplier=Decimal("0"),
            inbounds=["VLESS TCP"],
            hosts={"VLESS TCP": [1]},
        )


def test_only_owner_can_create_and_update_products(product_db):
    db, owner, child, tag, selected, _ = product_db
    with pytest.raises(admin_hierarchy.HierarchyError) as forbidden:
        products.create(db, child, _values(tag, selected.id))
    assert forbidden.value.code == "product_management_forbidden"

    product = products.create(db, owner, _values(tag, selected.id))
    stable_id = product.id
    result = products.response(db, product)
    assert result.id == stable_id
    assert result.inbounds == [tag]
    assert result.hosts == {tag: [selected.id]}
    assert result.traffic_price_multiplier == Decimal("1.250000")

    updated = products.update(
        db,
        owner,
        product,
        _values(
            tag,
            selected.id,
            name="Renamed Product",
            traffic_price_multiplier="2.000000",
        ),
    )
    assert updated.id == stable_id
    assert updated.name == "Renamed Product"
    assert updated.traffic_price_multiplier == Decimal("2.000000")
    assert db.query(Product).count() == 1

    with pytest.raises(admin_hierarchy.HierarchyError) as forbidden_update:
        products.update(db, child, product, _values(tag, selected.id))
    assert forbidden_update.value.code == "product_management_forbidden"


def test_product_network_validation_fails_closed(product_db):
    db, owner, _, tag, selected, disabled = product_db
    with pytest.raises(admin_hierarchy.HierarchyError) as unknown_inbound:
        products.create(db, owner, _values("UNKNOWN", selected.id))
    assert unknown_inbound.value.code == "product_inbound_invalid"

    with pytest.raises(admin_hierarchy.HierarchyError) as unavailable_host:
        products.create(db, owner, _values(tag, disabled.id))
    assert unavailable_host.value.code == "product_host_invalid"

    with pytest.raises(admin_hierarchy.HierarchyError) as missing_host:
        products.create(db, owner, _values(tag, 99999))
    assert missing_host.value.code == "product_host_invalid"
    assert db.query(Product).count() == 0


def test_product_routes_and_api_token_scopes_are_explicit():
    methods_by_path: dict[str, set[str]] = {}
    for route in api_router.routes:
        if getattr(route, "path", None):
            methods_by_path.setdefault(route.path, set()).update(
                getattr(route, "methods", None) or []
            )
    assert methods_by_path["/api/products"] >= {"GET", "POST"}
    assert methods_by_path["/api/products/{product_id}"] >= {"GET", "PUT", "DELETE"}
    assert methods_by_path["/api/products/{product_id}/restore"] == {"POST"}
    from app.models.admin import Admin as ApiAdmin

    assert ApiAdmin._required_api_scope("GET", "/api/products") == "products:read"
    assert ApiAdmin._required_api_scope("POST", "/api/products") == "products:write"


def test_archive_preserves_product_identity_and_historical_network(product_db):
    db, owner, _, tag, selected, _ = product_db
    product = products.create(db, owner, _values(tag, selected.id))
    product_id = product.id

    archived = products.archive(db, owner, product)
    assert archived.id == product_id
    assert archived.archived_at is not None
    assert products.list_products(db, owner) == []
    assert [row.id for row in products.list_products(db, owner, include_archived=True)] == [
        product_id
    ]
    assert products.response(db, archived).hosts == {tag: [selected.id]}
    assert products.validated_scope(db, archived) == ({tag}, {tag: {selected.id}})
    assert products.archive(db, owner, archived).archived_at == archived.archived_at

    with pytest.raises(admin_hierarchy.HierarchyError) as edit_archived:
        products.update(db, owner, archived, _values(tag, selected.id))
    assert edit_archived.value.code == "product_archived"
    assert db.get(Product, product_id) is not None


def test_restore_requires_valid_live_network_and_is_idempotent(product_db):
    db, owner, _, tag, selected, _ = product_db
    product = products.create(db, owner, _values(tag, selected.id))
    products.archive(db, owner, product)

    selected.is_disabled = True
    db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError) as invalid_restore:
        products.restore(db, owner, product)
    assert invalid_restore.value.code == "product_host_invalid"
    db.refresh(product)
    assert product.archived_at is not None

    selected.is_disabled = False
    db.commit()
    restored = products.restore(db, owner, product)
    assert restored.archived_at is None
    assert products.restore(db, owner, restored).archived_at is None


def test_non_owner_cannot_archive_or_restore_product(product_db):
    db, owner, child, tag, selected, _ = product_db
    product = products.create(db, owner, _values(tag, selected.id))
    with pytest.raises(admin_hierarchy.HierarchyError) as archive_forbidden:
        products.archive(db, child, product)
    assert archive_forbidden.value.code == "product_management_forbidden"
    with pytest.raises(admin_hierarchy.HierarchyError) as restore_forbidden:
        products.restore(db, child, product)
    assert restore_forbidden.value.code == "product_management_forbidden"
