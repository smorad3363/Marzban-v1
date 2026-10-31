from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import Admin, AdminAccountAlert, AdminFinancialUserHold, AdminMoneyTransaction, MarzhelpAdminSettings, User, UserDeletionRequest, UserUsageResetLogs
from app.models.user import UserStatus
from app.utils import admin_hierarchy, financial_controls as finance, money_billing, user_deletion_finance as refunds, marzhelp_policy
from test_stage3_billing_modes import _seed


@pytest.fixture
def tree(tmp_path):
    engine=create_engine(f'sqlite:///{tmp_path}/finance.db')
    Base.metadata.create_all(engine)
    db=sessionmaker(bind=engine,expire_on_commit=False)()
    owner,child,user=_seed(db)
    settings=db.get(MarzhelpAdminSettings,child.id)
    settings.money_billing_enabled=True
    settings.money_balance_toman=1000
    settings.last_positive_charge_toman=1000
    user.data_limit=10000
    user.used_traffic=0
    db.commit()
    yield db,owner,child,user,settings
    db.close();engine.dispose()


def paid(db,owner,child,user,price=1000):
    row=AdminMoneyTransaction(operation_key='purchase:one',operation_type='plan_create',admin_id=child.id,actor_admin_id=child.id,counterparty_admin_id=owner.id,delta_toman=-price,balance_before=2000,balance_after=1000,user_id=user.id,details={'usage_baseline':0,'quota_bytes':10000})
    db.add(row);db.commit()
    return row


@pytest.mark.parametrize('used,status,automatic',[(0,'on_hold',True),(0,'active',True),(99,'active',True),(100,'active',True),(101,'active',False)])
def test_exact_one_percent_boundary_and_onhold_refund(tree,used,status,automatic):
    db,owner,child,user,settings=tree
    paid(db,owner,child,user)
    user.used_traffic=used;user.status=UserStatus(status);db.commit()
    row=refunds.request_deletion(db,child,user)
    assert (row.status=='APPROVED') is automatic
    assert settings.money_balance_toman==(2000 if automatic else 1000)
    assert refunds.request_deletion(db,child,user).id==row.id
    assert db.query(AdminMoneyTransaction).filter_by(operation_type='purchase_refund').count()==int(automatic)
    if automatic:
        marzhelp_policy.capture_delete(db,user)
        db.delete(user);db.commit()
        assert db.get(UserDeletionRequest,row.id).refund_toman==1000
        assert settings.money_balance_toman==2000


def test_approval_is_direct_parent_capped_atomic_and_replayed(tree):
    db,owner,child,user,settings=tree
    paid(db,owner,child,user)
    user.used_traffic=101;db.commit()
    row=refunds.request_deletion(db,child,user);db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError,match='direct parent'):
        refunds.decide(db,child,row.id,True,100,None)
    with pytest.raises(admin_hierarchy.HierarchyError,match='exceeds'):
        refunds.decide(db,owner,row.id,True,1001,None)
    result,deleted=refunds.decide(db,owner,row.id,True,600,'partial approval');db.commit()
    assert db.get(User,user.id) is None
    assert settings.money_balance_toman==1600
    assert result.refund_toman==600
    replay,deleted=refunds.decide(db,owner,row.id,True,600,'partial approval')
    assert deleted is None
    with pytest.raises(admin_hierarchy.HierarchyError):
        refunds.decide(db,owner,row.id,True,700,'partial approval')
    assert db.query(AdminMoneyTransaction).filter_by(operation_type='purchase_refund').count()==1


def test_rejection_does_not_delete_or_move_money_and_scopes_history(tree):
    db,owner,child,user,settings=tree
    paid(db,owner,child,user)
    user.used_traffic=200;db.commit()
    row=refunds.request_deletion(db,child,user);db.commit()
    refunds.decide(db,owner,row.id,False,0,'rejected');db.commit()
    assert db.get(User,user.id) is not None
    assert settings.money_balance_toman==1000
    unrelated=Admin(username='unrelated',hashed_password='x');db.add(unrelated);db.commit()
    assert refunds.visible_requests(db,unrelated).count()==0
    assert refunds.visible_requests(db,child).count()==1


def test_used_traffic_charges_are_never_refunded_and_reset_cannot_hide_usage(tree):
    db,owner,child,user,settings=tree
    settings.billing_mode='USED_TRAFFIC'
    db.add(AdminMoneyTransaction(operation_key='usage:one',operation_type='usage_settlement',admin_id=child.id,actor_admin_id=child.id,delta_toman=-600,balance_before=1600,balance_after=1000,user_id=user.id))
    db.commit()
    row=refunds.request_deletion(db,child,user)
    assert row.status=='APPROVED' and row.refund_toman==0
    assert settings.money_balance_toman==1000
    # A real purchase is refundable in any mode, but historical usage is counted.
    db.rollback();db.query(UserDeletionRequest).delete();db.commit()
    paid(db,owner,child,user)
    db.add(UserUsageResetLogs(user_id=user.id,used_traffic_at_reset=101));db.commit();db.refresh(user)
    assert refunds.request_deletion(db,child,user).status=='PENDING'


def test_bulk_delete_cannot_bypass_review(tree):
    db,owner,child,user,settings=tree
    paid(db,owner,child,user)
    user.used_traffic=200;db.commit()
    with pytest.raises(admin_hierarchy.HierarchyError,match='approval'):
        marzhelp_policy.capture_delete(db,user)
    assert settings.money_balance_toman==1000


@pytest.mark.parametrize('balance,expected',[(101,'normal'),(100,'low'),(0,'empty'),(-99,'empty'),(-100,'frozen'),(-399,'frozen'),(-400,'disabled')])
def test_debt_thresholds_are_inclusive_and_do_not_manually_suspend(tree,balance,expected):
    db,owner,child,user,settings=tree
    settings.money_balance_toman=balance
    finance.reconcile(db);db.commit()
    assert settings.financial_state==expected
    assert settings.account_status_id==1
    assert user.status==(UserStatus.disabled if expected=='disabled' else UserStatus.active)
    if expected in ('frozen','disabled'):
        with pytest.raises(admin_hierarchy.HierarchyError,match='Financial limit'):
            finance.require_spending(db,child.id)
    count=db.query(AdminAccountAlert).count();finance.reconcile(db);db.commit()
    assert db.query(AdminAccountAlert).count()==count


def test_recovery_preserves_manual_blocks_expiry_and_exhaustion(tree):
    db,owner,child,user,settings=tree
    manual=User(username='manual',admin_id=child.id,status=UserStatus.disabled)
    expired=User(username='expires',admin_id=child.id,status=UserStatus.active,expire=int((datetime.now(timezone.utc)+timedelta(days=1)).timestamp()))
    limited=User(username='limited',admin_id=child.id,status=UserStatus.active,data_limit=10,used_traffic=0)
    touched=User(username='touched',admin_id=child.id,status=UserStatus.active)
    db.add_all([manual,expired,limited,touched]);db.commit()
    settings.money_balance_toman=-400;finance.reconcile(db);db.commit()
    expired.expire=int((datetime.now(timezone.utc)-timedelta(seconds=1)).timestamp())
    limited.used_traffic=10
    finance.mark_manual_status(db,touched)
    db.commit()
    assert user.status==UserStatus.disabled
    result,created=money_billing.transfer_money(db,actor=owner,parent=owner,child=child,amount_toman=1000,operation_type='grant',idempotency_key='finance-recovery')
    db.commit()
    assert created and result['runtime_user_ids']
    assert user.status==UserStatus.active
    assert manual.status==UserStatus.disabled and touched.status==UserStatus.disabled
    assert expired.status==UserStatus.expired and limited.status==UserStatus.limited, (expired.expire, datetime.now(timezone.utc).timestamp(), expired.status, limited.status)
    assert db.query(AdminFinancialUserHold).count()==0
    assert settings.last_positive_charge_toman==1000
    _,created=money_billing.transfer_money(db,actor=owner,parent=owner,child=child,amount_toman=1000,operation_type='grant',idempotency_key='finance-recovery')
    assert not created and settings.money_balance_toman==600


def test_custom_percent_and_positive_grant_only_basis(tree):
    db,owner,child,user,settings=tree
    settings.financial_freeze_percent=20;settings.financial_disable_percent=60
    settings.money_balance_toman=-100
    assert finance.state(settings)=='empty'
    settings.money_balance_toman=-200
    assert finance.state(settings)=='frozen'
    settings.money_balance_toman=-600
    assert finance.state(settings)=='disabled'
    money_billing.transfer_money(db,actor=owner,parent=owner,child=child,amount_toman=100,operation_type='grant',idempotency_key='partial-topup')
    db.commit()
    assert settings.last_positive_charge_toman==100
    assert settings.money_balance_toman==-500


def test_overlapping_parent_and_child_debt_restore_only_after_both_clear(tree):
    db,owner,parent,user,parent_settings=tree
    child=Admin(username='financial-subchild',hashed_password='x')
    db.add(child);db.flush()
    policy=MarzhelpAdminSettings(admin_id=child.id,billing_mode='USED_TRAFFIC',money_billing_enabled=True,money_balance_toman=-400,last_positive_charge_toman=1000)
    db.add(policy);db.commit()
    parent_settings.can_create_admins=True;db.commit()
    admin_hierarchy.reparent_subtree(db,owner,child,parent)
    user.admin_id=child.id;parent_settings.money_balance_toman=-400;db.commit()
    finance.reconcile(db);db.commit()
    assert user.status==UserStatus.disabled and db.query(AdminFinancialUserHold).count()==2
    parent_settings.money_balance_toman=100;finance.reconcile(db);db.commit()
    assert user.status==UserStatus.disabled
    policy.money_balance_toman=100;finance.reconcile(db);db.commit()
    assert user.status==UserStatus.active and db.query(AdminFinancialUserHold).count()==0


def test_changed_financial_runtime_revision_survives_until_apply(tree):
    db,owner,child,user,settings=tree
    settings.money_balance_toman=-400
    finance.reconcile(db);db.commit()
    assert settings.financial_runtime_revision==1
    assert settings.financial_runtime_applied_revision==0
    finance.reconcile(db);db.commit()
    assert settings.financial_runtime_revision==1
    settings.money_balance_toman=100;finance.reconcile(db);db.commit()
    assert settings.financial_runtime_revision==2
    assert settings.financial_runtime_applied_revision==0


def test_refund_reverses_parent_margin_and_original_payer_after_transfer(tree):
    db,owner,child,user,settings=tree
    purchase=paid(db,owner,child,user)
    parent=Admin(username='refund-margin-parent',hashed_password='x')
    db.add(parent);db.flush()
    parent_policy=MarzhelpAdminSettings(admin_id=parent.id,billing_mode='ALLOCATED_TRAFFIC',money_balance_toman=100)
    db.add(parent_policy)
    db.add(AdminMoneyTransaction(operation_key=purchase.operation_key,operation_type='plan_create',admin_id=parent.id,actor_admin_id=child.id,delta_toman=300,balance_before=-200,balance_after=100,user_id=user.id))
    user.admin_id=owner.id
    db.commit()
    result=refunds.request_deletion(db,owner,user)
    assert result.account_admin_id==child.id and result.refund_toman==1000
    assert settings.money_balance_toman==2000
    assert parent_policy.money_balance_toman==-200


def test_decision_and_wallet_rollback_together(tree):
    db,owner,child,user,settings=tree
    paid(db,owner,child,user)
    user.used_traffic=200;db.commit()
    row=refunds.request_deletion(db,child,user);db.commit()
    refunds.decide(db,owner,row.id,True,1000,None)
    db.rollback()
    db.refresh(settings);db.refresh(row)
    assert settings.money_balance_toman==1000 and row.status=='PENDING'
    assert db.get(User,user.id) is not None
    assert db.query(AdminMoneyTransaction).filter_by(operation_type='purchase_refund').count()==0
