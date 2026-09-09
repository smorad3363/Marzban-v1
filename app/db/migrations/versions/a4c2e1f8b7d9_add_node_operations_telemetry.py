"""add Node Operations telemetry persistence

Revision ID: a4c2e1f8b7d9
Revises: e7b1c4d9a213
"""

from alembic import op
import sqlalchemy as sa


revision = "a4c2e1f8b7d9"
down_revision = "e7b1c4d9a213"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "node_events",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "node_id",
            sa.Integer(),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("trigger_reason", sa.String(length=64), nullable=True),
        sa.Column("root_cause", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("sanitized_message", sa.String(length=1024), nullable=True),
        sa.Column("previous_state", sa.String(length=32), nullable=True),
        sa.Column("new_state", sa.String(length=32), nullable=True),
        sa.Column("reconnect_mode", sa.String(length=16), nullable=True),
        sa.Column("reconnect_attempt", sa.Integer(), nullable=True),
        sa.Column("reconnect_result", sa.String(length=16), nullable=True),
        sa.Column("downtime_seconds", sa.Integer(), nullable=True),
        sa.Column("runtime_version", sa.String(length=64), nullable=True),
        sa.Column("runtime_stream_id", sa.String(length=64), nullable=True),
        sa.Column("runtime_event_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "node_id",
            "runtime_stream_id",
            "runtime_event_id",
            name="uq_node_events_runtime_identity",
        ),
    )
    op.create_index(
        "ix_node_events_node_occurred",
        "node_events",
        ["node_id", "occurred_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_node_events_type_occurred",
        "node_events",
        ["event_type", "occurred_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_node_events_severity_occurred",
        "node_events",
        ["severity", "occurred_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_node_events_received",
        "node_events",
        ["received_at", "id"],
        unique=False,
    )

    op.create_table(
        "node_traffic_buckets",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "node_id",
            sa.Integer(),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bucket_start", sa.DateTime(), nullable=False),
        sa.Column("uplink_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("downlink_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sample_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "node_id",
            "bucket_start",
            name="uq_node_traffic_node_bucket",
        ),
    )
    op.create_index(
        "ix_node_traffic_node_bucket",
        "node_traffic_buckets",
        ["node_id", "bucket_start", "id"],
        unique=False,
    )
    op.create_index(
        "ix_node_traffic_bucket_start",
        "node_traffic_buckets",
        ["bucket_start", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_node_traffic_bucket_start", table_name="node_traffic_buckets")
    op.drop_index("ix_node_traffic_node_bucket", table_name="node_traffic_buckets")
    op.drop_table("node_traffic_buckets")

    op.drop_index("ix_node_events_received", table_name="node_events")
    op.drop_index("ix_node_events_severity_occurred", table_name="node_events")
    op.drop_index("ix_node_events_type_occurred", table_name="node_events")
    op.drop_index("ix_node_events_node_occurred", table_name="node_events")
    op.drop_table("node_events")
