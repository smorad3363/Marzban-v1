from pathlib import Path

import pytest

from app.utils.node_logs import (
    NODE_LOG_INTERVAL_RANGE_ERROR,
    NODE_LOG_INTERVAL_VALUE_ERROR,
    parse_node_log_interval,
)


@pytest.mark.parametrize("value", ["0", "0.0", "-1", "-0.001", "10.0001", "11", "nan", "inf", "-inf"])
def test_node_log_interval_rejects_out_of_range_values(value: str):
    with pytest.raises(ValueError, match=NODE_LOG_INTERVAL_RANGE_ERROR):
        parse_node_log_interval(value)


@pytest.mark.parametrize("value", ["abc", "not-a-number", " "])
def test_node_log_interval_rejects_non_numeric_values(value: str):
    with pytest.raises(ValueError, match=NODE_LOG_INTERVAL_VALUE_ERROR):
        parse_node_log_interval(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("", None), ("0.001", 0.001), ("1", 1.0), ("10", 10.0)],
)
def test_node_log_interval_accepts_valid_boundaries(value: str | None, expected: float | None):
    assert parse_node_log_interval(value) == expected


def test_node_logs_websocket_uses_validated_interval_parser():
    source = Path("app/routers/node.py").read_text(encoding="utf-8")
    assert "parse_node_log_interval" in source
    assert 'websocket.query_params.get("interval")' in source
