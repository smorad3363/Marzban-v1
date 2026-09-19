"""Add the Product identity and explicit Inbound/Host network catalog.

Revision ID: f7a3c9e1d205
Revises: a4c2e1f8b7d9
"""

from alembic import op
import sqlalchemy as sa


revision = "f7a3c9e1d205"
down_revision = "a4c2e1f8b7d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "owner_admin_id",
            sa.Integer(),
            sa.ForeignKey("admins.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column(
            "traffic_price_multiplier",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            server_default="1",
        ),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "traffic_price_multiplier > 0",
            name="ck_products_traffic_price_multiplier_positive",
        ),
        sa.UniqueConstraint(
            "owner_admin_id",
            "name",
            name="uq_products_owner_name",
        ),
    )
    op.create_index(
        "ix_products_owner_active",
        "products",
        ["owner_admin_id", "archived_at", "id"],
    )

    op.create_table(
        "product_inbounds",
        sa.Column(
            "product_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("inbound_tag", sa.String(length=256), primary_key=True),
    )

    op.create_table(
        "product_hosts",
        sa.Column(
            "product_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
        ),
        sa.Column("inbound_tag", sa.String(length=256), primary_key=True),
        sa.Column("host_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(
            ["product_id", "inbound_tag"],
            ["product_inbounds.product_id", "product_inbounds.inbound_tag"],
            ondelete="CASCADE",
            name="fk_product_hosts_product_inbound",
        ),
    )
    op.create_index(
        "ix_product_hosts_host_product",
        "product_hosts",
        ["host_id", "product_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_hosts_host_product", table_name="product_hosts")
    op.drop_table("product_hosts")
    op.drop_table("product_inbounds")
    op.drop_index("ix_products_owner_active", table_name="products")
    op.drop_table("products")
