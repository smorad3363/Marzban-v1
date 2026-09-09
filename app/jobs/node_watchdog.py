import random
from html import escape
from time import time

from app import logger, scheduler, xray
from app.db import GetDB, crud
from app.models.node import NodeStatus
from app.utils.node_watchdog import send_telegram_message


last_check = 0
fail_count = {}
next_try = {}
last_remind = {}
outage_notified = set()


def reconnect_backoff_seconds(
    check_interval: int,
    attempts: int,
    backoff_cap: int,
    *,
    jitter_factor: float | None = None,
) -> int:
    """Existing exponential backoff with bounded downward jitter."""

    base = min(
        int(check_interval) * (2 ** min(max(1, int(attempts)), 20)),
        int(backoff_cap),
    )
    factor = random.uniform(0.85, 1.0) if jitter_factor is None else float(jitter_factor)
    factor = max(0.85, min(1.0, factor))
    return max(
        int(check_interval),
        min(int(backoff_cap), max(1, int(round(base * factor)))),
    )


def notify(settings, message: str) -> None:
    try:
        send_telegram_message(
            settings.telegram_bot_token, settings.telegram_chat_id, message
        )
    except RuntimeError as exc:
        logger.warning("Node watchdog Telegram notification failed: %s", exc)


def node_watchdog() -> None:
    global last_check
    now = int(time())

    with GetDB() as db:
        settings = crud.get_node_watchdog_settings(db)
        if not settings.enabled or not settings.telegram_bot_token or not settings.telegram_chat_id:
            return
        if now - last_check < settings.check_interval:
            return
        last_check = now
        nodes = crud.get_nodes(db)

        for node in nodes:
            node_id = node.id
            status = node.status
            if not node.watchdog_enabled or status == NodeStatus.disabled:
                fail_count.pop(node_id, None)
                next_try.pop(node_id, None)
                outage_notified.discard(node_id)
                continue

            if status == NodeStatus.connected:
                if node_id in outage_notified:
                    notify(
                        settings,
                        f"🟢 <b>{escape(node.name)}</b> (id {node_id}) is connected again.",
                    )
                fail_count[node_id] = 0
                next_try[node_id] = 0
                last_remind[node_id] = 0
                outage_notified.discard(node_id)
                continue

            if now < next_try.get(node_id, 0):
                continue

            attempts = fail_count.get(node_id, 0) + 1
            fail_count[node_id] = attempts
            backoff = reconnect_backoff_seconds(
                settings.check_interval,
                attempts,
                settings.backoff_cap,
            )
            next_try[node_id] = now + backoff

            if node_id not in outage_notified:
                detail = f" — {escape(node.message)}" if node.message else ""
                notify(
                    settings,
                    f"🔴 <b>{escape(node.name)}</b> (id {node_id}) is "
                    f"<b>{escape(status.value)}</b>{detail}\n✅ Reconnect triggered.",
                )
                outage_notified.add(node_id)

            xray.operations.connect_node(
                node_id,
                reconnect_mode="automatic",
                trigger_reason=f"watchdog_{status.value}",
                reconnect_attempt=attempts,
            )

            if attempts > 3 and now - last_remind.get(node_id, 0) >= settings.remind_every:
                notify(
                    settings,
                    f"🔴 <b>{escape(node.name)}</b> (id {node_id}) is still "
                    f"<b>{escape(status.value)}</b> after {attempts} reconnect attempts. "
                    f"Next retry in {backoff}s.",
                )
                last_remind[node_id] = now

        existing_ids = {node.id for node in nodes}
        for state in (fail_count, next_try, last_remind):
            for node_id in set(state) - existing_ids:
                state.pop(node_id, None)
        outage_notified.intersection_update(existing_ids)


scheduler.add_job(
    node_watchdog,
    "interval",
    seconds=5,
    coalesce=True,
    max_instances=1,
    id="node-watchdog",
    replace_existing=True,
)
