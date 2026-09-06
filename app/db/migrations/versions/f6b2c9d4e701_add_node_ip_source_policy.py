"""add trusted client IP source policy to nodes

Revision ID: f6b2c9d4e701
Revises: c9e1f4a7b203
"""

from alembic import op
import sqlalchemy as sa


revision = "f6b2c9d4e701"
down_revision = "c9e1f4a7b203"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "nodes",
        sa.Column("ip_source_mode", sa.String(24), nullable=False, server_default="direct"),
    )
    op.add_column("nodes", sa.Column("cdn_provider", sa.String(24), nullable=True))
    op.add_column("nodes", sa.Column("trusted_proxy_cidrs", sa.JSON(), nullable=True))
    op.create_check_constraint(
        "ck_nodes_ip_source_mode",
        "nodes",
        "ip_source_mode IN ('direct','trusted_xff','proxy_protocol')",
    )
    op.create_check_constraint(
        "ck_nodes_cdn_provider",
        "nodes",
        "cdn_provider IS NULL OR cdn_provider IN ('cloudflare','custom')",
    )


def downgrade():
    op.drop_constraint("ck_nodes_cdn_provider", "nodes", type_="check")
    op.drop_constraint("ck_nodes_ip_source_mode", "nodes", type_="check")
    op.drop_column("nodes", "trusted_proxy_cidrs")
    op.drop_column("nodes", "cdn_provider")
    op.drop_column("nodes", "ip_source_mode")
