from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime


HISTORY_SECONDS = 300
MAX_HISTORY_SAMPLES = 120


@dataclass(frozen=True)
class BandwidthPoint:
    sampled_at: float
    uplink_bps: float
    downlink_bps: float


class BandwidthStore:
    """Small process-local cache fed by the existing Xray usage collector.

    The collector is the sole reader of reset=True Xray outbound counters. This
    store never polls Xray itself, so live monitoring cannot steal accounting
    deltas. History is bounded to keep memory predictable on small servers.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_poll: dict[int | None, float] = {}
        self._history: dict[int | None, deque[BandwidthPoint]] = {}

    def clear(self) -> None:
        with self._lock:
            self._last_poll.clear()
            self._history.clear()

    def observe(
        self,
        node_id: int | None,
        uplink_bytes: int,
        downlink_bytes: int,
        *,
        sampled_at: float | None = None,
    ) -> BandwidthPoint | None:
        now = float(sampled_at if sampled_at is not None else time.time())
        with self._lock:
            previous = self._last_poll.get(node_id)
            self._last_poll[node_id] = now
            if previous is None or now <= previous:
                return None

            elapsed = now - previous
            point = BandwidthPoint(
                sampled_at=now,
                uplink_bps=max(0.0, float(uplink_bytes) * 8.0 / elapsed),
                downlink_bps=max(0.0, float(downlink_bytes) * 8.0 / elapsed),
            )
            history = self._history.setdefault(
                node_id, deque(maxlen=MAX_HISTORY_SAMPLES)
            )
            history.append(point)
            cutoff = now - HISTORY_SECONDS
            while history and history[0].sampled_at < cutoff:
                history.popleft()
            return point

    def snapshot(
        self,
        node_id: int | None,
        *,
        now: float | None = None,
        stale_after: float = 90.0,
    ) -> dict:
        current = float(now if now is not None else time.time())
        with self._lock:
            last_poll = self._last_poll.get(node_id)
            history = tuple(self._history.get(node_id, ()))

        if last_poll is None:
            return {
                "state": "offline",
                "sampled_at": None,
                "sample_age_seconds": None,
                "uplink_bps": 0.0,
                "downlink_bps": 0.0,
                "peak_5m_uplink_bps": 0.0,
                "peak_5m_downlink_bps": 0.0,
            }

        if not history:
            return {
                "state": "warming_up",
                "sampled_at": datetime.utcfromtimestamp(last_poll),
                "sample_age_seconds": max(0.0, current - last_poll),
                "uplink_bps": 0.0,
                "downlink_bps": 0.0,
                "peak_5m_uplink_bps": 0.0,
                "peak_5m_downlink_bps": 0.0,
            }

        point = history[-1]
        age = max(0.0, current - point.sampled_at)
        state = "stale" if age > stale_after else "online"
        return {
            "state": state,
            "sampled_at": datetime.utcfromtimestamp(point.sampled_at),
            "sample_age_seconds": age,
            "uplink_bps": point.uplink_bps,
            "downlink_bps": point.downlink_bps,
            "peak_5m_uplink_bps": max(item.uplink_bps for item in history),
            "peak_5m_downlink_bps": max(item.downlink_bps for item in history),
        }


bandwidth_store = BandwidthStore()
