import pytest
from app.db.models import Admin, AdminMoneyTransaction, MarzhelpAdminSettings, UserPlanAssignment
from app.models.admin_hierarchy import AccessGroupInput, PlanCreate, PlanVersionInput
from app.utils import access_groups, admin_hierarchy, admin_plans
from test_stage4_plan_network_scope import db, _configure_network


def test_plan_only_user_credit_renewal_uses_plan_price_not_byte_credit(db,monkeypatch):
    session,owner=db
    tag,host,_=_configure_network(session,monkeypatch)
    child=Admin(username='plan-renew-admin',hashed_password='x',parent_admin_id=owner.id,role_id=3)
    session.add(child);session.flush()
    settings=MarzhelpAdminSettings(admin_id=child.id,billing_mode='USER_CREDIT',user_creation_mode_id=2,money_billing_enabled=True,money_balance_toman=1000,last_positive_charge_toman=1000,max_users=1,total_traffic=None,renewal_enabled=True)
    session.add(settings);session.commit()
    admin_hierarchy.reparent_subtree(session,owner,child,owner)
    plan=admin_plans.create_plan(session,owner,PlanCreate(name='paid-unlimited',version=PlanVersionInput(price_toman=200,data_limit=0,duration_days=30)))
    group=access_groups.create(session,owner,AccessGroupInput(name='renew-net',inbounds=[tag],hosts={tag:[host.id]}))
    user,_,_=admin_plans.create_user_from_plan(session,actor=child,plan_id=plan.id,access_group_id=group.id,username='renew-customer',status='active',note=None,idempotency_key='paid-create-renewal')
    original_expire=user.expire
    assert user.lifetime_used_traffic==0
    user.used_traffic=1234
    session.commit()
    assert settings.money_balance_toman==800
    assert settings.user_count_used==1
    assert admin_hierarchy.available_credit(session,settings)==0
    user,_,changed=admin_plans.renew_user_from_plan(session,actor=child,user=user,plan_id=plan.id,idempotency_key='paid-renewal-once')
    assert changed and settings.money_balance_toman==600
    transaction=session.query(AdminMoneyTransaction).filter_by(operation_type="plan_renew",admin_id=child.id).one()
    assert transaction.details["usage_baseline"]==1234
    assert user.data_limit is None and user.expire==original_expire+30*86400
    assert user.used_traffic==0 and settings.user_count_used==1
    _,_,changed=admin_plans.renew_user_from_plan(session,actor=child,user=user,plan_id=plan.id,idempotency_key='paid-renewal-once')
    assert not changed and settings.money_balance_toman==600
    assert session.query(AdminMoneyTransaction).filter_by(operation_type='plan_renew',admin_id=child.id).count()==1
    settings.money_balance_toman=-100;session.commit()
    with pytest.raises(admin_hierarchy.HierarchyError,match='Financial limit'):
        admin_plans.renew_user_from_plan(session,actor=child,user=user,plan_id=plan.id,idempotency_key='frozen-plan-renewal')
    session.rollback()
    assert session.query(UserPlanAssignment).filter_by(idempotency_key='frozen-plan-renewal').count()==0
