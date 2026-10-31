from app.db.models import MarzhelpAdminSettings
from app.models.user import UserStatus
from app.utils import financial_controls as finance, money_billing
from test_financial_controls import tree


def test_owner_wallet_flag_does_not_block_funded_child(tree):
    db,owner,child,user,settings=tree
    owner_policy=db.get(MarzhelpAdminSettings,owner.id)
    owner_policy.money_billing_enabled=True
    owner_policy.money_balance_toman=0
    owner_policy.last_positive_charge_toman=0
    db.commit()
    finance.require_spending(db,child.id)
    assert not finance.connections_blocked(db,child.id)
    assert not finance.connections_blocked(db,owner.id)


def test_owner_wallet_is_exempt_during_child_debt_recovery(tree):
    db,owner,child,user,settings=tree
    owner_policy=db.get(MarzhelpAdminSettings,owner.id)
    owner_policy.money_billing_enabled=True
    owner_policy.money_balance_toman=-1000
    owner_policy.last_positive_charge_toman=1000
    db.commit()
    assert not finance.connections_blocked(db,child.id)
    settings.money_balance_toman=-400
    finance.reconcile(db);db.commit()
    assert user.status==UserStatus.disabled
    money_billing.transfer_money(db,actor=owner,parent=owner,child=child,amount_toman=500,operation_type='grant',idempotency_key='owner-independent-recovery')
    db.commit()
    assert user.status==UserStatus.active
    assert settings.money_balance_toman==100
    assert owner_policy.money_balance_toman==-1000
