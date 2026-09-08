"""Stable, Persian API error envelopes without internal implementation details."""

from __future__ import annotations

from typing import Any
import re


STATUS_CODES = {
    400: ("BAD_REQUEST", "درخواست نامعتبر است. ورودی‌ها را بررسی کنید."),
    401: ("AUTHENTICATION_REQUIRED", "برای ادامه دوباره وارد حساب شوید."),
    403: ("PERMISSION_DENIED", "اجازه انجام این عملیات را ندارید."),
    404: ("NOT_FOUND", "مورد درخواستی پیدا نشد."),
    409: ("DATABASE_CONFLICT", "این تغییر با وضعیت فعلی داده‌ها تداخل دارد."),
    422: ("VALIDATION_ERROR", "اطلاعات واردشده معتبر نیست."),
    429: ("RATE_LIMITED", "تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید."),
    500: ("INTERNAL_ERROR", "خطای داخلی رخ داد؛ با کد پیگیری با پشتیبانی تماس بگیرید."),
    502: ("BAD_GATEWAY", "سرویس بالادستی پاسخ معتبر نداد."),
    503: ("SERVICE_UNAVAILABLE", "سرویس موقتاً در دسترس نیست."),
    504: ("GATEWAY_TIMEOUT", "پاسخ سرویس بالادستی بیش از حد طول کشید."),
}

ERROR_CODE_MESSAGES = {
    "category_in_use": "این دسته‌بندی پلن فعال دارد؛ ابتدا پلن‌ها را منتقل یا بایگانی کنید.",
    "duration_present_required": "برای ساخت دستی کاربر، مدت سرویس را انتخاب کنید.",
    "duration_preset_required": "مدت انتخاب‌شده مجاز نیست؛ یکی از مدت‌های تعیین‌شده توسط Owner را انتخاب کنید.",
    "plan_not_found": "پلن انتخاب‌شده پیدا نشد یا غیرفعال است.",
    "plan_not_allowed": "اجازه استفاده از این پلن را ندارید.",
    "plan_required": "برای این عملیات انتخاب پلن الزامی است.",
    "admin_not_found": "ادمین موردنظر پیدا نشد.",
    "admin_has_children": "این ادمین زیرمجموعه دارد؛ ابتدا زیرمجموعه‌ها را منتقل یا حذف کنید.",
    "admin_delete_history_blocked": "این ادمین سابقه حسابداری یا ممیزی دارد و حذف فیزیکی آن مجاز نیست.",
    "admin_delete_debt_blocked": "این ادمین مانده اعتبار یا بدهی تسویه‌نشده دارد.",
    "owner_delete_forbidden": "حذف حساب Owner مجاز نیست.",
    "access_group_required": "انتخاب Access Group الزامی است.",
    "access_group_not_found": "Access Group انتخاب‌شده پیدا نشد.",
    "access_group_not_allowed": "اجازه استفاده از این Access Group را ندارید.",
    "username_already_exists": "این نام کاربری قبلاً استفاده شده است.",
    "permission_denied": "اجازه انجام این عملیات را ندارید.",
    "insufficient_credit": "اعتبار کافی برای انجام این عملیات وجود ندارد.",
}

FIELD_MESSAGES = {
    "missing": "این فیلد الزامی است.",
    "string_too_short": "مقدار این فیلد کوتاه‌تر از حد مجاز است.",
    "string_too_long": "مقدار این فیلد بلندتر از حد مجاز است.",
    "greater_than_equal": "مقدار این فیلد از حداقل مجاز کمتر است.",
    "less_than_equal": "مقدار این فیلد از حداکثر مجاز بیشتر است.",
    "int_parsing": "این فیلد باید عدد صحیح باشد.",
    "float_parsing": "این فیلد باید عدد باشد.",
    "bool_parsing": "این فیلد باید مقدار درست یا نادرست داشته باشد.",
}

SAFE_DETAIL_KEYS = {
    "allowed_actions",
    "fields",
    "forbidden_users",
    "impact",
    "missing_users",
    "retry_after",
}

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
ERROR_CODE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")


def safe_request_id(value: object, fallback: str) -> str:
    return str(value) if isinstance(value, str) and REQUEST_ID_PATTERN.fullmatch(value) else fallback


def contains_persian(value: object) -> bool:
    return isinstance(value, str) and any("\u0600" <= char <= "\u06ff" for char in value)


def request_id(request: Any) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def http_error_detail(status_code: int, detail: object, trace_id: str) -> dict[str, Any]:
    fallback_code, fallback_message = STATUS_CODES.get(
        status_code,
        ("REQUEST_FAILED", "انجام درخواست ممکن نشد. دوباره تلاش کنید."),
    )
    source = detail if isinstance(detail, dict) else {}
    token_detail = detail if isinstance(detail, str) and ERROR_CODE_PATTERN.fullmatch(detail) else None
    code = str(source.get("error_code") or source.get("code") or token_detail or fallback_code)
    candidate_message = source.get("message_fa") or source.get("message") or detail
    message_fa = candidate_message if contains_persian(candidate_message) else ERROR_CODE_MESSAGES.get(code, fallback_message)
    result: dict[str, Any] = {
        "error_code": code,
        "message_fa": message_fa,
        "request_id": trace_id,
    }
    field = source.get("field")
    if isinstance(field, str):
        result["field"] = field
    for key in SAFE_DETAIL_KEYS:
        if key in source:
            result[key] = source[key]
    return result


def validation_error_detail(errors: list[dict[str, Any]], trace_id: str) -> dict[str, Any]:
    fields: dict[str, str] = {}
    for error in errors:
        location = error.get("loc") or ()
        field = str(location[-1]) if location else "request"
        fields[field] = FIELD_MESSAGES.get(
            str(error.get("type", "")).split(".")[-1],
            "مقدار این فیلد معتبر نیست.",
        )
    first_field = next(iter(fields), "request")
    return {
        "error_code": "VALIDATION_ERROR",
        "message_fa": fields.get(first_field, "اطلاعات واردشده معتبر نیست."),
        "field": first_field,
        "fields": fields,
        "request_id": trace_id,
    }


def internal_error_detail(trace_id: str) -> dict[str, str]:
    return {
        "error_code": "INTERNAL_ERROR",
        "message_fa": f"خطای داخلی رخ داد. کد پیگیری: {trace_id}",
        "request_id": trace_id,
    }
