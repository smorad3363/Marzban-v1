"""Deletion refunds reverse a recorded purchase, never metered usage charges."""
from datetime import datetime
from sqlalchemy import and_, or_
from app.db.models import Admin, AdminMoneyTransaction, MarzhelpAdminSettings, User, UserDeletionRequest
from app.utils import admin_hierarchy, financial_controls
from app.utils.money_billing import usage_total

PURCHASE_TYPES = ('plan_create','plan_renew','form_create')


def visible_requests(db,actor):
    query=db.query(UserDeletionRequest)
    if admin_hierarchy.is_owner(db,actor): return query
    direct_accounts=db.query(Admin.id).filter(Admin.parent_admin_id==actor.id)
    return query.filter(or_(UserDeletionRequest.requester_admin_id==actor.id,and_(UserDeletionRequest.status!="PENDING",UserDeletionRequest.reviewer_admin_id==actor.id),UserDeletionRequest.account_admin_id==actor.id,UserDeletionRequest.account_admin_id.in_(direct_accounts)))


def current_reviewer(db,row,lock=False):
    account=(db.query(Admin).filter(Admin.id==row.account_admin_id).with_for_update().populate_existing().one_or_none() if lock else db.get(Admin,row.account_admin_id))
    return (account.parent_admin_id if account is not None else None) or admin_hierarchy.owner_id(db)


def request_response(db,row):
    from app.models.admin_hierarchy import DeletionRequestResponse
    response=DeletionRequestResponse.model_validate(row)
    if row.status=='PENDING': response.reviewer_admin_id=current_reviewer(db,row)
    return response


def purchase(db,user):
    # Only the latest paid entitlement can be refunded. A renewal cannot refund
    # already consumed previous cycles, and a manual counter reset cannot hide usage.
    row=db.query(AdminMoneyTransaction).filter(AdminMoneyTransaction.user_id==user.id,AdminMoneyTransaction.operation_type.in_(PURCHASE_TYPES),AdminMoneyTransaction.delta_toman<0).order_by(AdminMoneyTransaction.id.desc()).first()
    if row is None: return 0,[],usage_total(db,user),int(user.data_limit or 0)
    rows=db.query(AdminMoneyTransaction).filter(AdminMoneyTransaction.operation_key==row.operation_key).order_by(AdminMoneyTransaction.admin_id).all()
    details=row.details or {}
    used=max(0,usage_total(db,user)-int(details.get('usage_baseline',0)))
    quota=int(details.get('quota_bytes',user.data_limit or 0))
    return -int(row.delta_toman),[{'admin_id':r.admin_id,'delta':int(r.delta_toman),'source_id':r.id} for r in rows],used,quota


def low_usage(used,quota):
    return used==0 or (quota>0 and used*100<=quota)


def request_deletion(db,actor,user):
    user=db.query(User).filter(User.id==user.id).with_for_update().populate_existing().one()
    if not admin_hierarchy.can_access_user(db,actor,user):
        raise admin_hierarchy.HierarchyError('user_scope_forbidden','User is outside actor scope')
    settings=db.get(MarzhelpAdminSettings,user.admin_id)
    if settings is not None and settings.prevent_user_deletion:
        raise admin_hierarchy.HierarchyError('deletion_forbidden','User deletion is disabled')
    existing=db.query(UserDeletionRequest).filter(UserDeletionRequest.user_id==user.id).order_by(UserDeletionRequest.id.desc()).with_for_update().first()
    if existing is not None and existing.status != "REJECTED": return existing
    amount,rows,used,quota=purchase(db,user)
    payer_id=next((entry["admin_id"] for entry in rows if entry["delta"]<0),user.admin_id)
    if not admin_hierarchy.admin_in_scope(db,actor,payer_id):
        raise admin_hierarchy.HierarchyError("refund_payer_scope_forbidden", "Original purchaser is outside actor scope; contact Owner")
    account=db.get(Admin,payer_id)
    if account is None: raise admin_hierarchy.HierarchyError('user_owner_missing','User owner is missing')
    reviewer=account.parent_admin_id or admin_hierarchy.owner_id(db)
    automatic=amount==0 or low_usage(used,quota)
    row=UserDeletionRequest(user_id=user.id,username=user.username,account_admin_id=account.id,requester_admin_id=actor.id,reviewer_admin_id=reviewer,status='PENDING',purchase_toman=amount,used_bytes=used,quota_bytes=quota,purchase_snapshot=rows)
    db.add(row);db.flush()
    if automatic:
        apply_refund(db,row,actor,amount)
    return row


def apply_refund(db,row,actor,amount):
    if row.status!='PENDING':
        raise admin_hierarchy.HierarchyError('refund_already_finalized','Deletion decision is already finalized')
    if amount<0 or amount>row.purchase_toman:
        raise admin_hierarchy.HierarchyError('invalid_refund_amount','Refund exceeds recorded purchase')
    ids={entry['admin_id'] for entry in row.purchase_snapshot}
    settings={s.admin_id:s for s in db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id.in_(ids)).order_by(MarzhelpAdminSettings.admin_id).with_for_update().populate_existing().all()}
    for entry in row.purchase_snapshot:
        delta=(-entry['delta']*amount//row.purchase_toman) if entry['delta']<=0 else -(entry['delta']*amount//row.purchase_toman)
        if not delta: continue
        policy=settings[entry['admin_id']]
        before=int(policy.money_balance_toman or 0)
        policy.money_balance_toman=before+delta
        db.add(AdminMoneyTransaction(operation_key=f'deletion-refund:{row.id}',operation_type='purchase_refund',admin_id=policy.admin_id,actor_admin_id=actor.id,counterparty_admin_id=row.account_admin_id if policy.admin_id!=row.account_admin_id else row.reviewer_admin_id,delta_toman=delta,balance_before=before,balance_after=before+delta,details={'deletion_request_id':row.id,'source_transaction_id':entry['source_id'],'username':row.username}))
    row.status='APPROVED';row.refund_toman=amount;row.decided_by_admin_id=actor.id;row.decided_at=datetime.utcnow()
    db.flush()
    financial_controls.reconcile(db, ids)


def decide(db,actor,request_id,approve,amount,note):
    # Lock user before request consistently with the deletion/renewal paths.
    candidate=db.get(UserDeletionRequest,request_id)
    if candidate is None: raise admin_hierarchy.HierarchyError('refund_request_not_found','Deletion request not found')
    user=db.query(User).filter(User.id==candidate.user_id).with_for_update().populate_existing().one_or_none()
    row=db.query(UserDeletionRequest).filter(UserDeletionRequest.id==request_id).with_for_update().populate_existing().one()
    reviewer_id=current_reviewer(db,row,lock=True) if row.status=='PENDING' else row.reviewer_admin_id
    if actor.id!=reviewer_id:
        raise admin_hierarchy.HierarchyError('refund_decision_forbidden','Only the direct parent assigned to this request can decide')
    if row.status!='PENDING':
        # Exact repeat is harmless; differing decisions are rejected.
        if row.decided_by_admin_id==actor.id and row.status==('APPROVED' if approve else 'REJECTED') and (not approve or row.refund_toman==amount) and row.decision_note==note: return row,None
        raise admin_hierarchy.HierarchyError('refund_already_finalized','Deletion request is already finalized')
    row.reviewer_admin_id=reviewer_id
    if approve:
        if user is None: raise admin_hierarchy.HierarchyError('user_not_found','User no longer exists')
        if not admin_hierarchy.can_access_user(db,actor,user):
            raise admin_hierarchy.HierarchyError('user_scope_forbidden','User moved outside reviewer scope')
        current_amount,current_rows,_,_=purchase(db,user)
        if current_amount!=row.purchase_toman or current_rows!=row.purchase_snapshot:
            raise admin_hierarchy.HierarchyError('refund_purchase_changed','Purchase changed; reject this request before deleting again')
        apply_refund(db,row,actor,amount)
        from app.db import crud
        # capture_delete sees the finalized, locked request and cannot refund twice.
        from app.utils import marzhelp_policy
        marzhelp_policy.capture_delete(db,user)
        db.delete(user)
    else:
        row.status='REJECTED';row.refund_toman=0;row.decided_by_admin_id=actor.id;row.decided_at=datetime.utcnow()
    row.decision_note=note
    db.flush()
    return row,user if approve else None


def capture_financial_delete(db,user):
    """Central guard also covers bulk, cleanup and retirement deletion paths."""
    policy=db.query(MarzhelpAdminSettings).filter(MarzhelpAdminSettings.admin_id==user.admin_id).with_for_update().one_or_none()
    if policy is not None:
        policy.financial_runtime_revision=int(policy.financial_runtime_revision or 0)+1
    amount,_,used,quota=purchase(db,user)
    if amount==0: return
    row=db.query(UserDeletionRequest).filter(UserDeletionRequest.user_id==user.id).order_by(UserDeletionRequest.id.desc()).with_for_update().first()
    if row is not None and row.status=='APPROVED': return
    if not low_usage(used,quota):
        raise admin_hierarchy.HierarchyError('refund_review_required','Request deletion approval from the direct parent first')
    if row is not None and row.status=='PENDING':
        raise admin_hierarchy.HierarchyError('refund_review_required','Resolve the existing deletion request first')
    actor=db.get(Admin,admin_hierarchy.owner_id(db)) or db.get(Admin,user.admin_id)
    request_deletion(db,actor,user)
