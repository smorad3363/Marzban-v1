"""Transaction-safe Xray user usage accounting.

Never clear Xray counters during polling. Read cumulative per-account stats,
and advance persistent watermarks in the SAME database transaction as billing.
If a database commit fails, a later poll reads the still-live cumulative counts.
"""

from collections import defaultdict
from datetime import datetime

from app.db.models import XrayUserUsageCursor


def counter_delta(current: int, previous: int, *, same_epoch: bool) -> int:
    current = max(int(current), 0)
    previous = max(int(previous), 0)
    if not same_epoch or current < previous:
        # The Xray process or the account counter was recreated.
        return current
    return current - previous


def is_same_epoch(cursor: XrayUserUsageCursor, *, uptime: int, sampled_at: datetime) -> bool:
    if uptime < cursor.uptime_seconds:
        return False
    elapsed = (sampled_at - cursor.sampled_at).total_seconds()
    uptime_elapsed = uptime - cursor.uptime_seconds
    # Xray uptime is rounded to seconds. Allow poll duration and clock jitter.
    return elapsed >= -2 and abs(elapsed - uptime_elapsed) <= 8


def accumulate_snapshots(db, snapshots: dict, usage_coefficient: dict):
    """Return (combined user deltas, per-node deltas), updating ORM cursors.

    Call in the same transaction as User/Admin updates and monetary settlement.
    Never commit from this function. Missing or failed nodes are left unchanged.
    """
    node_keys = [
        "main" if node_id is None else "node:%d" % node_id
        for node_id, sample in snapshots.items() if sample is not None
    ]
    if not node_keys:
        return [], {}

    previous = {
        (cursor.node_key, cursor.account_name): cursor
        for cursor in (
            db.query(XrayUserUsageCursor)
            .filter(XrayUserUsageCursor.node_key.in_(node_keys))
            .with_for_update()
            .all()
        )
    }
    combined = defaultdict(int)
    per_node = {}

    for node_id, snapshot in snapshots.items():
        if snapshot is None:
            continue
        key_prefix = "main" if node_id is None else "node:%d" % node_id
        current_time = snapshot["sampled_at"]
        uptime = int(snapshot["uptime"])
        factor = float(usage_coefficient.get(node_id, 1))
        node_deltas = defaultdict(int)

        for account_name, stats in snapshot["accounts"].items():
            if len(account_name) > 191:
                raise ValueError("Xray account identifier exceeds accounting key limit")
            user_part = account_name.split(".", 1)[0]
            if not user_part.isdecimal():
                continue

            cursor_key = (key_prefix, account_name)
            cursor = previous.get(cursor_key)
            current_up = max(int(stats.get("uplink", 0)), 0)
            current_down = max(int(stats.get("downlink", 0)), 0)
            same_epoch = (
                cursor is not None
                and is_same_epoch(cursor, uptime=uptime, sampled_at=current_time)
            )
            raw_delta = counter_delta(
                current_up, cursor.uplink if cursor is not None else 0, same_epoch=same_epoch
            ) + counter_delta(
                current_down, cursor.downlink if cursor is not None else 0, same_epoch=same_epoch
            )
            if cursor is None:
                cursor = XrayUserUsageCursor(node_key=key_prefix, account_name=account_name)
                db.add(cursor)
                previous[cursor_key] = cursor
            cursor.uplink = current_up
            cursor.downlink = current_down
            cursor.uptime_seconds = uptime
            cursor.sampled_at = current_time

            delta = int(raw_delta * factor)
            if delta:
                uid = int(user_part)
                combined[uid] += delta
                node_deltas[uid] += delta

        per_node[node_id] = [
            {"uid": uid, "value": value} for uid, value in node_deltas.items()
        ]

    return [{"uid": uid, "value": value} for uid, value in combined.items()], per_node
