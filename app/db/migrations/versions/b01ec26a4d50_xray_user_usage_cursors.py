"""Persist transactional non-resetting Xray user traffic cursors.

Revision ID: b01ec26a4d50
Revises: a4c2e1f8b7d9
"""

from alembic import op
import sqlalchemy as sa

revision = "b01ec26a4d50"
down_revision = "a4c2e1f8b7d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xray_user_usage_cursors",
        sa.Column("node_key", sa.String(length=64), nullable=False),
        sa.Column("account_name", sa.String(length=191), nullable=False),
        sa.Column("uplink", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("downlink", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("uptime_seconds", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sampled_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("node_key", "account_name"),
    )


def downgrade() -> None:
    op.drop_table("xray_user_usage_cursors")
