"""index Access Group hosts for reverse host lookups

Revision ID: c9e1f4a7b203
Revises: b8d5f0a3c721
"""

from alembic import op


revision = "c9e1f4a7b203"
down_revision = "b8d5f0a3c721"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_access_group_hosts_host_group",
        "access_group_hosts",
        ["host_id", "access_group_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_access_group_hosts_host_group",
        table_name="access_group_hosts",
    )
