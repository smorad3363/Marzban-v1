from datetime import datetime, timedelta
import pytest
import sqlalchemy as sa
from app.db.models import AdminAlertIncident, AdminAlertReceipt, AdminAccountAlert, MarzhelpAdminSettings
from app.utils import admin_alerts, financial_controls
from test_financial_controls import tree


def test_financial_incident_current_values_seen_and_resolution(tree):
    db,owner,child,user,s=tree
    s.money_balance_toman=-100
    financial_controls.reconcile(db); db.commit()
    result=admin_alerts.center(db,child)
    incident=next(i for i in result['items'] if i['resource']=='financial')
    assert incident['state']=='frozen' and incident['severity']=='critical'
    assert incident['details']['debt_percent']==10
    assert not incident['seen']
    admin_alerts.seen(db,child,incident['id'],incident['revision']); db.commit()
    again=admin_alerts.center(db,child)
    assert next(i for i in again['items'] if i['id']==incident['id'])['seen']
    assert again['counts']['critical']>=1  # Seeing cannot clear active state.
    s.money_balance_toman=-400
    financial_controls.reconcile(db);db.commit()
    escalated=next(i for i in admin_alerts.center(db,child)['items'] if i['resource']=='financial')
    assert escalated['state']=='disabled' and not escalated['seen']
    assert escalated['revision']==incident['revision']+1
    s.money_balance_toman=1000
    financial_controls.reconcile(db);db.commit()
    assert not any(i['resource']=='financial' for i in admin_alerts.center(db,child)['items'])
    assert any(i['resource']=='financial' for i in admin_alerts.center(db,child,status='resolved')['items'])


def test_unchanged_incident_updates_details_without_repeated_notification(tree):
    db,owner,child,user,s=tree
    s.money_balance_toman=-101
    financial_controls.reconcile(db);db.commit()
    row=db.query(AdminAlertIncident).filter_by(resource='financial',admin_id=child.id).one()
    count=db.query(AdminAccountAlert).filter(AdminAccountAlert.kind.like('incident_%')).count()
    revision=row.revision
    s.money_balance_toman=-102
    financial_controls.reconcile(db);db.commit()
    assert row.details['balance_toman']==-102 and row.revision==revision
    assert db.query(AdminAccountAlert).filter(AdminAccountAlert.kind.like('incident_%')).count()==count


def test_owner_and_subtree_scope_filter_and_receipts_are_private(tree):
    from app.db.models import Admin, AdminHierarchy
    db,owner,child,user,s=tree
    sibling=Admin(username='other-branch',hashed_password='x')
    db.add(sibling);db.flush()
    db.add(AdminHierarchy(ancestor_id=sibling.id,descendant_id=sibling.id,depth=0))
    db.add(MarzhelpAdminSettings(admin_id=sibling.id,money_billing_enabled=True,money_balance_toman=-400,last_positive_charge_toman=1000))
    descendant=Admin(username='alert-descendant',hashed_password='x',parent_admin_id=child.id)
    db.add(descendant);db.flush()
    db.add_all([AdminHierarchy(ancestor_id=child.id,descendant_id=descendant.id,depth=1),AdminHierarchy(ancestor_id=descendant.id,descendant_id=descendant.id,depth=0)])
    db.add(MarzhelpAdminSettings(admin_id=descendant.id,max_users=10,user_count_used=9))
    db.commit()
    admin_alerts.collect(db);db.commit()
    child_result=admin_alerts.center(db,child)
    assert descendant.id in {i['admin_id'] for i in child_result['items']}
    assert sibling.id not in {i['admin_id'] for i in child_result['items']}
    private=next(i for i in admin_alerts.center(db,owner)['items'] if i['admin_id']==sibling.id)
    with pytest.raises(Exception,match='Incident not found'):
        admin_alerts.seen(db,child,private['id'],private['revision'])
    assert not admin_alerts.center(db,child,username='other-branch')['items']
    admin_alerts.seen(db,owner,private['id'],private['revision']);db.commit()
    assert not next(i for i in admin_alerts.center(db,sibling)['items'] if i['id']==private['id'])['seen']


def test_quota_ceilings_zero_disabled_and_recovery(tree):
    db,owner,child,user,s=tree
    s.max_users=10;s.user_count_used=8;s.user_limit=0;s.renewal_remaining=0
    s.trial_quota_limit=5;s.trials_used=5
    s.expiry_date=datetime.utcnow().date()+timedelta(days=3)
    admin_alerts.collect(db);db.commit()
    rows={i['resource']:i for i in admin_alerts.center(db,child)['items']}
    assert rows['accounts']['state']=='near_limit' and rows['accounts']['details']['remaining']==2
    assert rows['create_operations']['severity']=='critical'
    assert rows['renewals']['severity']=='critical' and rows['trials']['severity']=='critical'
    assert rows['expiry']['details']['remaining_days']==3
    s.user_count_used=2;s.user_limit=None;s.renewal_remaining=None;s.trials_used=0
    s.expiry_date=None
    admin_alerts.collect(db);db.commit()
    assert not admin_alerts.center(db,child)['items']


def test_query_count_does_not_scale_with_incident_count(tree):
    db,owner,child,user,s=tree
    s.max_users=10;s.user_count_used=10
    admin_alerts.collect(db);db.commit()
    statements=[]
    def capture(*args):statements.append(args[2])
    sa.event.listen(db.bind,'before_cursor_execute',capture)
    try:
        result=admin_alerts.center(db,owner)
    finally:sa.event.remove(db.bind,'before_cursor_execute',capture)
    assert result['items']
    assert len(statements)<12
    assert not any('FROM users' in q for q in statements)


def test_incident_migration_replay_and_current_data_retention(tree):
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    db,owner,child,user,s=tree
    admin_alerts.collect(db);db.commit()
    count=db.query(AdminAlertIncident).count()
    spec=importlib.util.spec_from_file_location('incident_migration','app/db/migrations/versions/c7f3a1d9e820_admin_alert_center.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with db.bind.begin() as conn:
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade();module.upgrade()
    assert db.query(AdminAlertIncident).count()==count
    assert db.get(MarzhelpAdminSettings,child.id).money_balance_toman==1000


def test_stream_is_scoped_and_revalidates_without_writing(tree,monkeypatch):
    import asyncio
    from contextlib import contextmanager
    from types import SimpleNamespace
    from app import db as db_module
    from app.models.admin import Admin as APIAdmin
    from app.routers.admin_hierarchy import alert_events
    from starlette import concurrency
    db,owner,child,user,s=tree
    @contextmanager
    def session():yield db
    async def inline(fn,*args,**kwargs):return fn(*args,**kwargs)
    async def connected():return False
    monkeypatch.setattr(db_module,'GetDB',session)
    monkeypatch.setattr(concurrency,'run_in_threadpool',inline)
    identity=APIAdmin(id=child.id,username=child.username,is_sudo=False)
    monkeypatch.setattr(APIAdmin,'get_admin',classmethod(lambda cls,token,session:identity))
    request=SimpleNamespace(headers={'Authorization':'Bearer test-token'},is_disconnected=connected)
    response=alert_events(request,db,identity)
    async def run():
        first=await response.body_iterator.__anext__()
        assert 'event: alerts' in first
        monkeypatch.setattr(APIAdmin,'get_admin',classmethod(lambda cls,token,session:None))
        # Close rather than retaining a test session/connection for a stream.
        await response.body_iterator.aclose()
    asyncio.run(run())


def test_batch_collector_and_stale_receipt_revision(tree):
    db,owner,child,user,s=tree
    s.max_users=1;s.user_count_used=1
    admin_alerts.collect(db);db.commit()
    row=db.query(AdminAlertIncident).filter_by(admin_id=child.id,resource='accounts').one()
    old=row.revision
    s.max_users=2
    admin_alerts.collect(db);db.commit()
    with pytest.raises(Exception,match='Refresh the changed incident'):
        admin_alerts.seen(db,child,row.id,old)


def test_legacy_traffic_warnings_batch_and_deduplicate(tree):
    from app.db.models import User
    db,owner,child,user,s=tree
    user.data_limit=100;user.used_traffic=90
    db.add_all([User(username='batch-alert-'+str(i),admin_id=child.id,status='active',data_limit=100,used_traffic=90) for i in range(20)])
    db.commit()
    statements=[]
    def capture(*args):statements.append(args[2])
    sa.event.listen(db.bind,'before_cursor_execute',capture)
    try:
        financial_controls.collect_alerts(db);db.commit()
    finally:sa.event.remove(db.bind,'before_cursor_execute',capture)
    assert db.query(AdminAccountAlert).filter_by(kind='user_usage').count()==21
    selects=[q for q in statements if q.lstrip().upper().startswith('SELECT')]
    assert len(selects)<10
    financial_controls.collect_alerts(db);db.commit()
    assert db.query(AdminAccountAlert).filter_by(kind='user_usage').count()==21


def test_crud_materializes_account_ceiling_in_same_transaction(tree):
    from app.db import crud
    from app.models.user import UserModify
    db,owner,child,user,s=tree
    s.max_users=1;s.user_count_used=1
    db.commit()
    crud.update_user(db,user,UserModify(note='test ceiling notification'),actor=child)
    assert db.query(AdminAlertIncident).filter_by(admin_id=child.id,resource='accounts',resolved_at=None).one().state=='exhausted'
