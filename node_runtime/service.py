from __future__ import annotations

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
            "event_stream_id": spool.stream_id,
            "capabilities": [
                "control_v1",
                "event_ack_v1",
                "client_ip_direct_v1",
                "structured_events_v1",
            ],
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
        try:
            spool.append(
                "runtime.session.connected",
                {"severity": "info", "reason_code": "panel_connected"},
            )
        except Exception:
            pass
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
        try:
            spool.append(
                "runtime.session.disconnected",
                {"severity": "info", "reason_code": "panel_disconnected"},
            )
        except Exception:
            pass
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
