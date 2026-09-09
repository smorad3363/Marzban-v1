from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    Admin as DBAdmin,
    AdminHierarchy,
    AdminHierarchySettings,
    AdminRole,
    SystemOwner,
    User,
)
from app.models.admin import Admin as APIAdmin
from app.models.user import UserStatus
from app.routers import user_summary
from app.utils import marzhelp_policy


def _db(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'user-summary.sqlite3'}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)()


def _api_admin(admin: DBAdmin) -> APIAdmin:
    return APIAdmin.model_validate(admin)


def test_user_summary_is_hierarchy_scoped_and_uses_shared_attention_thresholds(
    tmp_path,
    monkeypatch,
):
    engine, db = _db(tmp_path)
    try:
        monkeypatch.setattr(
            marzhelp_policy,
            "allowed_inbound_tags",
            lambda _db, _admin: None,
        )
        monkeypatch.setattr(user_summary, "NOTIFY_DAYS_LEFT", [3, 7])
        monkeypatch.setattr(user_summary, "NOTIFY_REACHED_USAGE_PERCENT", [95, 80])

        db.add_all(
            [
                AdminRole(id=1, code="OWNER"),
                AdminRole(id=2, code="SUPER_ADMIN"),
                AdminRole(id=3, code="ADMIN"),
                AdminHierarchySettings(id=1, enabled=True, max_depth=64),
            ]
        )
        owner = DBAdmin(
            username="owner",
            hashed_password="x",
            is_sudo=True,
            role_id=1,
        )
        manager = DBAdmin(
            username="manager",
            hashed_password="x",
            is_sudo=False,
            role_id=3,
            parent=owner,
        )
        child = DBAdmin(
            username="child",
            hashed_password="x",
            is_sudo=False,
            role_id=3,
            parent=manager,
        )
        sibling = DBAdmin(
            username="sibling",
            hashed_password="x",
            is_sudo=False,
            role_id=3,
            parent=owner,
        )
        db.add_all([owner, manager, child, sibling])
        db.flush()
        db.add(SystemOwner(id=1, admin_id=owner.id))
        db.add_all(
            [
                AdminHierarchy(ancestor_id=owner.id, descendant_id=owner.id, depth=0),
                AdminHierarchy(ancestor_id=owner.id, descendant_id=manager.id, depth=1),
                AdminHierarchy(ancestor_id=owner.id, descendant_id=child.id, depth=2),
                AdminHierarchy(ancestor_id=owner.id, descendant_id=sibling.id, depth=1),
                AdminHierarchy(ancestor_id=manager.id, descendant_id=manager.id, depth=0),
                AdminHierarchy(ancestor_id=manager.id, descendant_id=child.id, depth=1),
                AdminHierarchy(ancestor_id=child.id, descendant_id=child.id, depth=0),
                AdminHierarchy(ancestor_id=sibling.id, descendant_id=sibling.id, depth=0),
            ]
        )

        now = datetime.now(timezone.utc)
        db.add_all(
            [
                User(
                    username="near-high-online",
                    admin_id=manager.id,
                    status=UserStatus.active,
                    used_traffic=90,
                    data_limit=100,
                    expire=int((now + timedelta(days=2)).timestamp()),
                    online_at=(now - timedelta(hours=1)).replace(tzinfo=None),
                ),
                User(
                    username="child-online",
                    admin_id=child.id,
                    status=UserStatus.active,
                    used_traffic=10,
                    data_limit=100,
                    expire=int((now + timedelta(days=30)).timestamp()),
                    online_at=(now - timedelta(hours=2)).replace(tzinfo=None),
                ),
                User(
                    username="scoped-stale",
                    admin_id=manager.id,
                    status=UserStatus.disabled,
                    used_traffic=0,
                    data_limit=None,
                    expire=None,
                    online_at=(now - timedelta(days=2)).replace(tzinfo=None),
                ),
                User(
                    username="outside-high-online",
                    admin_id=sibling.id,
                    status=UserStatus.active,
                    used_traffic=99,
                    data_limit=100,
                    expire=int((now + timedelta(days=1)).timestamp()),
                    online_at=(now - timedelta(minutes=10)).replace(tzinfo=None),
                ),
            ]
        )
        db.commit()

        scoped = user_summary.get_users_summary(db=db, admin=_api_admin(manager))
        assert scoped.total_users == 3
        assert scoped.online_users == 2
        assert scoped.expiring_users == 1
        assert scoped.high_usage_users == 1
        assert scoped.online_window_hours == 24
        assert scoped.expiring_within_days == 7
        assert scoped.high_usage_threshold_percent == 80

        global_summary = user_summary.get_users_summary(db=db, admin=_api_admin(owner))
        assert global_summary.total_users == 4
        assert global_summary.online_users == 3
        assert global_summary.expiring_users == 2
        assert global_summary.high_usage_users == 2
    finally:
        db.close()
        engine.dispose()
