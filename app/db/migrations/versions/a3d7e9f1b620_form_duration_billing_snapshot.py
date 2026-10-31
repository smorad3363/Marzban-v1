"""Persist Form duration coefficients without rewriting existing usage or wallets."""
from alembic import op
import sqlalchemy as sa

revision = "a3d7e9f1b620"
down_revision = "f31a6c9d2e70"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table, columns in {
        "users": [
            sa.Column("form_duration_days", sa.Integer(), nullable=True),
            sa.Column("duration_multiplier_basis_points", sa.Integer(), nullable=False, server_default="10000"),
        ],
        "marzhelp_admin_settings": [
            sa.Column("usage_billing_fraction", sa.Integer(), nullable=False, server_default="0"),
        ],
    }.items():
        existing = {c["name"] for c in sa.inspect(bind).get_columns(table)}
        for column in columns:
            if column.name not in existing:
                op.add_column(table, column)


def downgrade():
    op.drop_column("marzhelp_admin_settings", "usage_billing_fraction")
    op.drop_column("users", "duration_multiplier_basis_points")
    op.drop_column("users", "form_duration_days")
