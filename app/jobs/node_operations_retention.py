from datetime import datetime, timedelta

from app import scheduler
from app.db import GetDB
from app.db.node_operations import purge_node_operations_before
from config import (
    JOB_NODE_OPERATIONS_RETENTION_INTERVAL,
    NODE_OPERATIONS_EVENT_RETENTION_DAYS,
    NODE_OPERATIONS_RETENTION_BATCH_SIZE,
    NODE_OPERATIONS_TRAFFIC_RETENTION_DAYS,
)


def purge_node_operations_telemetry() -> None:
    """Delete at most one bounded batch per run to cap DB/IO pressure."""

    now = datetime.utcnow()
    with GetDB() as db:
        purge_node_operations_before(
            db,
            event_before=now - timedelta(days=NODE_OPERATIONS_EVENT_RETENTION_DAYS),
            traffic_before=now - timedelta(days=NODE_OPERATIONS_TRAFFIC_RETENTION_DAYS),
            batch_size=NODE_OPERATIONS_RETENTION_BATCH_SIZE,
        )
        db.commit()


scheduler.add_job(
    purge_node_operations_telemetry,
    "interval",
    seconds=JOB_NODE_OPERATIONS_RETENTION_INTERVAL,
    coalesce=True,
    max_instances=1,
)
