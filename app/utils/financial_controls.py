"""Debt state is independent of manual account suspension and traffic credit."""
from datetime import datetime, timezone
from app.db.models import Admin, AdminAccountAlert, AdminFinancialUserHold, AdminHierarchy, MarzhelpAdminSettings, User, UserUsageResetLogs
from app.models.user import UserStatus
from app.utils import admin_hierarchy


def state(settings):
    if not settings.money_billing_enabled or not settings.financial_limits_enabled:
        return 'normal'
    basis = int(settings.last_positive_charge_toman or 0)
    balance = int(settings.money_balance_toman or 0)
    if basis > 0:
        if balance * 100 <= -basis * int(settings.financial_disable_percent or 40): return 'disabled'
        if balance * 100 <= -basis * int(settings.financial_freeze_percent or 10): return 'frozen'
    # An account without any recorded funding cannot accumulate unlimited debt.
    if basis <= 0 and balance < 0: return 'disabled'
    if balance <= 0: return 'empty'
    if basis > 0 and balance * 100 <= basis * 10: return 'low'
    return 'normal'


def can_spend(settings, amount):
    """A recorded top-up permits bounded debt, never an unbounded overdraft."""
    floor = 0
    if settings.money_billing_enabled and settings.financial_limits_enabled:
        floor = -(int(settings.last_positive_charge_toman or 0) * int(settings.financial_freeze_percent or 10) // 100)
    return state(settings) not in {'frozen','disabled'} and int(settings.money_balance_toman or 0) - amount >= floor


def connections_blocked(db, admin_id):
    ids={admin_id} | {r[0] for r in db.query(AdminHierarchy.ancestor_id).filter(AdminHierarchy.descendant_id==admin_id).all()}
    ids.discard(admin_hierarchy.owner_id(db))
    return any(state(s)=='disabled' for s in db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id.in_(ids)).all())


def require_spending(db, admin_id, *, allow_unfunded=False):
    if admin_id is None: return
    admin = db.get(Admin, admin_id)
    if admin is not None and admin_hierarchy.is_owner(db, admin): return
    ids = {admin_id} | {r[0] for r in db.query(AdminHierarchy.ancestor_id).filter(AdminHierarchy.descendant_id == admin_id).all()}
    ids.discard(admin_hierarchy.owner_id(db))
    for settings in db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id.in_(ids)).all():
        if state(settings) in {'frozen','disabled'}:
            raise admin_hierarchy.HierarchyError('financial_account_frozen','Financial limit blocks new purchases and renewals')
        if not allow_unfunded and settings.money_billing_enabled and settings.financial_limits_enabled and int(settings.last_positive_charge_toman or 0)<=0 and int(settings.money_balance_toman or 0)<=0:
            raise admin_hierarchy.HierarchyError('money_funding_required','A positive wallet grant is required before provisioning paid service')


def alert(db, admin_id, key, kind, details=None):
    if not db.query(AdminAccountAlert.id).filter(AdminAccountAlert.event_key == key).first():
        db.add(AdminAccountAlert(admin_id=admin_id,event_key=key,kind=kind,details=details))


def mark_manual_status(db, user):
    from app.db.models import AdminSuspensionUser
    for snapshot in db.query(AdminSuspensionUser).filter_by(user_id=user.id, sync_status="applied").all():
        snapshot.sync_status = "skipped_changed"
    for hold in db.query(AdminFinancialUserHold).filter(AdminFinancialUserHold.user_id == user.id).all():
        hold.restore_allowed = False


def reconcile(db, admin_ids=None):
    """Caller owns transaction; return user IDs whose runtime must be refreshed."""
    # Production disables autoflush. Reloading locked rows must not discard a
    # pending wallet grant, initial funding, refund or charge in this transaction.
    db.flush()
    query = db.query(MarzhelpAdminSettings).order_by(MarzhelpAdminSettings.admin_id)
    if admin_ids is not None: query = query.filter(MarzhelpAdminSettings.admin_id.in_(admin_ids))
    changed = set()
    for settings in query.with_for_update().populate_existing().all():
        # An earlier ancestor in this pass may have created an overlapping hold.
        db.flush()
        account = db.get(Admin, settings.admin_id)
        if account is None or admin_hierarchy.is_owner(db,account): continue
        previously_changed = set(changed)
        new = state(settings)
        transitioned = new != settings.financial_state
        if transitioned:
            # A large usage sample can cross several thresholds at once.
            levels=['normal','low','empty','frozen','disabled']
            old_rank=levels.index(settings.financial_state) if settings.financial_state in levels else 0
            new_rank=levels.index(new)
            kinds=levels[old_rank+1:new_rank+1] if new_rank>old_rank and settings.last_positive_charge_toman else [new]
            for kind in kinds:
                alert(db,account.id,f'financial:{account.id}:{kind}:{datetime.now(timezone.utc).timestamp()}',kind,{'balance_toman':int(settings.money_balance_toman),'basis_toman':int(settings.last_positive_charge_toman)})
            settings.financial_state = new
        ids = {account.id} | {r[0] for r in db.query(AdminHierarchy.descendant_id).filter(AdminHierarchy.ancestor_id==account.id).all()}
        holds = {h.user_id:h for h in db.query(AdminFinancialUserHold).filter(AdminFinancialUserHold.admin_id==account.id).all()}
        if new == 'disabled':
            candidates=db.query(User).filter(User.admin_id.in_(ids))
            if not transitioned:
                candidates=candidates.filter(User.status.in_((UserStatus.active,UserStatus.on_hold)))
            for user in candidates.order_by(User.id).with_for_update().all():
                other=db.query(AdminFinancialUserHold).filter(AdminFinancialUserHold.user_id==user.id).first()
                if user.status not in (UserStatus.active,UserStatus.on_hold) and not (user.status==UserStatus.disabled and other is not None): continue
                if user.id not in holds:
                    # Overlapping ancestor holds retain the original restoration state.
                    db.add(AdminFinancialUserHold(admin_id=account.id,user_id=user.id,previous_status=other.previous_status if other else user.status.value,restore_allowed=other.restore_allowed if other else True))
                if user.status!=UserStatus.disabled:
                    user.status=UserStatus.disabled
                    changed.add(user.id)
        for hold in holds.values():
            user=db.query(User).filter(User.id==hold.user_id).with_for_update().one_or_none()
            if new == 'disabled' and user is not None and user.admin_id in ids:
                continue
            other=db.query(AdminFinancialUserHold).filter(AdminFinancialUserHold.user_id==hold.user_id,AdminFinancialUserHold.admin_id!=account.id).first()
            if user is not None and hold.restore_allowed and other is None and user.status==UserStatus.disabled:
                owner_settings=db.get(MarzhelpAdminSettings,user.admin_id)
                valid_admin=owner_settings is not None and int(owner_settings.account_status_id or 1)==1 and (owner_settings.expiry_date is None or owner_settings.expiry_date>=datetime.now(timezone.utc).date())
                debt_blocked=connections_blocked(db,user.admin_id)
                if valid_admin and not debt_blocked:
                    expired=(user.expire is not None and user.expire<=datetime.now(timezone.utc).timestamp()) or (hold.previous_status=="on_hold" and user.on_hold_timeout is not None and user.on_hold_timeout<=datetime.now(timezone.utc).replace(tzinfo=None))
                    exhausted=user.data_limit is not None and int(user.used_traffic or 0)>=user.data_limit
                    penalty=getattr(user,'device_limit_state',None)
                    blocked=penalty is not None and getattr(penalty,'penalty_status',None) in {'temporarily_disabled','permanently_disabled'}
                    if not blocked:
                        user.status=UserStatus.expired if expired else UserStatus.limited if exhausted else UserStatus(hold.previous_status)
                        changed.add(user.id)
            db.delete(hold)
        if changed != previously_changed:
            settings.financial_runtime_revision = int(settings.financial_runtime_revision or 0) + 1
    db.flush()
    return changed


def collect_alerts(db):
    for settings in db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.account_status_id.in_([2,3])).all():
        kind='account_suspended' if settings.account_status_id==2 else 'account_disabled'
        alert(db,settings.admin_id,f'manual-status:{settings.admin_id}:{kind}:{settings.suspended_at}',kind)
    for user,settings in db.query(User,MarzhelpAdminSettings).join(MarzhelpAdminSettings,MarzhelpAdminSettings.admin_id==User.admin_id).filter(User.data_limit>0).all():
        percent=int(settings.admin_traffic_warning_percent or 80)
        if int(user.used_traffic or 0)*100 < int(user.data_limit)*percent: continue
        reset=db.query(UserUsageResetLogs.id).filter(UserUsageResetLogs.user_id==user.id).order_by(UserUsageResetLogs.id.desc()).first()
        key=f'user-usage:{user.id}:{reset[0] if reset else 0}:{user.data_limit}:{percent}'
        alert(db,user.admin_id,key,'user_usage',{'username':user.username,'percent':percent})
