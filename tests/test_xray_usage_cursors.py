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


def test_wall_clock_adjustment_does_not_recharge_cumulative_traffic():
    cursor = SimpleNamespace(uptime_seconds=100, sampled_at=datetime(2026, 10, 29))
    for jump in (-3600, 10, 3600):
        same = is_same_epoch(cursor, uptime=160, sampled_at=cursor.sampled_at + timedelta(seconds=60 + jump))
        assert counter_delta(1100, 1000, same_epoch=same) == 100


def test_history_write_failure_rolls_back_usage_and_cursor(monkeypatch):
    from contextlib import contextmanager
    import pytest
    from sqlalchemy.exc import OperationalError
    from app.jobs import record_usages
    from app.db.models import Admin, User, NodeUserUsage

    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        admin = Admin(username="atomic-admin", hashed_password="x")
        user = User(username="atomic-user", admin=admin, used_traffic=0)
        db.add(user)
        db.commit()
        at = datetime.utcnow()
        sample = {"sampled_at": at, "uptime": 100, "accounts": {
            f"{user.id}.atomic-user": {"uplink": 100, "downlink": 50}}}
        @contextmanager
        def get_db():
            yield db
        monkeypatch.setattr(record_usages, "GetDB", get_db)
        monkeypatch.setattr(record_usages.xray, "nodes", {})
        monkeypatch.setattr(record_usages, "get_user_counter_snapshot", lambda _: sample)
        monkeypatch.setattr(record_usages, "DISABLE_RECORDING_NODE_USAGE", False)
        monkeypatch.setattr(record_usages.money_billing, "settle_used_traffic", lambda *_, **_kwargs: set())
        original = record_usages._record_user_stats
        def fail_history(*args):
            original(*args)
            raise OperationalError("history", {}, Exception(2006, "lost connection"))
        monkeypatch.setattr(record_usages, "_record_user_stats", fail_history)
        with pytest.raises(OperationalError):
            record_usages.record_user_usages()
        db.refresh(user)
        assert user.used_traffic == 0
        assert db.query(XrayUserUsageCursor).count() == 0
        assert db.query(NodeUserUsage).count() == 0
        monkeypatch.setattr(record_usages, "_record_user_stats", original)
        record_usages.record_user_usages()
        db.refresh(user)
        assert user.used_traffic == 150
        assert db.query(NodeUserUsage).one().used_traffic == 150
        record_usages.record_user_usages()
        db.refresh(user)
        assert user.used_traffic == 150
        assert db.query(NodeUserUsage).one().used_traffic == 150
        # A removed account can remain in a polled Xray snapshot. Its history
        # must not violate the user FK and roll back everybody else's traffic.
        sample["accounts"]["999999.removed-user"] = {"uplink": 30, "downlink": 20}
        record_usages.record_user_usages()
        assert db.query(NodeUserUsage).count() == 1
    engine.dispose()
