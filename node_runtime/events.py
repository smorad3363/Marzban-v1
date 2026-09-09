from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


_CONSUMER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_MAX_PAYLOAD_BYTES = 65536


class EventSpool:
    """Bounded durable event spool with independent consumer ACK cursors."""

    def __init__(self, path: Path | str, max_events: int = 20000):
        self.path = Path(path)
        self.max_events = max(1000, int(max_events))
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _consumer(value: str) -> str:
        if not isinstance(value, str) or _CONSUMER_RE.fullmatch(value) is None:
            raise ValueError("consumer_id must match [A-Za-z0-9._:-]{1,64}")
        return value

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=NORMAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS consumer_offsets ("
                "consumer TEXT PRIMARY KEY, event_id INTEGER NOT NULL DEFAULT 0)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS runtime_meta ("
                "key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0)"
            )
            db.execute(
                "INSERT OR IGNORE INTO runtime_meta(key, value) VALUES('dropped_events_total', 0)"
            )
            stream = db.execute(
                "SELECT value FROM runtime_meta WHERE key='event_stream_id'"
            ).fetchone()
            if stream is None:
                db.execute(
                    "INSERT INTO runtime_meta(key, value) VALUES('event_stream_id', ?)",
                    (uuid4().hex,),
                )

    @property
    def stream_id(self) -> str:
        """Stable identity for this spool lifetime, used for replay dedupe."""

        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT value FROM runtime_meta WHERE key='event_stream_id'"
            ).fetchone()
        if row is None or not str(row[0]).strip():
            raise RuntimeError("event stream identity is unavailable")
        return str(row[0]).strip()[:64]

    def append(self, event_type: str, payload: Mapping[str, Any]) -> int:
        if not isinstance(event_type, str) or not event_type or len(event_type) > 96:
            raise ValueError("event_type must be a non-empty string up to 96 characters")
        if not isinstance(payload, Mapping):
            raise ValueError("event payload must be an object")
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            raise ValueError("event payload exceeds the bounded spool payload size")
        created_at = datetime.now(UTC).isoformat()
        with self._lock, self._connect() as db:
            cursor = db.execute(
                "INSERT INTO events(event_type, payload, created_at) VALUES(?, ?, ?)",
                (event_type, encoded, created_at),
            )
            event_id = int(cursor.lastrowid)
            count = int(db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
            excess = max(0, count - self.max_events)
            if excess:
                db.execute(
                    "DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY id LIMIT ?)",
                    (excess,),
                )
                db.execute(
                    "UPDATE runtime_meta SET value = value + ? WHERE key='dropped_events_total'",
                    (excess,),
                )
            return event_id

    def _offset(self, db: sqlite3.Connection, consumer: str) -> int:
        row = db.execute(
            "SELECT event_id FROM consumer_offsets WHERE consumer=?", (consumer,)
        ).fetchone()
        return int(row[0]) if row else 0

    def read(self, consumer: str, after_id: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        consumer = self._consumer(consumer)
        after_id = max(0, int(after_id))
        limit = max(1, min(int(limit), 256))
        with self._lock, self._connect() as db:
            cursor = max(after_id, self._offset(db, consumer))
            rows = db.execute(
                "SELECT id, event_type, payload, created_at FROM events "
                "WHERE id > ? ORDER BY id LIMIT ?",
                (cursor, limit),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "type": row["event_type"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def ack(self, consumer: str, event_id: int) -> int:
        consumer = self._consumer(consumer)
        event_id = int(event_id)
        if event_id <= 0:
            raise ValueError("event_id must be positive")
        with self._lock, self._connect() as db:
            latest = int(db.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()[0])
            if event_id > latest:
                raise ValueError("cannot ACK beyond the latest available event")
            current = self._offset(db, consumer)
            new_value = max(current, event_id)
            db.execute(
                "INSERT INTO consumer_offsets(consumer, event_id) VALUES(?, ?) "
                "ON CONFLICT(consumer) DO UPDATE SET event_id=excluded.event_id",
                (consumer, new_value),
            )
            return new_value

    def stats(self) -> dict[str, int]:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT COUNT(*), COALESCE(MIN(id), 0), COALESCE(MAX(id), 0) FROM events"
            ).fetchone()
            dropped = db.execute(
                "SELECT value FROM runtime_meta WHERE key='dropped_events_total'"
            ).fetchone()
        return {
            "event_count": int(row[0]),
            "oldest_event_id": int(row[1]),
            "latest_event_id": int(row[2]),
            "dropped_events_total": int(dropped[0]) if dropped else 0,
            "max_events": self.max_events,
        }
