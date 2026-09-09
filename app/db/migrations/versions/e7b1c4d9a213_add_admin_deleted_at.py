"""add Admin retirement marker

Revision ID: e7b1c4d9a213
Revises: e1a7c4d9b302
"""
from alembic import op
import sqlalchemy as sa

revision = "e7b1c4d9a213"
down_revision = "e1a7c4d9b302"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("admins", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index("ix_admins_deleted_at", "admins", ["deleted_at"], unique=False)


def downgrade():
    op.drop_index("ix_admins_deleted_at", table_name="admins")
    op.drop_column("admins", "deleted_at")
