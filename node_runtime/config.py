from __future__ import annotations

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
