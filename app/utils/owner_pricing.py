"""Owner policy and deterministic capped daily Form pricing."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import Admin, MarzhelpAdminSettings, OwnerCommercialPolicy, OwnerDurationPreset
from app.models.admin_hierarchy import DurationPresetInput, OwnerPricingResponse, OwnerPricingUpdate
from app.utils import admin_hierarchy
from app.utils.admin_billing import BillingMode, billing_mode


GIB = 1024**3
BASE_DAYS = 30
CAP_DAYS = 365
MAX_MULTIPLIER_BPS = 12000


@dataclass(frozen=True)
class DurationQuote:
    duration_days: int
    multiplier_basis_points: int


def duration_multiplier_basis_points(days: int) -> int:
    """Concave daily pricing: 1x through day 30, a smooth 1.2x cap at day 365."""
    if days <= 0:
        raise admin_hierarchy.HierarchyError("duration_required", "A positive account duration is required")
    if days <= BASE_DAYS:
        return 10000
    if days >= CAP_DAYS:
        return MAX_MULTIPLIER_BPS
    span = CAP_DAYS - BASE_DAYS
    remaining = CAP_DAYS - days
    denominator = span ** 3
    numerator = (MAX_MULTIPLIER_BPS - 10000) * (denominator - remaining ** 3)
    return 10000 + (numerator + denominator // 2) // denominator


def get_policy(db: Session) -> OwnerCommercialPolicy:
    policy = db.get(OwnerCommercialPolicy, 1)
    if policy is None:
        policy = OwnerCommercialPolicy(id=1, price_per_gib_toman=1000, allow_unlimited_duration=False)
        db.add(policy)
        db.flush()
    return policy


def response(db: Session) -> OwnerPricingResponse:
    policy = get_policy(db)
    presets = db.query(OwnerDurationPreset).order_by(OwnerDurationPreset.duration_days).all()
    return OwnerPricingResponse(
        price_per_gib_toman=policy.price_per_gib_toman,
        allow_unlimited_duration=False,
        duration_pricing_mode="CAPPED_DAILY",
        duration_base_days=BASE_DAYS,
        duration_cap_days=CAP_DAYS,
        duration_max_multiplier=MAX_MULTIPLIER_BPS / 10000,
        duration_examples=[DurationPresetInput(duration_days=days, multiplier=duration_multiplier_basis_points(days) / 10000)
                           for days in (30, 60, 90, 180, 270, 365, 730)],
        duration_presets=[
            DurationPresetInput(
                duration_days=row.duration_days,
                multiplier=row.multiplier_basis_points / 10_000,
                enabled=row.enabled,
            )
            for row in presets
        ],
    )


def enabled_duration_days(db: Session) -> list[int]:
    # Compatibility examples only; these are no longer an allowlist or a cap.
    return [BASE_DAYS, 180, CAP_DAYS]


def update(db: Session, actor: Admin, values: OwnerPricingUpdate) -> OwnerPricingResponse:
    if not admin_hierarchy.is_owner(db, actor):
        raise admin_hierarchy.HierarchyError("pricing_owner_only", "Only Owner can manage pricing")
    policy = get_policy(db)
    policy.price_per_gib_toman = values.price_per_gib_toman
    policy.allow_unlimited_duration = False
    # Keep historical preset rows for history/compatibility; the formula alone
    # prices new Form purchases. An old client cannot re-enable unlimited time.
    db.commit()
    return response(db)


def duration_preset(db: Session, expire: int | None) -> DurationQuote:
    if not expire:
        raise admin_hierarchy.HierarchyError("duration_required", "A positive account duration is required")
    now = int(datetime.now(timezone.utc).timestamp())
    seconds = int(expire) - now
    if seconds <= 0:
        raise admin_hierarchy.HierarchyError("duration_required", "A positive account duration is required")
    days = (seconds + 86399) // 86400
    return duration_days_preset(db, days)


def duration_days_preset(db: Session, duration_days: int) -> DurationQuote:
    return DurationQuote(duration_days, duration_multiplier_basis_points(duration_days))


def form_price(db: Session, settings: MarzhelpAdminSettings, *, data_limit: int | None, expire: int | None) -> int:
    mode = billing_mode(settings)
    if mode == BillingMode.USER_CREDIT:
        raise admin_hierarchy.HierarchyError("user_credit_plan_only", "USER_CREDIT is always Plan Only")
    policy = get_policy(db)
    preset = duration_preset(db, expire)
    if data_limit is None or int(data_limit) <= 0:
        raise admin_hierarchy.HierarchyError("unlimited_form_traffic_forbidden", "Form cannot create unlimited traffic")
    numerator = int(data_limit) * int(policy.price_per_gib_toman) * int(preset.multiplier_basis_points)
    return (numerator + GIB * 10_000 - 1) // (GIB * 10_000)


def adjustment_price(db: Session, *, old_limit: int | None, new_limit: int | None,
                     old_expire: int | None, new_expire: int | None,
                     old_duration_days: int | None = None,
                     old_multiplier_basis_points: int = 10000) -> int:
    """Quote added traffic or a purchased duration extension; never refund edits."""
    if not new_limit:
        raise admin_hierarchy.HierarchyError("unlimited_form_traffic_forbidden", "Form requires finite traffic")
    if old_limit is not None and new_limit < old_limit:
        raise admin_hierarchy.HierarchyError("allocated_traffic_reduction_forbidden", "Admin cannot reduce allocated user traffic")
    extension = max(int(new_expire or 0) - int(old_expire or 0), 0)
    added = max(new_limit - int(old_limit or 0), 0)
    if not extension and not added:
        return 0
    if extension:
        if not old_expire:
            raise admin_hierarchy.HierarchyError("duration_required", "An existing duration is required")
        now = int(datetime.now(timezone.utc).timestamp())
        baseline = old_duration_days or max(BASE_DAYS, (int(old_expire) - now + 86399) // 86400)
        factor = duration_multiplier_basis_points(baseline + (extension + 86399) // 86400)
    else:
        factor = old_multiplier_basis_points
    # A time-only extension buys only the increase in the duration coefficient.
    # Added traffic is priced at the resulting coefficient. No edit refunds.
    weighted_volume = added * factor + int(old_limit or 0) * max(factor - old_multiplier_basis_points, 0)
    policy = get_policy(db)
    denominator = GIB * 10_000
    return (weighted_volume * int(policy.price_per_gib_toman)
            + denominator - 1) // denominator
