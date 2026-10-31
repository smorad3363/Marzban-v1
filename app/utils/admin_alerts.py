"""Current incidents are materialized by writers, never by a viewer's poll."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, or_
from app.db.models import Admin, AdminAccountAlert, AdminAlertIncident, AdminAlertReceipt, AdminAlertScanState, AdminHierarchy, MarzhelpAdminSettings
from app.utils import admin_hierarchy


def conditions(s, *, today=None):
    """Evaluate stored counters only; no per-user scan and no financial mutation."""
    from app.utils.financial_controls import state
    today = today or datetime.now(timezone.utc).date()
    result = {}
    financial = state(s)
    if financial != 'normal':
        basis = int(s.last_positive_charge_toman or 0)
        balance = int(s.money_balance_toman or 0)
        freeze = basis * int(s.financial_freeze_percent or 10) // 100
        cutoff = basis * int(s.financial_disable_percent or 40) // 100
        result['financial'] = (financial, 'critical' if financial in ('frozen','disabled') else 'warning', {
            'balance_toman': balance, 'basis_toman': basis,
            'debt_percent': round(max(-balance, 0) * 100 / basis, 2) if basis else None,
            'freeze_percent': int(s.financial_freeze_percent or 10),
            'cutoff_percent': int(s.financial_disable_percent or 40),
            'remaining_to_freeze_toman': max(balance + freeze, 0),
            'remaining_to_cutoff_toman': max(balance + cutoff, 0),
        })
    if int(s.account_status_id or 1) != 1:
        result['account'] = ('suspended' if s.account_status_id == 2 else 'disabled', 'critical', {})
    if s.expiry_date is not None:
        days = (s.expiry_date - today).days
        if days <= 7:
            result['expiry'] = ('expired' if days < 0 else 'near_limit', 'critical' if days < 0 else 'warning',
                                {'remaining_days': days, 'expiry_date': str(s.expiry_date)})
    def quota(key, used, limit, unit='count'):
        if limit is None: return
        used, limit = int(used or 0), int(limit)
        percent = 100 if limit <= 0 else min(used * 100 / limit, 100)
        if percent >= 80:
            result[key] = ('exhausted' if used >= limit else 'near_limit', 'critical' if used >= limit else 'warning',
                           {'used': used, 'limit': limit, 'remaining': max(limit-used,0), 'percent': round(percent,2), 'unit': unit})
    quota('accounts', s.user_count_used, s.max_users)
    quota('create_operations', 0, s.user_limit)
    quota('renewals', 0, s.renewal_remaining)
    quota('renewal_budget', s.renewals_used, s.renewal_limit)
    quota('provisioning_volume', s.provisioning_volume_used, s.provisioning_volume_limit, 'bytes')
    if s.billing_mode == 'SEAT_CREDIT':
        quota('devices', int(s.capacity_used or 0) + int(s.delegated_traffic or 0), s.device_capacity_limit)
    if s.billing_mode == 'ALLOCATED_TRAFFIC':
        quota('traffic', int(s.used_traffic or 0) + int(s.delegated_traffic or 0), s.total_traffic, 'bytes')
    if int(s.trial_quota_limit or 0) > 0:
        quota('trials', int(s.trials_used or 0), s.trial_quota_limit)
    return result


def sync_settings(db, settings):
    """Caller holds policy locks; incident and history commit with that policy."""
    if not settings: return
    if len(settings) > 250:
        for offset in range(0,len(settings),250): sync_settings(db,settings[offset:offset+250])
        return
    db.flush()
    ids = [s.admin_id for s in settings]
    owner = admin_hierarchy.owner_id(db)
    rows = {(r.admin_id, r.resource): r for r in db.query(AdminAlertIncident).filter(
        AdminAlertIncident.admin_id.in_(ids)).with_for_update().populate_existing().all()}
    by_admin = {}
    for admin_id, resource in rows: by_admin.setdefault(admin_id,set()).add(resource)
    now = datetime.utcnow()
    for s in settings:
        desired = {} if s.admin_id == owner else conditions(s)
        resources = set(desired) | by_admin.get(s.admin_id,set())
        for resource in resources:
            row = rows.get((s.admin_id,resource))
            value = desired.get(resource)
            transition = None
            if value is None:
                if row is None or row.resolved_at is not None: continue
                row.resolved_at = now
                row.revision += 1
                transition = 'incident_resolved'
            else:
                state, severity, details = value
                if row is None:
                    row = AdminAlertIncident(admin_id=s.admin_id, resource=resource, state=state,
                        severity=severity, details=details, revision=1, opened_at=now, updated_at=now)
                    db.add(row); rows[(s.admin_id,resource)] = row
                    transition = 'incident_open'
                elif row.resolved_at is not None or (row.state,row.severity) != (state,severity):
                    transition = 'incident_change'
                    if row.resolved_at is not None: row.opened_at = now
                    row.revision += 1
                row.state, row.severity, row.details = state, severity, details
                row.resolved_at = None
            row.updated_at = now
            if transition:
                db.add(AdminAccountAlert(admin_id=s.admin_id, event_key='incident:'+uuid4().hex,
                    kind=transition, details={'resource':resource,'state':row.state,'severity':row.severity,
                                            'revision':row.revision,'values':row.details}))
    db.flush()


def collect(db):
    """Lock policies in stable order, matching financial writer order."""
    db.flush()
    last = 0
    while True:
        settings = db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id > last).order_by(
            MarzhelpAdminSettings.admin_id).limit(250).with_for_update().populate_existing().all()
        if not settings: break
        sync_settings(db, settings)
        last = settings[-1].admin_id
    marker = db.get(AdminAlertScanState,1)
    if marker is None:
        marker = AdminAlertScanState(id=1, checked_at=datetime.utcnow())
        db.add(marker)
    marker.checked_at = datetime.utcnow()
    db.flush()


def center(db, actor, *, status='active', severity=None, username=None, before=None, limit=50):
    base = admin_hierarchy.scope_admin_column(db.query(AdminAlertIncident), db, actor, AdminAlertIncident.admin_id)
    active = base.filter(AdminAlertIncident.resolved_at.is_(None))
    counts = dict(active.with_entities(AdminAlertIncident.severity, func.count(AdminAlertIncident.id))
                  .group_by(AdminAlertIncident.severity).all())
    query = base.join(Admin, Admin.id == AdminAlertIncident.admin_id)
    if status != 'all':
        query = query.filter(AdminAlertIncident.resolved_at.is_(None) if status == 'active' else AdminAlertIncident.resolved_at.isnot(None))
    if severity: query = query.filter(AdminAlertIncident.severity == severity)
    if username: query = query.filter(Admin.username.contains(username, autoescape=True))
    if before is not None: query = query.filter(AdminAlertIncident.id < before)
    records = query.with_entities(AdminAlertIncident, Admin.username).order_by(AdminAlertIncident.id.desc()).limit(limit+1).all()
    more = len(records) > limit
    records = records[:limit]
    receipts = dict(db.query(AdminAlertReceipt.incident_id, AdminAlertReceipt.revision).filter(
        AdminAlertReceipt.viewer_admin_id == actor.id,
        AdminAlertReceipt.incident_id.in_([r.id for r,_ in records])).all()) if records else {}
    items = [dict(id=r.id, admin_id=r.admin_id, admin_username=name, resource=r.resource, state=r.state,
        severity=r.severity, details=r.details, revision=r.revision, opened_at=r.opened_at,
        updated_at=r.updated_at, resolved_at=r.resolved_at, seen=receipts.get(r.id)==r.revision) for r,name in records]
    inherited = False
    if not admin_hierarchy.is_owner(db, actor):
        inherited = db.query(MarzhelpAdminSettings.admin_id).join(AdminHierarchy,
            AdminHierarchy.ancestor_id == MarzhelpAdminSettings.admin_id).filter(
                AdminHierarchy.descendant_id == actor.id,
                AdminHierarchy.ancestor_id != actor.id,
                AdminHierarchy.ancestor_id != admin_hierarchy.owner_id(db),
                or_(MarzhelpAdminSettings.account_status_id.in_([2,3]),
                    MarzhelpAdminSettings.financial_state.in_(['frozen','disabled']),
                    MarzhelpAdminSettings.expiry_date < datetime.now(timezone.utc).date())).first() is not None
    marker = db.get(AdminAlertScanState,1)
    return dict(items=items, inherited_restriction=inherited, counts={'critical':counts.get('critical',0),'warning':counts.get('warning',0)},
                next_before=records[-1][0].id if more else None, checked_at=marker.checked_at if marker else None)


def seen(db, actor, incident_id, revision):
    row = admin_hierarchy.scope_admin_column(db.query(AdminAlertIncident), db, actor, AdminAlertIncident.admin_id).filter(
        AdminAlertIncident.id==incident_id).with_for_update().populate_existing().one_or_none()
    if row is None: raise admin_hierarchy.HierarchyError('incident_not_found','Incident not found')
    if revision != row.revision: raise admin_hierarchy.HierarchyError('incident_changed','Refresh the changed incident')
    receipt = db.get(AdminAlertReceipt,(actor.id,row.id))
    if receipt is None:
        receipt = AdminAlertReceipt(viewer_admin_id=actor.id,incident_id=row.id,revision=revision)
        db.add(receipt)
    receipt.revision, receipt.seen_at = revision, datetime.utcnow()
    db.flush()
