"""Regressions from observed live Admin failures; production disables autoflush."""
from datetime import datetime, timedelta, timezone
import importlib.util

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import BackgroundTasks
from starlette.requests import Request

from app.db.models import Admin, MarzhelpAdminSubscriptionModePermission, AdminAccountAlert, AdminMoneyTransaction, AdminSuspensionUser, MarzhelpAdminSettings, OwnerDurationPreset, User, UserPlanAssignment
from app.models.admin import Admin as APIAdmin, ManagedAdminCreate, MarzhelpAdminPolicy
from app.models.admin_hierarchy import PlanCreate, PlanVersionInput
from app.models.user import UserStatus
from app.routers import admin as admin_api, admin_hierarchy as hierarchy_api
from app.utils import admin_hierarchy, admin_plans, financial_controls, money_billing, owner_pricing, trials
from test_financial_controls import tree
from test_stage6_trials import db as trial_db


def request():
    return Request({"type": "http", "method": "POST", "path": "/api/admin-management", "headers": []})


def test_initial_credit_and_repeated_grants_survive_reload_and_replay(tree):
    db, owner, _, _, _ = tree
    result = admin_api.create_managed_admin(request(), ManagedAdminCreate(
        username="funded-new", password="secret123", initial_money_credit_toman=10000,
        policy=MarzhelpAdminPolicy(billing_mode="ALLOCATED_TRAFFIC"),
    ), db, APIAdmin(username=owner.username, is_sudo=True))
    settings = db.get(MarzhelpAdminSettings, result.id)
    assert result.policy.money_balance_toman == settings.money_balance_toman == 10000
    child = db.get(Admin, result.id)
    for i in range(2):
        money_billing.transfer_money(db, actor=owner, parent=owner, child=child, amount_toman=1000,
                                     operation_type="grant", idempotency_key=f"grant-repeat-{i}")
        db.commit(); db.refresh(settings)
        assert settings.money_balance_toman == 11000 + i * 1000
    _, created = money_billing.transfer_money(db, actor=owner, parent=owner, child=child, amount_toman=1000,
                                             operation_type="grant", idempotency_key="grant-repeat-1")
    assert not created and settings.money_balance_toman == 12000
    assert sum(r.delta_toman for r in db.query(AdminMoneyTransaction).filter_by(admin_id=child.id)) == 12000


def test_legacy_debt_suspension_has_resume_action_and_restores_only_valid_users(tree):
    db, owner, child, active, settings = tree
    db.add(MarzhelpAdminSubscriptionModePermission(admin_id=child.id, mode="limited_traffic_unlimited_devices")); db.commit()
    expired = User(username="legacy-expired", admin_id=child.id, status=UserStatus.active, expire=1)
    manual = User(username="legacy-manual", admin_id=child.id, status=UserStatus.active)
    db.add_all([expired, manual]); db.commit()
    admin_hierarchy.suspend_admin(db, actor=owner, target=child, reason_id=2)
    db.refresh(settings)
    response = admin_api.managed_admin_response(db, child, settings)
    assert response.account_status == "SUSPENDED" and response.active_owner_freeze_event_id is None
    financial_controls.mark_manual_status(db, manual); db.commit()
    admin_hierarchy.resume_admin(db, actor=owner, target=child)
    assert settings.account_status_id == 1 and active.status == UserStatus.active
    assert expired.status == UserStatus.expired and manual.status == UserStatus.disabled


def test_legacy_resume_refuses_debt_and_owner_freeze(tree):
    db, owner, child, _, settings = tree
    db.add(MarzhelpAdminSubscriptionModePermission(admin_id=child.id, mode="limited_traffic_unlimited_devices")); db.commit()
    admin_hierarchy.suspend_admin(db, actor=owner, target=child, reason_id=2)
    db.refresh(settings)
    settings.money_balance_toman = -400; db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError, match="condition is still active"):
        admin_hierarchy.resume_admin(db, actor=owner, target=child)
    db.rollback()
    settings.money_balance_toman = 1000; db.commit()
    admin_hierarchy.resume_admin(db, actor=owner, target=child)
    event, _ = admin_hierarchy.freeze_admin(db, actor=owner, target=child, reason_id=1, idempotency_key="manual-freeze-regression")
    assert admin_api.managed_admin_response(db, child, settings).active_owner_freeze_event_id == event.id
    with pytest.raises(admin_hierarchy.HierarchyError, match="Owner Freeze"):
        admin_hierarchy.resume_admin(db, actor=owner, target=child)


def test_alerts_return_scoped_admin_usernames(tree):
    db, owner, child, _, _ = tree
    db.add(AdminAccountAlert(admin_id=child.id, event_key="low-credit-name", kind="low")); db.commit()
    result = hierarchy_api.requests_alerts(None, None, db, APIAdmin(username=owner.username, is_sudo=True))
    assert result['alerts'][0]['admin_username'] == child.username
    assert result['alerts'][0]['admin_id'] == child.id


@pytest.mark.parametrize('days', [1,30,31,45,59,60,180,365,1000])
def test_arbitrary_days_use_capped_daily_curve(tree, days):
    db, _, _, _, settings = tree
    db.add_all([OwnerDurationPreset(duration_days=30, multiplier_basis_points=10000), OwnerDurationPreset(duration_days=60, multiplier_basis_points=13000, enabled=False)])
    db.commit()
    expire = int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())
    factor = owner_pricing.duration_multiplier_basis_points(days)
    assert owner_pricing.duration_preset(db, expire).multiplier_basis_points == factor
    assert owner_pricing.form_price(db, settings, data_limit=1024**3, expire=expire) == (factor + 9) // 10
    assert owner_pricing.duration_days_preset(db, 100000).multiplier_basis_points == 12000


def test_usage_factor_settles_exactly_without_changing_real_usage(tree):
    db, _, child, user, settings = tree
    settings.billing_mode = "USED_TRAFFIC"
    settings.used_traffic_price_per_gib_toman = 1000
    settings.money_balance_toman = 10000
    settings.usage_billing_remainder = 0; db.commit()
    original_usage = user.used_traffic
    # Fractional samples must give the same result as one full GiB at 1.3x.
    for value in [1, 3, 1024**3 - 4]:
        money_billing.settle_used_traffic(db, {child.id: value}, weighted_usage={child.id: value * 13000})
        db.commit()
    assert settings.money_balance_toman == 8700
    assert settings.usage_billing_remainder == settings.usage_billing_fraction == 0
    assert user.used_traffic == original_usage


def test_trial_can_renew_once_per_quota_and_cannot_convert_paid_user(trial_db):
    db, owner, tag, host, group_id = trial_db
    plan = admin_plans.create_plan(db, owner, PlanCreate(name="renewable trial", is_trial=True, version=PlanVersionInput(data_limit=1024**3, duration_days=1)))
    user, _, _ = admin_plans.create_user_from_plan(db, actor=owner, plan_id=plan.id, username="trial-renew", status="active", note=None, idempotency_key="trial-new-renew", access_group_id=group_id)
    settings = db.get(MarzhelpAdminSettings, owner.id)
    before, expire = settings.trial_quota, user.expire
    user.used_traffic = 123; db.commit()
    _, assignment, changed = admin_plans.renew_user_from_plan(db, actor=owner, user=user, plan_id=plan.id, idempotency_key="trial-renew-once")
    assert changed and assignment.is_trial and settings.trial_quota == before - 1
    assert user.expire == expire + 86400 and user.used_traffic == 0
    assert user.lifetime_used_traffic == 123
    assert not admin_plans.renew_user_from_plan(db, actor=owner, user=user, plan_id=plan.id, idempotency_key="trial-renew-once")[2]
    assert settings.trial_quota == before - 1
    settings.trial_quota = 0; db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError, match="quota is exhausted"):
        admin_plans.renew_user_from_plan(db, actor=owner, user=user, plan_id=plan.id, idempotency_key="trial-no-quota")
    db.rollback()
    assignment.is_trial = False; db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError, match="paid User"):
        admin_plans.renew_user_from_plan(db, actor=owner, user=user, plan_id=plan.id, idempotency_key="trial-cannot-free")


def test_trial_management_is_limited_to_requested_billing_modes(tree):
    db, owner, child, _, settings = tree
    settings.billing_mode = "USED_TRAFFIC"; db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError, match="only for Plan"):
        trials.adjust_quota(db, actor=owner, target=child, amount=5, operation="grant", idempotency_key="trial-used-block", note=None)
    for mode in ["ALLOCATED_TRAFFIC", "USER_CREDIT"]:
        settings.billing_mode = mode; db.commit()
        trials.adjust_quota(db, actor=owner, target=child, amount=5, operation="grant", idempotency_key=f"trial-grant-{mode}", note=None)
        db.commit()
        trials.consume_quota(db, child, settings); db.commit()
        trials.reset_quota(db, actor=owner, target=child, idempotency_key=f"trial-reset-{mode}", note=None); db.commit()
        assert settings.trial_quota == settings.trial_quota_limit and settings.trials_used == 0


def test_duration_migration_replay_preserves_existing_data():
    spec = importlib.util.spec_from_file_location('duration_migration', 'app/db/migrations/versions/a3d7e9f1b620_form_duration_billing_snapshot.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(sa.text('CREATE TABLE users (id INTEGER PRIMARY KEY, used_traffic BIGINT)'))
        connection.execute(sa.text('CREATE TABLE marzhelp_admin_settings (admin_id INTEGER PRIMARY KEY, money_balance_toman BIGINT, usage_billing_remainder BIGINT)'))
        connection.execute(sa.text('INSERT INTO users VALUES (1,123)'))
        connection.execute(sa.text('INSERT INTO marzhelp_admin_settings VALUES (1,456,789)'))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade(); module.upgrade()
        assert tuple(connection.execute(sa.text('SELECT used_traffic,form_duration_days,duration_multiplier_basis_points FROM users')).one()) == (123,None,10000)
        assert tuple(connection.execute(sa.text('SELECT money_balance_toman,usage_billing_remainder,usage_billing_fraction FROM marzhelp_admin_settings')).one()) == (456,789,0)


def test_lost_grant_repair_is_dry_run_audited_and_idempotent(tree):
    from scripts.repair_lost_wallet_grants import repair
    db, owner, child, _, settings = tree
    settings.money_balance_toman = 0
    for i, amount in enumerate([1000, 10000]):
        db.add(AdminMoneyTransaction(operation_key=f"lost-grant-{i}", operation_type="grant",
            admin_id=child.id, actor_admin_id=owner.id, counterparty_admin_id=owner.id,
            delta_toman=amount, balance_before=0, balance_after=amount))
    db.commit()
    assert repair(db, owner, child.username)['after'] == 11000
    assert settings.money_balance_toman == 0
    assert repair(db, owner, child.username, apply=True)['changed']
    db.commit()
    assert settings.money_balance_toman == 11000
    assert not repair(db, owner, child.username, apply=True)['changed']
    assert db.query(AdminMoneyTransaction).filter_by(admin_id=child.id).count() == 2
    db.add(AdminMoneyTransaction(operation_key="spending-prevents-repair", operation_type="form_create",
        admin_id=child.id, actor_admin_id=child.id, delta_toman=-1, balance_before=11000, balance_after=10999))
    db.commit()
    with pytest.raises(ValueError, match="grant-only"):
        repair(db, owner, child.username, apply=True)
