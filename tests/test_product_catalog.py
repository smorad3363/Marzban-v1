import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Admin, AdminUserPlan, Product, ProductHost, ProductInbound


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "app"
    / "db"
    / "migrations"
    / "versions"
    / "f7a3c9e1d205_add_product_catalog.py"
)


def _migration():
    spec = importlib.util.spec_from_file_location("product_catalog_migration", MIGRATION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _enable_foreign_keys(connection, _record) -> None:
    connection.execute("PRAGMA foreign_keys=ON")


@pytest.fixture()
def product_db():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    sa.event.listen(engine, "connect", _enable_foreign_keys)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    owner = Admin(username="owner", hashed_password="x", is_sudo=True)
    session.add(owner)
    session.commit()
    try:
        yield session, owner
    finally:
        session.close()


def test_product_schema_is_separate_from_legacy_commercial_plan():
    product_columns = set(Product.__table__.c.keys())
    assert product_columns == {
        "id",
        "owner_admin_id",
        "name",
        "description",
        "traffic_price_multiplier",
        "archived_at",
        "created_at",
        "updated_at",
    }
    assert {
        "price_toman",
        "data_limit",
        "duration_days",
        "concurrent_user_limit",
        "base_price_toman",
        "node_ids",
    }.isdisjoint(product_columns)
    assert Product.__tablename__ != AdminUserPlan.__tablename__
    assert ProductInbound.__table__.primary_key.columns.keys() == ["product_id", "inbound_tag"]
    assert ProductHost.__table__.primary_key.columns.keys() == [
        "product_id",
        "inbound_tag",
        "host_id",
    ]


def test_product_identity_multiplier_and_network_constraints(product_db):
    db, owner = product_db
    product = Product(owner_admin_id=owner.id, name="Primary")
    db.add(product)
    db.flush()
    db.add(ProductInbound(product_id=product.id, inbound_tag="VLESS TCP"))
    db.flush()
    db.add(ProductHost(product_id=product.id, inbound_tag="VLESS TCP", host_id=7))
    db.commit()
    db.refresh(product)

    assert product.id is not None
    assert product.traffic_price_multiplier == Decimal("1.000000")

    db.add(Product(owner_admin_id=owner.id, name="Primary"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(
        Product(
            owner_admin_id=owner.id,
            name="Invalid multiplier",
            traffic_price_multiplier=Decimal("0"),
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(ProductHost(product_id=product.id, inbound_tag="UNKNOWN", host_id=8))
    with pytest.raises(IntegrityError):
        db.commit()


def test_product_migration_is_additive_on_seeded_schema(monkeypatch):
    migration = _migration()
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    sa.event.listen(engine, "connect", _enable_foreign_keys)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE admins (id INTEGER PRIMARY KEY, username VARCHAR(34) NOT NULL)"
            )
        )
        connection.execute(
            sa.text(
                "CREATE TABLE admin_user_plans (id INTEGER PRIMARY KEY, name VARCHAR(128) NOT NULL)"
            )
        )
        connection.execute(
            sa.text(
                "CREATE TABLE access_groups (id INTEGER PRIMARY KEY, name VARCHAR(128) NOT NULL)"
            )
        )
        connection.execute(sa.text("INSERT INTO admins VALUES (1, 'owner')"))
        connection.execute(sa.text("INSERT INTO admin_user_plans VALUES (10, 'legacy-plan')"))
        connection.execute(sa.text("INSERT INTO access_groups VALUES (20, 'legacy-network')"))

        monkeypatch.setattr(
            migration,
            "op",
            Operations(MigrationContext.configure(connection)),
        )
        migration.upgrade()

        inspector = sa.inspect(connection)
        assert {"products", "product_inbounds", "product_hosts"} <= set(
            inspector.get_table_names()
        )
        assert connection.execute(sa.text("SELECT * FROM admin_user_plans")).all() == [
            (10, "legacy-plan")
        ]
        assert connection.execute(sa.text("SELECT * FROM access_groups")).all() == [
            (20, "legacy-network")
        ]
        connection.execute(
            sa.text(
                "INSERT INTO products "
                "(id, owner_admin_id, name, traffic_price_multiplier, created_at, updated_at) "
                "VALUES (100, 1, 'new-product', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        assert connection.execute(
            sa.text(
                "SELECT id, owner_admin_id, name, traffic_price_multiplier FROM products"
            )
        ).one() == (100, 1, "new-product", 1)


def test_product_migration_upgrades_clean_database_and_can_be_reapplied(
    monkeypatch, tmp_path
):
    """Exercise the Product migration on a disposable, empty installation DB."""
    migration = _migration()
    database_path = tmp_path / "fresh-product-install.sqlite3"
    engine = sa.create_engine(f"sqlite+pysqlite:///{database_path}")
    sa.event.listen(engine, "connect", _enable_foreign_keys)

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE admins (id INTEGER PRIMARY KEY, username VARCHAR(34) NOT NULL)"
            )
        )
        monkeypatch.setattr(
            migration,
            "op",
            Operations(MigrationContext.configure(connection)),
        )

        migration.upgrade()
        inspector = sa.inspect(connection)
        assert {"products", "product_inbounds", "product_hosts"} <= set(
            inspector.get_table_names()
        )
        assert set(column["name"] for column in inspector.get_columns("products")) == {
            "id",
            "owner_admin_id",
            "name",
            "description",
            "traffic_price_multiplier",
            "archived_at",
            "created_at",
            "updated_at",
        }

        migration.downgrade()
        assert {"products", "product_inbounds", "product_hosts"}.isdisjoint(
            sa.inspect(connection).get_table_names()
        )
        migration.upgrade()
        assert {"products", "product_inbounds", "product_hosts"} <= set(
            sa.inspect(connection).get_table_names()
        )


def test_product_migration_is_new_head_and_does_not_mutate_legacy_tables():
    source = MIGRATION_PATH.read_text(encoding="utf-8")
    assert 'down_revision = "a4c2e1f8b7d9"' in source
    assert "op.create_table(\n        \"products\"" in source
    assert "op.create_table(\n        \"product_inbounds\"" in source
    assert "op.create_table(\n        \"product_hosts\"" in source
    for legacy_table in ("admin_user_plans", "access_groups", "users"):
        assert f'op.drop_table("{legacy_table}")' not in source
        assert f'op.alter_column("{legacy_table}"' not in source
