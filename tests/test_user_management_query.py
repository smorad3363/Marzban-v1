from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    Admin as DBAdmin,
    AdminHierarchy,
    AdminHierarchySettings,
    AdminRole,
    AdminUserPlan,
    AdminUserPlanVersion,
    DeviceLimitUserState,
    SystemOwner,
    User,
    UserPlanAssignment,
)
from app.models.admin import Admin as APIAdmin
from app.models.user import UserStatus
from app.utils import marzhelp_policy, user_management


def _db(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'user-management.sqlite3'}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)()


def _api_admin(admin: DBAdmin) -> APIAdmin:
    return APIAdmin.model_validate(admin)


def _seed_hierarchy(db):
    db.add_all(
        [
            AdminRole(id=1, code="OWNER"),
            AdminRole(id=2, code="SUPER_ADMIN"),
            AdminRole(id=3, code="ADMIN"),
            AdminHierarchySettings(id=1, enabled=True, max_depth=64),
        ]
    )
    owner = DBAdmin(username="owner", hashed_password="x", is_sudo=True, role_id=1)
    manager = DBAdmin(username="manager", hashed_password="x", role_id=3, parent=owner)
    child = DBAdmin(username="child", hashed_password="x", role_id=3, parent=manager)
    sibling = DBAdmin(username="sibling", hashed_password="x", role_id=3, parent=owner)
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
    return owner, manager, child, sibling


def _plan(db, owner: DBAdmin, name: str, *, trial: bool = False):
    plan = AdminUserPlan(owner_admin_id=owner.id, name=name, is_trial=trial)
    db.add(plan)
    db.flush()
    version = AdminUserPlanVersion(
        plan_id=plan.id,
        version_number=1,
        price_toman=0,
        data_limit=100,
        duration_days=30,
        concurrent_user_limit=None,
        reset_strategy="no_reset",
        renewal_volume_strategy="replace",
        renewal_time_strategy="extend_max",
        created_by_admin_id=owner.id,
    )
    db.add(version)
    db.flush()
    plan.current_version_id = version.id
    return plan, version


def _assign(db, user: User, plan, version, actor: DBAdmin, key: str, *, trial=False):
    assignment = UserPlanAssignment(
        user_id=user.id,
        plan_id=plan.id,
        version_id=version.id,
        actor_admin_id=actor.id,
        operation_type="create",
        is_trial=trial,
        idempotency_key=key,
    )
    db.add(assignment)
    db.flush()
    return assignment


def test_management_query_preserves_scope_and_plan_filters(tmp_path, monkeypatch):
    engine, db = _db(tmp_path)
    try:
        monkeypatch.setattr(marzhelp_policy, "allowed_inbound_tags", lambda _db, _admin: None)
        owner, manager, child, sibling = _seed_hierarchy(db)
        standard, standard_v = _plan(db, owner, "Standard")
        premium, premium_v = _plan(db, owner, "Premium")
        trial_plan, trial_v = _plan(db, owner, "Trial", trial=True)

        standard_user = User(username="standard-user", admin_id=manager.id, status=UserStatus.active)
        latest_user = User(username="latest-user", admin_id=manager.id, status=UserStatus.active)
        trial_user = User(username="trial-user", admin_id=child.id, status=UserStatus.active)
        no_plan_user = User(username="no-plan-user", admin_id=manager.id, status=UserStatus.active)
        outside = User(username="outside", admin_id=sibling.id, status=UserStatus.active)
        db.add_all([standard_user, latest_user, trial_user, no_plan_user, outside])
        db.flush()
        _assign(db, standard_user, standard, standard_v, manager, "standard-1")
        _assign(db, latest_user, standard, standard_v, manager, "latest-old")
        _assign(db, latest_user, premium, premium_v, manager, "latest-new")
        _assign(db, trial_user, trial_plan, trial_v, child, "trial-1", trial=True)
        _assign(db, outside, premium, premium_v, sibling, "outside-1")
        db.commit()

        actor = _api_admin(manager)
        all_scoped = user_management.scoped_query(db, actor).all()
        assert {user.username for user in all_scoped} == {
            "standard-user",
            "latest-user",
            "trial-user",
            "no-plan-user",
        }

        standard_only = user_management.scoped_query(db, actor, plan_id=standard.id).all()
        assert {user.username for user in standard_only} == {"standard-user"}

        premium_only = user_management.scoped_query(db, actor, plan_id=premium.id).all()
        assert {user.username for user in premium_only} == {"latest-user"}

        without_plan = user_management.scoped_query(db, actor, without_plan=True).all()
        assert {user.username for user in without_plan} == {"no-plan-user"}

        trials = user_management.scoped_query(db, actor, trial=True).all()
        assert {user.username for user in trials} == {"trial-user"}

        page, total = user_management.page_users(
            user_management.scoped_query(db, actor),
            offset=0,
            limit=10,
            sort_options=None,
        )
        assert total == 4
        meta = user_management.plan_meta_for_users(db, page)
        assert meta["standard-user"].plan_name == "Standard"
        assert meta["latest-user"].plan_name == "Premium"
        assert meta["trial-user"].is_trial is True
        assert meta["no-plan-user"] is None
    finally:
        db.close()
        engine.dispose()


def test_management_smart_filters_use_real_user_and_device_fields(tmp_path, monkeypatch):
    engine, db = _db(tmp_path)
    try:
        monkeypatch.setattr(marzhelp_policy, "allowed_inbound_tags", lambda _db, _admin: None)
        monkeypatch.setattr(user_management, "NOTIFY_DAYS_LEFT", [3, 7])
        monkeypatch.setattr(user_management, "NOTIFY_REACHED_USAGE_PERCENT", [95, 80])
        owner, manager, child, _ = _seed_hierarchy(db)
        now = datetime.now(timezone.utc)

        near_high = User(
            username="near-high",
            admin_id=manager.id,
            status=UserStatus.active,
            expire=int((now + timedelta(days=2)).timestamp()),
            used_traffic=90,
            data_limit=100,
            concurrent_user_limit=2,
            online_at=(now - timedelta(hours=2)).replace(tzinfo=None),
        )
        unlimited_inactive = User(
            username="unlimited-inactive",
            admin_id=child.id,
            status=UserStatus.active,
            data_limit=None,
            online_at=(now - timedelta(days=10)).replace(tzinfo=None),
        )
        limited = User(
            username="limited-user",
            admin_id=manager.id,
            status=UserStatus.limited,
            data_limit=100,
            used_traffic=20,
        )
        warned = User(
            username="warned-user",
            admin_id=manager.id,
            status=UserStatus.active,
            data_limit=100,
            used_traffic=10,
        )
        db.add_all([near_high, unlimited_inactive, limited, warned])
        db.flush()
        db.add(
            DeviceLimitUserState(
                user_id=warned.id,
                penalty_status="warning",
                violation_count=1,
                current_stage=1,
            )
        )
        db.commit()

        actor = _api_admin(manager)
        expiring = user_management.scoped_query(db, actor, expires_within_days=7).all()
        assert {user.username for user in expiring} == {"near-high"}

        high_usage = user_management.scoped_query(db, actor, usage_percent_min=80).all()
        assert {user.username for user in high_usage} == {"near-high"}

        device_limited = user_management.scoped_query(db, actor, has_device_limit=True).all()
        assert {user.username for user in device_limited} == {"near-high"}

        unlimited = user_management.scoped_query(db, actor, unlimited_traffic=True).all()
        assert {user.username for user in unlimited} == {"unlimited-inactive"}

        inactive = user_management.scoped_query(db, actor, inactive_hours=24 * 7).all()
        assert {user.username for user in inactive} == {
            "unlimited-inactive",
            "limited-user",
            "warned-user",
        }

        attention = user_management.scoped_query(db, actor, attention=True).all()
        assert {user.username for user in attention} == {
            "near-high",
            "limited-user",
            "warned-user",
        }
    finally:
        db.close()
        engine.dispose()
