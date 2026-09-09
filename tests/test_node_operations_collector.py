from pathlib import Path

from app.utils.bandwidth import BandwidthStore, MAX_RATE_INTERVAL_SECONDS


def test_bandwidth_point_exposes_actual_sample_duration():
    store = BandwidthStore()
    assert store.observe(7, 100, 200, sampled_at=10.0) is None
    point = store.observe(7, 300, 600, sampled_at=22.5)
    assert point is not None
    assert point.sample_seconds == 12.5
    assert point.uplink_bps == 192.0
    assert point.downlink_bps == 384.0


def test_bandwidth_long_gap_does_not_invent_persistable_duration():
    store = BandwidthStore()
    store.observe(3, 100, 200, sampled_at=1.0)
    assert store.observe(3, 100, 200, sampled_at=2.0) is not None
    assert (
        store.observe(
            3,
            999_999,
            999_999,
            sampled_at=2.0 + MAX_RATE_INTERVAL_SECONDS + 1,
        )
        is None
    )


def test_collector_uses_existing_reset_poll_and_skips_failed_samples_before_observe():
    source = Path("app/jobs/record_usages.py").read_text(encoding="utf-8")
    assert source.count("api.get_outbounds_stats(reset=True, timeout=10)") == 1

    function = source.split("def record_node_usages():", 1)[1].split(
        "scheduler.add_job(record_user_usages", 1
    )[0]
    failed_guard = function.index("if params is None:")
    observe_call = function.index("bandwidth_store.observe")
    assert failed_guard < observe_call
    assert "record_traffic_bucket" in source
    assert '"sample_seconds": point.sample_seconds' in source


def test_zero_traffic_samples_can_reach_history_without_changing_legacy_accounting():
    source = Path("app/jobs/record_usages.py").read_text(encoding="utf-8")
    function = source.split("def record_node_usages():", 1)[1].split(
        "scheduler.add_job(record_user_usages", 1
    )[0]

    # The previous early return on zero total traffic would erase idle time from
    # durable averages. Legacy System/NodeUsage writes remain guarded by nonzero
    # totals, while Node Operations samples are persisted afterwards.
    assert "if not (total_up or total_down):\n        return" not in function
    assert "if total_up or total_down:" in function
    assert function.index("if total_up or total_down:") < function.index(
        "_persist_node_operations_traffic(traffic_samples)"
    )


def test_node_operations_retention_is_configurable_and_bounded():
    config = Path("config.py").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")
    job = Path("app/jobs/node_operations_retention.py").read_text(encoding="utf-8")

    for name in (
        "NODE_OPERATIONS_EVENT_RETENTION_DAYS",
        "NODE_OPERATIONS_TRAFFIC_RETENTION_DAYS",
        "NODE_OPERATIONS_RETENTION_BATCH_SIZE",
        "JOB_NODE_OPERATIONS_RETENTION_INTERVAL",
    ):
        assert name in config
        assert name in env_example
        assert name in job

    assert "min(config(\"NODE_OPERATIONS_RETENTION_BATCH_SIZE\"" in config
    assert "max_instances=1" in job
    assert "purge_node_operations_before(" in job
