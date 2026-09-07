NODE_LOG_INTERVAL_VALUE_ERROR = "Invalid interval value"
NODE_LOG_INTERVAL_RANGE_ERROR = "Interval must be more than 0 and at most 10 seconds"


def parse_node_log_interval(value: str | None) -> float | None:
    """Parse and validate the optional node-log batching interval."""
    if not value:
        return None

    try:
        interval = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(NODE_LOG_INTERVAL_VALUE_ERROR) from exc

    if not 0 < interval <= 10:
        raise ValueError(NODE_LOG_INTERVAL_RANGE_ERROR)

    return interval
