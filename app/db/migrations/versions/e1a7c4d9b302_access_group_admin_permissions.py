"""add Access Group administrator permissions

Revision ID: e1a7c4d9b302
Revises: f6b2c9d4e701
"""

from alembic import op
import sqlalchemy as sa


revision = "e1a7c4d9b302"
down_revision = "f6b2c9d4e701"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "access_group_admin_access",
        sa.Column(
            "access_group_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("access_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "admin_id",
            sa.Integer(),
            sa.ForeignKey("admins.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_access_group_admin_access_admin_group",
        "access_group_admin_access",
        ["admin_id", "access_group_id"],
        unique=False,
    )


def downgrade():
    # MySQL may use the explicit composite index to satisfy the admin_id
    # foreign-key requirement. Dropping that index before the table therefore
    # fails with error 1553. Dropping the table removes its indexes and foreign
    # keys atomically on all supported databases.
    op.drop_table("access_group_admin_access")
