from app.utils.api_errors import http_error_detail, internal_error_detail, validation_error_detail


def test_machine_code_detail_is_preserved_and_translated():
    detail = http_error_detail(400, "duration_preset_required", "req-123")
    assert detail["error_code"] == "duration_preset_required"
    assert "مدت" in detail["message_fa"]
    assert detail["request_id"] == "req-123"


def test_validation_error_identifies_field_and_reference():
    detail = validation_error_detail(
        [{"loc": ("body", "username"), "type": "missing"}], "req-456"
    )
    assert detail["error_code"] == "VALIDATION_ERROR"
    assert detail["field"] == "username"
    assert detail["fields"]["username"] == "این فیلد الزامی است."
    assert detail["request_id"] == "req-456"


def test_internal_error_never_exposes_exception_details():
    detail = internal_error_detail("req-789")
    assert detail["error_code"] == "INTERNAL_ERROR"
    assert "req-789" in detail["message_fa"]
    assert "traceback" not in str(detail).lower()
