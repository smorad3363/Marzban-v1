"""Owner Product catalog and fail-closed live Inbound/Host validation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app import xray
from app.db.models import Admin, Product, ProductHost, ProductInbound, ProxyHost
from app.models.product import ProductInput, ProductResponse
from app.utils import admin_hierarchy


def _require_owner(db: Session, actor: Admin) -> None:
    if not admin_hierarchy.is_owner(db, actor):
        raise admin_hierarchy.HierarchyError(
            "product_management_forbidden",
            "Only Owner can manage Products",
        )


def _scope(db: Session, product_id: int) -> tuple[set[str], dict[str, set[int]]]:
    inbounds = {
        row.inbound_tag
        for row in db.query(ProductInbound).filter(ProductInbound.product_id == product_id)
    }
    hosts = {tag: set() for tag in inbounds}
    for row in db.query(ProductHost).filter(ProductHost.product_id == product_id):
        hosts.setdefault(row.inbound_tag, set()).add(row.host_id)
    return inbounds, hosts


def _validate_values(db: Session, values: ProductInput) -> None:
    unknown = set(values.inbounds) - set(xray.config.inbounds_by_tag)
    if unknown:
        raise admin_hierarchy.HierarchyError(
            "product_inbound_invalid",
            f"Unknown Product inbounds: {sorted(unknown)}",
        )
    selected_ids = {
        host_id
        for host_ids in values.hosts.values()
        for host_id in host_ids
    }
    live_hosts = {
        row.id: row.inbound_tag
        for row in db.query(ProxyHost.id, ProxyHost.inbound_tag)
        .filter(
            ProxyHost.id.in_(selected_ids),
            ProxyHost.is_legacy.is_(False),
            ProxyHost.is_disabled.is_(False),
            ProxyHost.address != "",
        )
        .all()
    }
    invalid = sorted(
        host_id
        for tag, host_ids in values.hosts.items()
        for host_id in host_ids
        if live_hosts.get(host_id) != tag
    )
    if invalid:
        raise admin_hierarchy.HierarchyError(
            "product_host_invalid",
            f"Unavailable or mismatched Product hosts: {invalid}",
        )


def _replace_scope(db: Session, product: Product, values: ProductInput) -> None:
    db.query(ProductHost).filter(ProductHost.product_id == product.id).delete(
        synchronize_session=False
    )
    db.query(ProductInbound).filter(ProductInbound.product_id == product.id).delete(
        synchronize_session=False
    )
    db.add_all(
        ProductInbound(product_id=product.id, inbound_tag=tag)
        for tag in values.inbounds
    )
    db.flush()
    db.add_all(
        ProductHost(product_id=product.id, inbound_tag=tag, host_id=host_id)
        for tag, host_ids in values.hosts.items()
        for host_id in host_ids
    )


def response(db: Session, product: Product) -> ProductResponse:
    inbounds, hosts = _scope(db, product.id)
    return ProductResponse(
        id=product.id,
        owner_admin_id=product.owner_admin_id,
        name=product.name,
        description=product.description,
        traffic_price_multiplier=product.traffic_price_multiplier,
        inbounds=sorted(inbounds),
        hosts={tag: sorted(hosts[tag]) for tag in sorted(inbounds)},
        archived_at=product.archived_at,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def list_products(
    db: Session,
    actor: Admin,
    *,
    include_archived: bool = False,
) -> list[Product]:
    _require_owner(db, actor)
    query = db.query(Product)
    if not include_archived:
        query = query.filter(Product.archived_at.is_(None))
    return query.order_by(Product.name, Product.id).all()


def get(db: Session, actor: Admin, product_id: int) -> Product:
    _require_owner(db, actor)
    product = db.get(Product, product_id)
    if product is None:
        raise admin_hierarchy.HierarchyError("product_not_found", "Product not found")
    return product


def create(db: Session, actor: Admin, values: ProductInput) -> Product:
    _require_owner(db, actor)
    _validate_values(db, values)
    product = Product(
        owner_admin_id=actor.id,
        name=values.name,
        description=values.description,
        traffic_price_multiplier=values.traffic_price_multiplier,
    )
    db.add(product)
    db.flush()
    _replace_scope(db, product, values)
    db.commit()
    db.refresh(product)
    return product


def update(
    db: Session,
    actor: Admin,
    product: Product,
    values: ProductInput,
) -> Product:
    _require_owner(db, actor)
    if product.archived_at is not None:
        raise admin_hierarchy.HierarchyError(
            "product_archived",
            "Archived Product must be restored before editing",
        )
    _validate_values(db, values)
    product.name = values.name
    product.description = values.description
    product.traffic_price_multiplier = values.traffic_price_multiplier
    _replace_scope(db, product, values)
    db.commit()
    db.refresh(product)
    return product


def archive(db: Session, actor: Admin, product: Product) -> Product:
    """Disable future selection without deleting identity or live network history."""
    _require_owner(db, actor)
    if product.archived_at is None:
        product.archived_at = admin_hierarchy.utc_now_naive()
        db.commit()
        db.refresh(product)
    return product


def restore(db: Session, actor: Admin, product: Product) -> Product:
    """Restore future selection only when the persisted live scope is valid."""
    _require_owner(db, actor)
    if product.archived_at is not None:
        validated_scope(db, product)
        product.archived_at = None
        db.commit()
        db.refresh(product)
    return product


def validated_scope(db: Session, product: Product) -> tuple[set[str], dict[str, set[int]]]:
    """Resolve stored live scope without any unrestricted fallback."""
    inbounds, hosts = _scope(db, product.id)
    if not inbounds or set(hosts) != inbounds or any(not hosts[tag] for tag in inbounds):
        raise admin_hierarchy.HierarchyError(
            "product_network_invalid",
            "Product has incomplete network scope",
        )
    values = ProductInput(
        name=product.name,
        description=product.description,
        traffic_price_multiplier=product.traffic_price_multiplier,
        inbounds=sorted(inbounds),
        hosts={tag: sorted(hosts[tag]) for tag in sorted(inbounds)},
    )
    _validate_values(db, values)
    return inbounds, hosts
