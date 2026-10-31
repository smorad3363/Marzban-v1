from app import logger, scheduler, xray
from app.db import GetDB
from app.db.models import Admin, AdminHierarchy, MarzhelpAdminSettings
from app.utils import admin_hierarchy, financial_controls
from config import JOB_ADMIN_ALERTS_INTERVAL


def enforce_admin_account_limits() -> None:
    """Durably reconcile financial holds, expiry and scoped account warnings."""
    changed = False
    with GetDB() as db:
        financial_controls.reconcile(db)
        pending = dict(db.query(MarzhelpAdminSettings.admin_id, MarzhelpAdminSettings.financial_runtime_revision).filter(
            MarzhelpAdminSettings.financial_runtime_revision > MarzhelpAdminSettings.financial_runtime_applied_revision).all())
        changed = bool(pending)
        db.commit()
        owner = db.get(Admin, admin_hierarchy.owner_id(db)) if admin_hierarchy.hierarchy_enabled(db) else None
        candidates = (db.query(Admin, MarzhelpAdminSettings)
            .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
            .filter(Admin.id != owner.id, MarzhelpAdminSettings.account_status_id == admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.ACTIVE])
            .order_by(Admin.id).all()) if owner is not None else []
        covered_admin_ids = set()
        for target, settings in candidates:
            if target.id in covered_admin_ids:
                continue
            reason_id = admin_hierarchy.automatic_suspension_reason(db, settings)
            if reason_id is None:
                continue
            admin_hierarchy.suspend_admin(db, actor=owner, target=target, reason_id=reason_id, include_subtree=True)
            covered_admin_ids.update(row[0] for row in db.query(AdminHierarchy.descendant_id).filter(AdminHierarchy.ancestor_id == target.id).all())
            changed = True
            logger.warning('Admin "%s" was suspended automatically (reason_id=%s)', target.username, reason_id)
    if changed:
        # A failed apply leaves its revision pending, including across restarts.
        xray.operations.restart_all_cores()
        with GetDB() as db:
            for admin_id, revision in pending.items():
                db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id == admin_id,
                    MarzhelpAdminSettings.financial_runtime_applied_revision < revision).update(
                    {MarzhelpAdminSettings.financial_runtime_applied_revision: revision}, synchronize_session=False)
            db.commit()


scheduler.add_job(enforce_admin_account_limits, "interval", minutes=1, coalesce=True, max_instances=1)


def collect_admin_alerts() -> None:
    """Slow comprehensive warning scans independently of debt enforcement."""
    with GetDB() as db:
        from app.utils import admin_alerts
        admin_alerts.collect(db)
        financial_controls.collect_alerts(db)
        db.commit()


scheduler.add_job(collect_admin_alerts, "interval", seconds=JOB_ADMIN_ALERTS_INTERVAL,
                  coalesce=True, max_instances=1)
