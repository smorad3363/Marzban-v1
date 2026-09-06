from pathlib import Path


def write_new(path: str, content: str) -> None:
    p = Path(path)
    if p.exists():
        raise SystemExit(f"{path}: already exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Same-batch duplicate event IDs must never be delivered twice.
replace_once(
    "app/xray/node_protocol_v2.py",
    '''    events: list[RuntimeEvent] = []
    highest_seen = max(0, int(after_event_id))
    previous_wire_id = 0
    for raw_event in raw_events:''',
    '''    events: list[RuntimeEvent] = []
    highest_seen = max(0, int(after_event_id))
    previous_wire_id = 0
    seen_ids: set[int] = set()
    for raw_event in raw_events:''',
)
replace_once(
    "app/xray/node_protocol_v2.py",
    '''        highest_seen = max(highest_seen, event_id)
        if event_id <= after_event_id:
            continue
        if not isinstance(event_type, str) or not event_type or len(event_type) > 96:''',
    '''        highest_seen = max(highest_seen, event_id)
        if event_id <= after_event_id or event_id in seen_ids:
            continue
        seen_ids.add(event_id)
        if not isinstance(event_type, str) or not event_type or len(event_type) > 96:''',
)
replace_once(
    "tests/test_v102_node_runtime_protocol.py",
    '''    assert [event.event_id for event in events] == [6, 6, 7]''',
    '''    assert [event.event_id for event in events] == [6, 7]
    assert events[0].payload["line"] == "new"''',
)

# Strict-mTLS-compatible server certificate pinning for REST/V2 nodes.
replace_once(
    "app/xray/node.py",
    '''    def _pin_server_certificate(self):
        self._node_cert = ssl.get_server_certificate((self.address, self.port))
        self._node_certfile = string_to_temp_file(self._node_cert)
        self.session.verify = self._node_certfile.name
''',
    '''    def _pin_server_certificate(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile=self._certfile.name, keyfile=self._keyfile.name)
        with socket.create_connection((self.address, self.port), timeout=3) as raw_socket:
            with context.wrap_socket(raw_socket, server_hostname=self.address) as tls_socket:
                certificate_der = tls_socket.getpeercert(binary_form=True)
        if not certificate_der:
            raise ssl.SSLError("Node did not present a server certificate")
        self._node_cert = ssl.DER_cert_to_PEM_cert(certificate_der)
        self._node_certfile = string_to_temp_file(self._node_cert)
        self.session.verify = self._node_certfile.name
''',
)

# Reliable V2 consumers: ACK only after callback processing succeeds.
replace_once(
    "app/xray/node.py",
    '''    def _bg_fetch_logs(self):
        while self._logs_queues:
            if not self._session_id:
                time.sleep(0.2)
                continue
            try:
                data = self.make_request(
                    "/v2/events",
                    timeout=5,
                    after_id=self._last_event_id,
                    limit=100,
                )
                events, highest_seen = parse_event_batch(data, self._last_event_id)
                for event in events:
                    if event.event_type != "xray.log":
                        continue
                    line = event.payload.get("line")
                    if not isinstance(line, str) or not line:
                        continue
                    for buf in list(self._logs_queues):
                        buf.append(line)
                if highest_seen > self._last_event_id:
                    self.make_request(
                        "/v2/events/ack",
                        timeout=3,
                        event_id=highest_seen,
                    )
                    self._last_event_id = highest_seen
                if not events:
                    time.sleep(0.2)
            except (NodeAPIError, RuntimeProtocolError):
                time.sleep(1)
''',
    '''    def _event_batch(self, consumer_id: str, after_id: int, limit: int = 100):
        data = self.make_request(
            "/v2/events",
            timeout=5,
            consumer_id=consumer_id,
            after_id=after_id,
            limit=limit,
        )
        return parse_event_batch(data, after_id)

    def _ack_event_batch(self, consumer_id: str, event_id: int) -> None:
        self.make_request(
            "/v2/events/ack",
            timeout=3,
            consumer_id=consumer_id,
            event_id=event_id,
        )

    def consume_events(self, consumer_id: str, callback, should_stop) -> None:
        """Consume durable V2 events and ACK only after successful callbacks."""
        cursor = 0
        while not should_stop():
            if not self._session_id:
                time.sleep(0.2)
                continue
            try:
                events, highest_seen = self._event_batch(consumer_id, cursor)
            except NodeAPIError:
                time.sleep(1)
                continue
            for event in events:
                if event.event_type != "xray.log":
                    continue
                line = event.payload.get("line")
                if isinstance(line, str) and line:
                    callback(line)
            if highest_seen > cursor:
                self._ack_event_batch(consumer_id, highest_seen)
                cursor = highest_seen
            if not events:
                time.sleep(0.2)

    def _bg_fetch_logs(self):
        while self._logs_queues:
            if not self._session_id:
                time.sleep(0.2)
                continue
            try:
                events, highest_seen = self._event_batch("panel-logs", self._last_event_id)
                for event in events:
                    if event.event_type != "xray.log":
                        continue
                    line = event.payload.get("line")
                    if not isinstance(line, str) or not line:
                        continue
                    for buf in list(self._logs_queues):
                        buf.append(line)
                if highest_seen > self._last_event_id:
                    self._ack_event_batch("panel-logs", highest_seen)
                    self._last_event_id = highest_seen
                if not events:
                    time.sleep(0.2)
            except (NodeAPIError, RuntimeProtocolError):
                time.sleep(1)
''',
)

# Device Limit gets a durable V2 consumer and a separate runtime-capability trust gate.
replace_once(
    "app/device_limit/engine.py",
    '''        self._limited_user_ids: set[int] | None = None
        self._untrusted_ip_sources: set[str] = set()
        self._last_user_cache_refresh = 0.0''',
    '''        self._limited_user_ids: set[int] | None = None
        self._untrusted_ip_sources: set[str] = set()
        self._runtime_untrusted_ip_sources: set[str] = set()
        self._last_user_cache_refresh = 0.0''',
)
replace_once(
    "app/device_limit/engine.py",
    '''    def forget_source_ip_trust(self, source_name: str) -> None:
        with self._lock:
            self._untrusted_ip_sources.discard(source_name)

    def _refresh_node_ip_source_policies(self, db) -> None:''',
    '''    def forget_source_ip_trust(self, source_name: str) -> None:
        with self._lock:
            self._untrusted_ip_sources.discard(source_name)

    def set_runtime_source_ip_trust(self, source_name: str, trusted: bool) -> None:
        if not source_name.startswith("node:"):
            return
        with self._lock:
            if trusted:
                self._runtime_untrusted_ip_sources.discard(source_name)
            else:
                self._runtime_untrusted_ip_sources.add(source_name)

    def forget_runtime_source_ip_trust(self, source_name: str) -> None:
        with self._lock:
            self._runtime_untrusted_ip_sources.discard(source_name)

    def _refresh_node_ip_source_policies(self, db) -> None:''',
)
replace_once(
    "app/device_limit/engine.py",
    '''    def _collect(self, source, source_name: str) -> None:
        generation = (getattr(source, "process", None), getattr(source, "_session_id", None))
        try:
            with source.get_logs() as logs:''',
    '''    def _collect(self, source, source_name: str) -> None:
        generation = (getattr(source, "process", None), getattr(source, "_session_id", None))
        runtime_handshake = getattr(source, "runtime_handshake", None)
        if source_name.startswith("node:"):
            if runtime_handshake is None:
                self.forget_runtime_source_ip_trust(source_name)
            else:
                self.set_runtime_source_ip_trust(
                    source_name,
                    bool(getattr(runtime_handshake, "supports_direct_client_ip", False)),
                )
        consume_events = getattr(source, "consume_events", None)
        if callable(consume_events):
            def should_stop() -> bool:
                if self._stop.is_set():
                    return True
                if source_name.startswith("node:"):
                    node_id = int(source_name.split(":", 1)[1])
                    if xray.nodes.get(node_id) is not source:
                        return True
                return generation != (
                    getattr(source, "process", None),
                    getattr(source, "_session_id", None),
                )

            try:
                consume_events(
                    "device-limit",
                    lambda line: self.record_log(line, source_name),
                    should_stop,
                )
            except Exception as exc:
                logger.debug("Device-limit durable collector %s stopped: %s", source_name, exc)
            return
        try:
            with source.get_logs() as logs:''',
)
replace_once(
    "app/device_limit/engine.py",
    '''            untrusted_ip_source = source_name in self._untrusted_ip_sources''',
    '''            untrusted_ip_source = (
                source_name in self._untrusted_ip_sources
                or source_name in self._runtime_untrusted_ip_sources
            )''',
)
replace_once(
    "app/device_limit/engine.py",
    '''                    "untrusted_ip_sources": sorted(self._untrusted_ip_sources),''',
    '''                    "untrusted_ip_sources": sorted(
                        self._untrusted_ip_sources | self._runtime_untrusted_ip_sources
                    ),''',
)

write_new("node_runtime/__init__.py", '''"""Standalone Marzban V1 Node Runtime V2."""\n''')

write_new("node_runtime/config.py", '''from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class RuntimeSettings:
    service_host: str
    service_port: int
    api_host: str
    api_port: int
    xray_executable: str
    xray_assets_path: str
    ssl_cert_file: Path
    ssl_key_file: Path
    ssl_client_cert_file: Path
    event_db_path: Path
    runtime_version: str
    inbounds: tuple[str, ...]
    max_events: int

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        client_cert = os.getenv("SSL_CLIENT_CERT_FILE", "").strip()
        if not client_cert:
            raise RuntimeError("SSL_CLIENT_CERT_FILE is required for the V2 node runtime")
        inbounds = tuple(
            item.strip()
            for item in os.getenv("INBOUNDS", "").split(",")
            if item.strip()
        )
        return cls(
            service_host=os.getenv("NODE_RUNTIME_HOST", "0.0.0.0"),
            service_port=_bounded_int("NODE_RUNTIME_PORT", 62050, 1, 65535),
            api_host=os.getenv("XRAY_API_HOST", "0.0.0.0"),
            api_port=_bounded_int("XRAY_API_PORT", 62051, 1, 65535),
            xray_executable=os.getenv("XRAY_EXECUTABLE_PATH", "/usr/local/bin/xray"),
            xray_assets_path=os.getenv("XRAY_ASSETS_PATH", "/usr/local/share/xray"),
            ssl_cert_file=Path(os.getenv("SSL_CERT_FILE", "/var/lib/marzban-node/ssl_cert.pem")),
            ssl_key_file=Path(os.getenv("SSL_KEY_FILE", "/var/lib/marzban-node/ssl_key.pem")),
            ssl_client_cert_file=Path(client_cert),
            event_db_path=Path(os.getenv("EVENT_DB_PATH", "/var/lib/marzban-node/events.sqlite3")),
            runtime_version=os.getenv("NODE_RUNTIME_VERSION", "dev").strip() or "dev",
            inbounds=inbounds,
            max_events=_bounded_int("EVENT_MAX_ROWS", 20000, 1000, 1000000),
        )
''')

write_new("node_runtime/events.py", '''from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


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
''')

write_new("node_runtime/certificates.py", '''from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def ensure_server_certificate(cert_path: Path, key_path: Path) -> None:
    cert_exists = cert_path.is_file()
    key_exists = key_path.is_file()
    if cert_exists and key_exists:
        return
    if cert_exists != key_exists:
        raise RuntimeError("Node TLS certificate/key pair is incomplete; refusing to overwrite it")
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Gozargah")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("Gozargah")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_bytes = certificate.public_bytes(serialization.Encoding.PEM)
    key_tmp = key_path.with_suffix(key_path.suffix + ".tmp")
    cert_tmp = cert_path.with_suffix(cert_path.suffix + ".tmp")
    key_tmp.write_bytes(key_bytes)
    cert_tmp.write_bytes(cert_bytes)
    os.chmod(key_tmp, 0o600)
    os.chmod(cert_tmp, 0o644)
    os.replace(key_tmp, key_path)
    os.replace(cert_tmp, cert_path)
''')

write_new("node_runtime/core.py", '''from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
from collections import deque
from typing import Any

from node_runtime.config import RuntimeSettings
from node_runtime.events import EventSpool


logger = logging.getLogger("marzban.node_runtime")


def prepare_xray_config(raw_config: str, peer_ip: str, settings: RuntimeSettings) -> dict[str, Any]:
    try:
        config = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to decode Xray config: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("Xray config must be a JSON object")
    api_tag = (config.get("api") or {}).get("tag")
    retained_inbounds = []
    for inbound in config.get("inbounds") or []:
        if not isinstance(inbound, dict):
            continue
        if inbound.get("protocol") == "dokodemo-door" and inbound.get("tag") == "API_INBOUND":
            continue
        if settings.inbounds and inbound.get("tag") not in settings.inbounds:
            continue
        retained_inbounds.append(inbound)
    config["inbounds"] = retained_inbounds
    routing = config.setdefault("routing", {})
    rules = routing.get("rules") or []
    if api_tag:
        rules = [rule for rule in rules if not (isinstance(rule, dict) and rule.get("outboundTag") == api_tag)]
    config["api"] = {
        "services": ["HandlerService", "StatsService", "LoggerService"],
        "tag": "API",
    }
    config["stats"] = {}
    api_inbound = {
        "listen": settings.api_host,
        "port": settings.api_port,
        "protocol": "dokodemo-door",
        "settings": {"address": "127.0.0.1"},
        "streamSettings": {
            "security": "tls",
            "tlsSettings": {
                "certificates": [{
                    "certificateFile": str(settings.ssl_cert_file),
                    "keyFile": str(settings.ssl_key_file),
                }]
            },
        },
        "tag": "API_INBOUND",
    }
    config["inbounds"].insert(0, api_inbound)
    rules.insert(0, {
        "inboundTag": ["API_INBOUND"],
        "source": ["127.0.0.1", peer_ip],
        "outboundTag": "API",
        "type": "field",
    })
    routing["rules"] = rules
    log_config = config.setdefault("log", {})
    if log_config.get("logLevel") in ("none", "error"):
        log_config["logLevel"] = "warning"
    return config


class XRayRuntimeCore:
    def __init__(self, settings: RuntimeSettings, spool: EventSpool):
        self.settings = settings
        self.spool = spool
        self.process: subprocess.Popen[str] | None = None
        self._lock = threading.RLock()
        self._last_logs: deque[str] = deque(maxlen=100)
        self.version = self._get_version()

    def _get_version(self) -> str | None:
        output = subprocess.check_output(
            [self.settings.xray_executable, "version"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
        match = re.match(r"^Xray (\\d+\\.\\d+\\.\\d+)", output)
        return match.group(1) if match else None

    @property
    def started(self) -> bool:
        process = self.process
        return bool(process is not None and process.poll() is None)

    def _capture_logs(self, process: subprocess.Popen[str]) -> None:
        stream = process.stdout
        if stream is None:
            return
        while self.process is process:
            line = stream.readline()
            if not line:
                if process.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line = line.rstrip("\\r\\n")
            if not line:
                continue
            self._last_logs.append(line)
            try:
                self.spool.append("xray.log", {"line": line})
            except Exception as exc:
                logger.warning("Unable to spool Xray log event: %s", exc)

    def start(self, raw_config: str, peer_ip: str) -> None:
        with self._lock:
            if self.started:
                raise RuntimeError("Xray is started already")
            prepared = prepare_xray_config(raw_config, peer_ip, self.settings)
            environment = os.environ.copy()
            environment["XRAY_LOCATION_ASSET"] = self.settings.xray_assets_path
            process = subprocess.Popen(
                [self.settings.xray_executable, "run", "-config", "stdin:"],
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.process = process
            if process.stdin is None:
                self.process = None
                process.kill()
                raise RuntimeError("Unable to open Xray configuration stdin")
            process.stdin.write(json.dumps(prepared, ensure_ascii=False))
            process.stdin.flush()
            process.stdin.close()
            threading.Thread(target=self._capture_logs, args=(process,), daemon=True).start()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if process.poll() is not None:
                self.process = None
                last_log = self._last_logs[-1] if self._last_logs else "Xray exited during startup"
                raise RuntimeError(last_log)
            time.sleep(0.1)

    def stop(self) -> None:
        with self._lock:
            process = self.process
            if process is None:
                return
            self.process = None
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

    def restart(self, raw_config: str, peer_ip: str) -> None:
        self.stop()
        self.start(raw_config, peer_ip)
''')

write_new("node_runtime/service.py", '''from __future__ import annotations

import threading
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from node_runtime.config import RuntimeSettings
from node_runtime.core import XRayRuntimeCore
from node_runtime.events import EventSpool


class SessionBody(BaseModel):
    session_id: UUID


class ConfigBody(SessionBody):
    config: str = Field(min_length=2)


class EventsBody(SessionBody):
    consumer_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    after_id: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=256)


class AckBody(SessionBody):
    consumer_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._:-]+$")
    event_id: int = Field(gt=0)


def create_app(
    settings: RuntimeSettings,
    spool: EventSpool | None = None,
    core: XRayRuntimeCore | None = None,
) -> FastAPI:
    spool = spool or EventSpool(settings.event_db_path, settings.max_events)
    core = core or XRayRuntimeCore(settings, spool)
    app = FastAPI(title="Marzban V1 Node Runtime", docs_url=None, redoc_url=None)
    state_lock = threading.RLock()
    state = {"session_id": None, "peer_ip": None}

    def status_payload(**extra):
        return {
            "connected": state["session_id"] is not None,
            "started": bool(core.started),
            "core_version": core.version,
            **extra,
        }

    def validate_session(session_id: UUID) -> None:
        with state_lock:
            if state["session_id"] != session_id:
                raise HTTPException(status_code=403, detail="Session ID mismatch.")

    def peer_ip() -> str:
        with state_lock:
            value = state["peer_ip"]
        if not value:
            raise HTTPException(status_code=409, detail="Node runtime is not connected")
        return str(value)

    @app.post("/v2/handshake")
    def handshake():
        return {
            "protocol": "marzban-node-v2",
            "protocol_version": 2,
            "runtime_version": settings.runtime_version,
            "capabilities": ["control_v1", "event_ack_v1", "client_ip_direct_v1"],
        }

    @app.post("/")
    def status():
        return status_payload()

    @app.post("/connect")
    def connect(request: Request):
        remote = request.client.host if request.client else None
        if not remote:
            raise HTTPException(status_code=400, detail="Unable to determine panel peer address")
        with state_lock:
            if state["session_id"] is not None and core.started:
                core.stop()
            state["session_id"] = uuid4()
            state["peer_ip"] = remote
            session_id = state["session_id"]
        return status_payload(session_id=session_id)

    @app.post("/ping")
    def ping(body: SessionBody):
        validate_session(body.session_id)
        return {}

    @app.post("/start")
    def start(body: ConfigBody):
        validate_session(body.session_id)
        try:
            core.start(body.config, peer_ip())
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return status_payload()

    @app.post("/stop")
    def stop(body: SessionBody):
        validate_session(body.session_id)
        core.stop()
        return status_payload()

    @app.post("/restart")
    def restart(body: ConfigBody):
        validate_session(body.session_id)
        try:
            core.restart(body.config, peer_ip())
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return status_payload()

    @app.post("/disconnect")
    def disconnect(body: SessionBody):
        validate_session(body.session_id)
        core.stop()
        with state_lock:
            state["session_id"] = None
            state["peer_ip"] = None
        return status_payload()

    @app.post("/v2/events")
    def events(body: EventsBody):
        validate_session(body.session_id)
        event_rows = spool.read(body.consumer_id, body.after_id, body.limit)
        return {"events": event_rows, **spool.stats()}

    @app.post("/v2/events/ack")
    def ack(body: AckBody):
        validate_session(body.session_id)
        try:
            acked = spool.ack(body.consumer_id, body.event_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"acked_event_id": acked}

    return app
''')

write_new("node_runtime/main.py", '''from __future__ import annotations

import logging
import ssl

import uvicorn

from node_runtime.certificates import ensure_server_certificate
from node_runtime.config import RuntimeSettings
from node_runtime.service import create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = RuntimeSettings.from_env()
    if not settings.ssl_client_cert_file.is_file():
        raise RuntimeError("SSL_CLIENT_CERT_FILE does not exist; strict mTLS is required")
    ensure_server_certificate(settings.ssl_cert_file, settings.ssl_key_file)
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        ssl_keyfile=str(settings.ssl_key_file),
        ssl_certfile=str(settings.ssl_cert_file),
        ssl_ca_certs=str(settings.ssl_client_cert_file),
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        access_log=False,
    )


if __name__ == "__main__":
    main()
''')

write_new("tests/test_v102_node_runtime.py", '''from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from node_runtime.config import RuntimeSettings
from node_runtime.core import prepare_xray_config
from node_runtime.events import EventSpool
from node_runtime.service import create_app
from app.device_limit.engine import DeviceLimitEngine
from app.xray.node import V2ReSTXRayNode


def _settings(tmp_path: Path, *, max_events: int = 1000) -> RuntimeSettings:
    return RuntimeSettings(
        service_host="127.0.0.1",
        service_port=62050,
        api_host="0.0.0.0",
        api_port=62051,
        xray_executable="/usr/local/bin/xray",
        xray_assets_path="/usr/local/share/xray",
        ssl_cert_file=tmp_path / "server.crt",
        ssl_key_file=tmp_path / "server.key",
        ssl_client_cert_file=tmp_path / "panel.crt",
        event_db_path=tmp_path / "events.sqlite3",
        runtime_version="v1.0.2",
        inbounds=(),
        max_events=max_events,
    )


def test_event_spool_persists_independent_consumer_offsets(tmp_path):
    path = tmp_path / "events.sqlite3"
    spool = EventSpool(path, max_events=1000)
    ids = [spool.append("xray.log", {"line": f"line-{index}"}) for index in range(1, 4)]
    assert ids == [1, 2, 3]
    assert [item["id"] for item in spool.read("device-limit")] == [1, 2, 3]
    assert spool.ack("device-limit", 2) == 2

    reopened = EventSpool(path, max_events=1000)
    assert [item["id"] for item in reopened.read("device-limit")] == [3]
    assert [item["id"] for item in reopened.read("panel-logs")] == [1, 2, 3]
    with pytest.raises(ValueError):
        reopened.ack("device-limit", 99)


def test_event_spool_is_bounded_without_blocking_new_events(tmp_path):
    spool = EventSpool(tmp_path / "bounded.sqlite3", max_events=1000)
    for index in range(1005):
        spool.append("xray.log", {"line": str(index)})
    stats = spool.stats()
    assert stats["event_count"] == 1000
    assert stats["dropped_events_total"] == 5
    assert stats["oldest_event_id"] == 6
    assert stats["latest_event_id"] == 1005


def test_prepare_xray_config_replaces_api_scope_with_current_panel_peer(tmp_path):
    settings = _settings(tmp_path)
    raw = '''{"api":{"tag":"OLD_API"},"inbounds":[{"tag":"API_INBOUND","protocol":"dokodemo-door"},{"tag":"public","protocol":"vless"}],"routing":{"rules":[{"outboundTag":"OLD_API"},{"outboundTag":"direct"}]},"log":{"logLevel":"none"}}'''
    prepared = prepare_xray_config(raw, "203.0.113.10", settings)
    assert prepared["inbounds"][0]["tag"] == "API_INBOUND"
    assert prepared["inbounds"][0]["port"] == 62051
    assert prepared["inbounds"][1]["tag"] == "public"
    assert prepared["routing"]["rules"][0]["source"] == ["127.0.0.1", "203.0.113.10"]
    assert all(rule.get("outboundTag") != "OLD_API" for rule in prepared["routing"]["rules"])
    assert prepared["log"]["logLevel"] == "warning"


class FakeCore:
    version = "26.7.28"

    def __init__(self):
        self.started = False
        self.calls = []

    def start(self, config, peer_ip):
        self.calls.append(("start", config, peer_ip))
        self.started = True

    def stop(self):
        self.calls.append(("stop",))
        self.started = False

    def restart(self, config, peer_ip):
        self.calls.append(("restart", config, peer_ip))
        self.started = True


def test_runtime_api_requires_session_and_persists_ack_cursor(tmp_path):
    settings = _settings(tmp_path)
    spool = EventSpool(settings.event_db_path, settings.max_events)
    core = FakeCore()
    client = TestClient(create_app(settings, spool=spool, core=core))
    handshake = client.post("/v2/handshake", json={})
    assert handshake.status_code == 200
    assert handshake.json()["protocol_version"] == 2
    assert "event_ack_v1" in handshake.json()["capabilities"]

    connected = client.post("/connect", json={})
    session_id = connected.json()["session_id"]
    assert client.post("/ping", json={"session_id": session_id}).status_code == 200
    assert client.post("/ping", json={"session_id": "00000000-0000-0000-0000-000000000000"}).status_code == 403

    first = spool.append("xray.log", {"line": "one"})
    second = spool.append("xray.log", {"line": "two"})
    response = client.post("/v2/events", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "after_id": 0,
        "limit": 100,
    })
    assert [item["id"] for item in response.json()["events"]] == [first, second]
    assert client.post("/v2/events/ack", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "event_id": second,
    }).status_code == 200
    replay = client.post("/v2/events", json={
        "session_id": session_id,
        "consumer_id": "device-limit",
        "after_id": 0,
        "limit": 100,
    })
    assert replay.json()["events"] == []


def test_v2_client_ack_happens_only_after_callback_success():
    node = object.__new__(V2ReSTXRayNode)
    node._session_id = "session"
    requests = []
    callback_lines = []

    def make_request(path, timeout, **params):
        requests.append((path, params.copy()))
        if path == "/v2/events":
            return {"events": [
                {"id": 1, "type": "xray.log", "payload": {"line": "one"}},
                {"id": 2, "type": "xray.log", "payload": {"line": "two"}},
            ]}
        return {"acked_event_id": params["event_id"]}

    node.make_request = make_request
    node.consume_events("device-limit", callback_lines.append, lambda: len(callback_lines) >= 2)
    assert callback_lines == ["one", "two"]
    assert requests[-1] == ("/v2/events/ack", {"consumer_id": "device-limit", "event_id": 2})

    node2 = object.__new__(V2ReSTXRayNode)
    node2._session_id = "session"
    requests2 = []
    node2.make_request = lambda path, timeout, **params: (
        requests2.append((path, params.copy())) or
        ({"events": [{"id": 1, "type": "xray.log", "payload": {"line": "boom"}}]} if path == "/v2/events" else {})
    )
    with pytest.raises(RuntimeError):
        node2.consume_events("device-limit", lambda _line: (_ for _ in ()).throw(RuntimeError("fail")), lambda: False)
    assert all(path != "/v2/events/ack" for path, _params in requests2)


def test_device_limit_collector_prefers_durable_v2_consumer(monkeypatch):
    from app import xray

    class Source:
        _session_id = "session"
        process = None
        runtime_handshake = SimpleNamespace(supports_direct_client_ip=True)

        def consume_events(self, consumer_id, callback, should_stop):
            assert consumer_id == "device-limit"
            assert should_stop() is False
            callback("2026/09/06 12:00:00 8.8.8.8:51000 accepted tcp:example.com:443 [vless >> direct] email: 42.demo.slot1")

    source = Source()
    monkeypatch.setattr(xray, "nodes", {7: source})
    tracker = DeviceLimitEngine()
    tracker.configure(True, "hybrid", True)
    tracker._limited_user_ids = {42}
    tracker._collect(source, "node:7")
    addresses, sources, slots = tracker.live_snapshot(42, 300, 1)
    assert addresses == {"8.8.8.8"}
    assert sources == {"node:7"}
    assert slots == {1: {"8.8.8.8"}}
    assert "node:7" not in tracker.diagnostics()["untrusted_ip_sources"]
''')
