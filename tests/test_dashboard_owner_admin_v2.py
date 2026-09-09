from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    Admin,
    AdminAccountStatus,
    DeviceLimitUserState,
    MarzhelpAdminSettings,
    Node,
    NodeUserUsage,
    User,
)
from app.models.node import NodeStatus
from app.models.user import UserStatus
from app.utils import dashboard_metrics


def _db(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'dashboard-v2.sqlite3'}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)()


def _settings(admin_id: int, *, status_id: int = 1):
    return MarzhelpAdminSettings(
        admin_id=admin_id,
        billing_mode="USED_TRAFFIC",
        account_status_id=status_id,
    )


def test_admin_dashboard_is_scoped_and_uses_real_usage_history(tmp_path):
    engine, db = _db(tmp_path)
    try:
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        owner = Admin(username="owner", hashed_password="x", is_sudo=True)
        admin = Admin(username="admin", hashed_password="x", is_sudo=False)
        other = Admin(username="other", hashed_password="x", is_sudo=False)
        db.add_all([owner, admin, other])
        db.flush()
        db.add_all([
            AdminAccountStatus(id=1, code="ACTIVE"),
            AdminAccountStatus(id=2, code="SUSPENDED"),
            AdminAccountStatus(id=3, code="DISABLED"),
            _settings(owner.id),
            _settings(admin.id),
            _settings(other.id, status_id=2),
        ])
        scoped = User(
            username="scoped",
            admin_id=admin.id,
            status=UserStatus.active,
            used_traffic=95,
            data_limit=100,
            online_at=now.replace(tzinfo=None) - timedelta(seconds=20),
            created_at=now.replace(tzinfo=None) - timedelta(hours=1),
        )
        expired = User(
            username="expired",
            admin_id=admin.id,
            status=UserStatus.expired,
            used_traffic=20,
            data_limit=100,
            online_at=now.replace(tzinfo=None) - timedelta(minutes=5),
            created_at=now.replace(tzinfo=None) - timedelta(hours=2),
        )
        outside = User(
            username="outside",
            admin_id=other.id,
            status=UserStatus.active,
            used_traffic=5_000,
            data_limit=10_000,
            online_at=now.replace(tzinfo=None) - timedelta(seconds=10),
            created_at=now.replace(tzinfo=None),
        )
        db.add_all([scoped, expired, outside])
        db.flush()
        hour = now.replace(tzinfo=None, minute=0, second=0, microsecond=0)
        db.add_all([
            NodeUserUsage(user_id=scoped.id, node_id=None, created_at=hour, used_traffic=123),
            NodeUserUsage(user_id=outside.id, node_id=None, created_at=hour, used_traffic=999),
            DeviceLimitUserState(
                user_id=scoped.id,
                penalty_status="warning",
                violation_count=1,
                current_stage=1,
                active_ip_count=2,
            ),
        ])
        db.commit()

        result = dashboard_metrics.overview(
            db,
            admin,
            timezone_offset_minutes=0,
            traffic_range="24h",
            now=now,
        )

        assert result.role == "ADMIN"
        assert result.total_users == 2
        assert result.online_users == 1
        assert result.today_traffic == 123
        assert result.traffic_history[-1].total_traffic == 123
        assert [item.username for item in result.top_consumers] == ["scoped", "expired"]
        assert "outside" not in {item.username for item in result.recent_users}
        assert result.attention_count == 2
        assert {item.username for item in result.attention_users} == {"scoped", "expired"}
        assert next(item for item in result.attention_users if item.username == "scoped").reason_code == "device_limit"
        assert result.node_summary is None
        assert result.admin_summary is None
    finally:
        db.close()
        engine.dispose()


def test_owner_dashboard_adds_global_node_and_admin_summaries(tmp_path):
    engine, db = _db(tmp_path)
    try:
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        owner = Admin(username="owner", hashed_password="x", is_sudo=True)
        active_admin = Admin(username="active-admin", hashed_password="x")
        suspended_admin = Admin(username="suspended-admin", hashed_password="x")
        db.add_all([owner, active_admin, suspended_admin])
        db.flush()
        db.add_all([
            AdminAccountStatus(id=1, code="ACTIVE"),
            AdminAccountStatus(id=2, code="SUSPENDED"),
            AdminAccountStatus(id=3, code="DISABLED"),
            _settings(owner.id),
            _settings(active_admin.id),
            _settings(suspended_admin.id, status_id=2),
            Node(name="healthy", address="127.0.0.1", port=62050, api_port=62051, status=NodeStatus.connected),
            Node(name="retrying", address="127.0.0.2", port=62052, api_port=62053, status=NodeStatus.connecting),
            Node(name="failed", address="127.0.0.3", port=62054, api_port=62055, status=NodeStatus.error),
        ])
        db.add_all([
            User(username="one", admin_id=active_admin.id, status=UserStatus.active, used_traffic=10, data_limit=100),
            User(username="two", admin_id=suspended_admin.id, status=UserStatus.disabled, used_traffic=20, data_limit=100),
        ])
        db.commit()

        result = dashboard_metrics.overview(
            db,
            owner,
            timezone_offset_minutes=0,
            traffic_range="7d",
            now=now,
        )

        assert result.role == "OWNER"
        assert result.total_users == 2
        assert result.node_summary is not None
        assert result.node_summary.total == 3
        assert result.node_summary.healthy == 1
        assert result.node_summary.reconnecting == 1
        assert result.node_summary.error == 1
        assert result.admin_summary is not None
        assert result.admin_summary.total == 2
        assert result.admin_summary.active == 1
        assert result.admin_summary.suspended == 1
    finally:
        db.close()
        engine.dispose()
