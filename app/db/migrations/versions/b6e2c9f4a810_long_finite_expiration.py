"""Keep finite durations past 2038 representable; retire unlimited-time permission."""
from alembic import op
import sqlalchemy as sa

revision = "b6e2c9f4a810"
down_revision = "a3d7e9f1b620"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table in ("users", "next_plans"):
        column = next(c for c in sa.inspect(bind).get_columns(table) if c["name"] == "expire")
        if not isinstance(column["type"], sa.BigInteger):
            with op.batch_alter_table(table) as batch:
                batch.alter_column("expire", existing_type=column["type"], type_=sa.BigInteger(), existing_nullable=True)
    bind.execute(sa.text("UPDATE owner_commercial_policy SET allow_unlimited_duration = 0 WHERE allow_unlimited_duration <> 0"))


def downgrade():
    bind = op.get_bind()
    for table in ("users", "next_plans"):
        if bind.execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE expire > 2147483647 OR expire < -2147483648")).scalar():
            raise RuntimeError("Cannot narrow expiration while long finite dates exist")
    for table in ("users", "next_plans"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column("expire", existing_type=sa.BigInteger(), type_=sa.Integer(), existing_nullable=True)
