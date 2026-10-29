"""Regression coverage for non-destructive, transaction-safe Xray usage."""
from datetime import datetime, timedelta
from types import SimpleNamespace

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import XrayUserUsageCursor
from app.utils.usage_cursors import accumulate_snapshots, counter_delta, is_same_epoch


def _sample(at, uptime, up, down):
    return {
        "sampled_at": at,
        "uptime": uptime,
        "accounts": {"123.test-user.slot2": {"uplink": up, "downlink": down}},
    }


def test_checkpoint_survives_transaction_failure_without_double_counting():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    start = datetime(2026, 10, 29, 0, 0)
    with Session() as db:
        usage, nodes = accumulate_snapshots(
            db, {None: _sample(start, 10, 100, 200)}, {None: 1}
        )
        assert usage == [{"uid": 123, "value": 300}]
        assert nodes[None] == usage
        db.commit()

        sample = _sample(start + timedelta(seconds=60), 70, 150, 270)
        usage, _ = accumulate_snapshots(db, {None: sample}, {None: 1})
        assert usage == [{"uid": 123, "value": 120}]
        # Simulate a failed MySQL write/commit after reading Xray counters.
        db.rollback()
        db.expire_all()
        saved = db.get(XrayUserUsageCursor, ("main", "123.test-user.slot2"))
        assert saved.uplink == 100
        assert saved.downlink == 200

        sample = _sample(start + timedelta(seconds=120), 130, 180, 280)
        usage, _ = accumulate_snapshots(db, {None: sample}, {None: 1})
        assert usage == [{"uid": 123, "value": 160}]
        db.commit()
        usage, _ = accumulate_snapshots(db, {None: sample}, {None: 1})
        assert usage == []
        db.commit()

        # A different Xray process has lower uptime and fresh counters.
        restart = _sample(start + timedelta(seconds=180), 5, 25, 15)
        usage, _ = accumulate_snapshots(db, {None: restart}, {None: 1})
        assert usage == [{"uid": 123, "value": 40}]
        db.commit()
    engine.dispose()


def test_node_accounting_keeps_independent_cursors_and_applies_coefficient():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    at = datetime(2026, 10, 29, 0, 0)
    with Session() as db:
        usage, nodes = accumulate_snapshots(
            db,
            {None: _sample(at, 5, 10, 10), 7: _sample(at, 40, 40, 60)},
            {None: 1, 7: 1.5},
        )
        assert usage == [{"uid": 123, "value": 170}]
        assert nodes[None] == [{"uid": 123, "value": 20}]
        assert nodes[7] == [{"uid": 123, "value": 150}]
        db.commit()

        # Disconnected node omitted: its watermark must not advance.
        usage, _ = accumulate_snapshots(
            db, {None: _sample(at + timedelta(seconds=60), 65, 12, 12), 7: None},
            {None: 1, 7: 1.5},
        )
        assert usage == [{"uid": 123, "value": 4}]
        db.commit()
        assert db.get(XrayUserUsageCursor, ("node:7", "123.test-user.slot2")).uplink == 40
    engine.dispose()


def test_counter_math_handles_reset_and_uptime_regression():
    cursor = SimpleNamespace(
        uptime_seconds=100, sampled_at=datetime(2026, 10, 29, 0, 0)
    )
    assert is_same_epoch(
        cursor, uptime=160, sampled_at=datetime(2026, 10, 29, 0, 1)
    )
    assert not is_same_epoch(
        cursor, uptime=3, sampled_at=datetime(2026, 10, 29, 0, 1)
    )
    assert counter_delta(200, 150, same_epoch=True) == 50
    assert counter_delta(10, 150, same_epoch=True) == 10
    assert counter_delta(10, 150, same_epoch=False) == 10


def test_snapshot_never_requests_destructive_xray_reset():
    from app.jobs.record_usages import get_user_counter_snapshot

    class FakeAPI:
        def get_sys_stats(self, **kwargs):
            return SimpleNamespace(uptime=100)

        def get_users_stats(self, **kwargs):
            assert kwargs.get("reset") is False
            return [
                SimpleNamespace(name="123.test-user.slot2", link="uplink", value=15),
                SimpleNamespace(name="123.test-user.slot2", link="downlink", value=20),
            ]

    sample = get_user_counter_snapshot(FakeAPI())
    assert sample["accounts"]["123.test-user.slot2"] == {"uplink": 15, "downlink": 20}
