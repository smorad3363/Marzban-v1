"""Mandatory finite duration for new service, including Owner and on-hold users."""
from datetime import datetime, timezone
from app.utils.marzhelp_policy import MarzhelpPolicyError


def require_duration(*, expire, status=None, on_hold_duration=None, now=None):
    current = int((now or datetime.now(timezone.utc)).timestamp())
    state = getattr(status, "value", status)
    if state == "on_hold":
        valid = expire in (None, 0) and on_hold_duration is not None and int(on_hold_duration) > 0
    else:
        valid = expire is not None and int(expire) > current
    if valid and ((int(expire or 0) if state != "on_hold" else current + int(on_hold_duration)) > 253402300799):
        raise MarzhelpPolicyError("invalid_expiration_date", "The expiration exceeds supported calendar dates")
    if not valid:
        raise MarzhelpPolicyError("duration_required", "A positive account duration is required")


def validate_new_user(user):
    require_duration(expire=user.expire, status=user.status, on_hold_duration=user.on_hold_expire_duration)
    if user.next_plan is not None and not (user.next_plan.expire and user.next_plan.expire > 0):
        raise MarzhelpPolicyError("duration_required", "The queued service also requires a positive duration")
