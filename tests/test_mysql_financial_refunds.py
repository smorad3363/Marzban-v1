"""Concurrent approval against the disposable CI MySQL database only."""
import os
from concurrent.futures import ThreadPoolExecutor
import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from OpenSSL import crypto
from app.db.models import Admin, AdminMoneyTransaction, MarzhelpAdminSettings, User, UserDeletionRequest
from app.utils import admin_hierarchy, money_billing, user_deletion_finance as refunds

URL=os.getenv('TEST_MYSQL_DATABASE_URL')


@pytest.mark.skipif(not URL,reason='Disposable MySQL CI database is not configured')
def test_concurrent_deletion_approvals_refund_once(monkeypatch):
    url=make_url(URL)
    assert url.get_backend_name()=='mysql' and url.database.endswith('marzban_test')
    engine=sa.create_engine(URL,pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(sa.text('SET FOREIGN_KEY_CHECKS=0'))
        for table in sa.inspect(conn).get_table_names():
            conn.execute(sa.text('DROP TABLE `'+table.replace('`','``')+'`'))
        conn.execute(sa.text('SET FOREIGN_KEY_CHECKS=1'))
    alembic=Config('alembic.ini')
    alembic.set_main_option('sqlalchemy.url',URL)
    original_not_after=crypto.X509.gmtime_adj_notAfter
    monkeypatch.setattr(crypto.X509,'gmtime_adj_notAfter',lambda certificate,seconds:original_not_after(certificate,min(seconds,2_000_000_000)))
    command.upgrade(alembic,'head')
    factory=sessionmaker(bind=engine,expire_on_commit=False,autoflush=False)
    with factory() as db:
        owner=Admin(username='financial-mysql-owner',hashed_password='x',is_sudo=True)
        child=Admin(username='financial-mysql-child',hashed_password='x',is_sudo=False)
        db.add_all([owner,child]);db.flush()
        db.add_all([MarzhelpAdminSettings(admin_id=owner.id,billing_mode='LEGACY_COMPAT'),MarzhelpAdminSettings(admin_id=child.id,billing_mode='ALLOCATED_TRAFFIC',total_traffic=100000,used_traffic=10000)])
        db.commit()
        admin_hierarchy.set_owner(db,owner.username)
        user=User(username='financial-mysql-user',admin_id=child.id,status='active',data_limit=10000,used_traffic=200)
        db.add(user);db.commit()
        settings=db.get(MarzhelpAdminSettings,child.id)
        settings.money_balance_toman=1000
        user.data_limit=10000;user.used_traffic=200
        db.add(AdminMoneyTransaction(operation_key='parallel-purchase',operation_type='plan_create',admin_id=child.id,actor_admin_id=child.id,counterparty_admin_id=owner.id,delta_toman=-1000,balance_before=2000,balance_after=1000,user_id=user.id,details={'usage_baseline':0,'quota_bytes':10000}))
        db.commit()
        row=refunds.request_deletion(db,child,user);db.commit()
        request_id,owner_id,child_id,user_id=row.id,owner.id,child.id,user.id
    def approve(_):
        with factory() as db:
            row,deleted=refunds.decide(db,db.get(Admin,owner_id),request_id,True,600,'concurrent approval')
            db.commit()
            return deleted is not None
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes=list(executor.map(approve,range(2)))
    with factory() as db:
        assert sum(outcomes)==1
        assert db.get(User,user_id) is None
        assert db.get(MarzhelpAdminSettings,child_id).money_balance_toman==1600
        assert db.get(UserDeletionRequest,request_id).refund_toman==600
        assert db.query(AdminMoneyTransaction).filter_by(operation_type='purchase_refund').count()==1
    def grant(_):
        with factory() as db:
            result,created=money_billing.transfer_money(db,actor=db.get(Admin,owner_id),parent=db.get(Admin,owner_id),child=db.get(Admin,child_id),amount_toman=100,operation_type='grant',idempotency_key='parallel-grant-once')
            db.commit()
            return created
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes=list(executor.map(grant,range(2)))
    with factory() as db:
        assert sum(outcomes)==1
        assert db.get(MarzhelpAdminSettings,child_id).money_balance_toman==1700
        assert db.get(MarzhelpAdminSettings,child_id).last_positive_charge_toman==100
        assert db.query(AdminMoneyTransaction).filter_by(operation_key='money:grant:parallel-grant-once').count()==1
    with factory() as db:
        settings = db.get(MarzhelpAdminSettings, child_id)
        settings.billing_mode = 'USED_TRAFFIC'
        settings.money_billing_enabled = True
        settings.used_traffic_price_per_gib_toman = 1000
        db.commit()
        for value in [1, 3, 1024**3 - 4]:
            money_billing.settle_used_traffic(db, {child_id: value}, weighted_usage={child_id: value * 13000})
            db.commit()
        db.refresh(settings)
        assert settings.money_balance_toman == 400
        assert settings.usage_billing_remainder == settings.usage_billing_fraction == 0
    engine.dispose()
