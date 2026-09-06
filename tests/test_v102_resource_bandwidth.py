import inspect
from pathlib import Path

from app.device_limit.engine import HIT_BUFFER_CAPACITY
from app.models.admin import Admin as AdminSchema
from app.routers.node import get_bandwidth
from app.utils.bandwidth import (
    BandwidthStore,
    MAX_HISTORY_SAMPLES,
    MAX_RATE_INTERVAL_SECONDS,
)


def test_low_memory_defaults_are_explicit_and_overrideable():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    config = Path("config.py").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "${MYSQL_INNODB_BUFFER_POOL_SIZE:-128M}" in compose
    assert "${SQLALCHEMY_POOL_SIZE:-5}" in compose
    assert "${SQLIALCHEMY_MAX_OVERFLOW:-5}" in compose
    assert 'default=5' in config
    assert 'XRAY_STATS_MAX_WORKERS' in config
    assert 'default=2' in config
    assert "MYSQL_INNODB_BUFFER_POOL_SIZE = 128M" in env_example
    assert "XRAY_STATS_MAX_WORKERS = 2" in env_example


def test_phpmyadmin_is_not_started_in_the_default_profile():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    phpmyadmin = compose.split("  phpmyadmin:", 1)[1]
    assert 'profiles: ["tools"]' in phpmyadmin
    assert "restart: unless-stopped" in phpmyadmin


def test_bandwidth_route_is_owner_protected():
    dependency = inspect.signature(get_bandwidth).parameters["_"].default.dependency
    assert dependency.__func__ is AdminSchema.check_sudo_admin.__func__


def test_bandwidth_first_sample_warms_then_uses_elapsed_time():
    store = BandwidthStore()
    assert store.observe(7, 1_000_000, 2_000_000, sampled_at=100.0) is None
    warm = store.snapshot(7, now=100.0)
    assert warm["state"] == "warming_up"
    assert warm["total_bps"] if "total_bps" in warm else 0 == 0

    point = store.observe(7, 1_000_000, 2_000_000, sampled_at=110.0)
    assert point is not None
    assert point.uplink_bps == 800_000
    assert point.downlink_bps == 1_600_000
    snapshot = store.snapshot(7, now=110.0)
    assert snapshot["state"] == "online"
    assert snapshot["uplink_bps"] == 800_000
    assert snapshot["downlink_bps"] == 1_600_000


def test_bandwidth_long_gap_restarts_warmup_instead_of_inventing_rate():
    store = BandwidthStore()
    store.observe(3, 100, 200, sampled_at=10.0)
    assert store.observe(3, 100, 200, sampled_at=20.0) is not None

    assert (
        store.observe(
            3,
            999_999_999,
            999_999_999,
            sampled_at=20.0 + MAX_RATE_INTERVAL_SECONDS + 1,
        )
        is None
    )
    snapshot = store.snapshot(3, now=20.0 + MAX_RATE_INTERVAL_SECONDS + 1)
    assert snapshot["state"] == "warming_up"
    assert snapshot["uplink_bps"] == 0
    assert snapshot["downlink_bps"] == 0


def test_bandwidth_history_is_bounded():
    store = BandwidthStore()
    store.observe(1, 0, 0, sampled_at=1.0)
    for index in range(1, MAX_HISTORY_SAMPLES + 50):
        store.observe(1, 100, 100, sampled_at=1.0 + index)
    assert len(store._history[1]) <= MAX_HISTORY_SAMPLES


def test_device_limit_hit_buffer_remains_bounded_alongside_telemetry():
    # Prevent future monitoring changes from silently replacing the existing
    # bounded device-limit event memory with an unbounded collection.
    assert HIT_BUFFER_CAPACITY == 128
