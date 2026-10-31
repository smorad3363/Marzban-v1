"""Repair explicitly named, grant-only wallets after a verified database backup.

Run inside the released application container. Dry-run is the default. This
strict repair refuses wallets with spending/refund/reclaim history, a nonzero
opening balance, or retirement. It never inserts another monetary transaction.
"""
import argparse
import json

from app.db import GetDB
from app.db.models import Admin, AdminMoneyTransaction, MarzhelpAdminSettings
from app.utils import admin_hierarchy, financial_controls
from app.utils.audit import AuditLogService


def repair(db, owner, username, *, apply=False):
    account = db.query(Admin).filter_by(username=username).with_for_update().one()
    if not admin_hierarchy.is_owner(db, owner) or account.deleted_at is not None or account.id == owner.id:
        raise ValueError("An active Owner and a non-retired child account are required")
    settings = db.query(MarzhelpAdminSettings).filter_by(admin_id=account.id).with_for_update().one()
    rows = db.query(AdminMoneyTransaction).filter_by(admin_id=account.id).order_by(AdminMoneyTransaction.id).with_for_update().all()
    if not rows or rows[0].balance_before != 0 or any(
        row.operation_type != "grant" or row.delta_toman <= 0
        or row.balance_after != row.balance_before + row.delta_toman for row in rows
    ):
        raise ValueError("Repair requires a zero-opening, internally valid grant-only ledger")
    expected = sum(int(row.delta_toman) for row in rows)
    before = int(settings.money_balance_toman)
    if before < 0 or before > expected:
        raise ValueError("Unexpected wallet state; manual investigation is required")
    result = dict(username=username, before=before, after=expected, changed=before != expected)
    if apply and result['changed']:
        settings.money_balance_toman = expected
        settings.last_positive_charge_toman = rows[-1].delta_toman
        financial_controls.reconcile(db, {account.id})
        AuditLogService.log(db, owner, "money.recover_lost_grants", "admin_money",
                            "Recovered wallet from existing grant-only ledger", target_id=account.id,
                            target_name=account.username, previous_value={"money_balance_toman": before},
                            new_value={"money_balance_toman": expected},
                            details={"ledger_ids": [row.id for row in rows]}, commit=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with GetDB() as db:
        owner = db.get(Admin, admin_hierarchy.owner_id(db))
        results = [repair(db, owner, username, apply=args.apply) for username in dict.fromkeys(args.admin)]
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print(json.dumps({"applied": args.apply, "wallets": results}))


if __name__ == "__main__":
    main()
