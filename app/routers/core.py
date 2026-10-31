import asyncio
import json
import os
import tempfile
import threading
import time

import commentjson
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from starlette.websockets import WebSocketDisconnect

from app import xray
from app.db import Session, crud, get_db
from app.models.admin import Admin
from app.models.core import CoreStats
from app.utils import admin_hierarchy, responses
from app.utils.core_inbound_sync import (
    capture_network_state, restore_network_state, synchronize_inbounds,
)
from app.utils.audit import AuditLogService
from app.xray import XRayConfig
from config import XRAY_JSON, XRAY_LOCAL_CORE_ENABLED

router = APIRouter(tags=["Core"], prefix="/api", responses={401: responses._401})


@router.websocket("/core/logs")
async def core_logs(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token") or websocket.headers.get(
        "Authorization", ""
    ).removeprefix("Bearer ")
    admin = Admin.get_admin(token, db)
    if not admin:
        return await websocket.close(reason="Unauthorized", code=4401)

    dbadmin = crud.get_admin(db, admin.username)
    if admin.auth_method != "session" or dbadmin is None or not admin_hierarchy.is_owner(db, dbadmin):
        return await websocket.close(reason="You're not allowed", code=4403)

    if not XRAY_LOCAL_CORE_ENABLED:
        return await websocket.close(reason="Local core intentionally disabled: management-only Master", code=1000)

    interval = websocket.query_params.get("interval")
    if interval:
        try:
            interval = float(interval)
        except ValueError:
            return await websocket.close(reason="Invalid interval value", code=4400)
        if interval > 10:
            return await websocket.close(
                reason="Interval must be more than 0 and at most 10 seconds", code=4400
            )

    await websocket.accept()

    cache = ""
    last_sent_ts = 0
    with xray.core.get_logs() as logs:
        while True:
            if interval and time.time() - last_sent_ts >= interval and cache:
                try:
                    await websocket.send_text(cache)
                except (WebSocketDisconnect, RuntimeError):
                    break
                cache = ""
                last_sent_ts = time.time()

            if not logs:
                try:
                    await asyncio.wait_for(websocket.receive(), timeout=0.2)
                    continue
                except asyncio.TimeoutError:
                    continue
                except (WebSocketDisconnect, RuntimeError):
                    break

            log = logs.popleft()

            if interval:
                cache += f"{log}\n"
                continue

            try:
                await websocket.send_text(log)
            except (WebSocketDisconnect, RuntimeError):
                break


@router.get("/core", response_model=CoreStats)
def get_core_stats(admin: Admin = Depends(Admin.check_sudo_admin)):
    """Retrieve core statistics such as version and uptime."""
    return CoreStats(
        version=xray.core.version,
        started=xray.core.started,
        local_enabled=XRAY_LOCAL_CORE_ENABLED,
        logs_websocket=router.url_path_for("core_logs"),
    )


@router.post("/core/restart", responses={403: responses._403})
def restart_core(
    request: Request,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Restart the core and all connected nodes."""
    startup_config = xray.config.include_db_users()
    xray.core.restart(startup_config)

    for node_id, node in list(xray.nodes.items()):
        if node.connected:
            xray.operations.restart_node(node_id, startup_config)

    AuditLogService.log(
        db,
        admin,
        "core.restart",
        "core",
        f"Admin {admin.username} restarted the core and connected nodes",
        details={"connected_nodes": sum(node.connected for node in xray.nodes.values())},
        request=request,
    )
    return {}


@router.get("/core/config", responses={403: responses._403})
def get_core_config(admin: Admin = Depends(Admin.check_sudo_admin)) -> dict:
    """Get the current core configuration."""
    with open(XRAY_JSON, "r") as f:
        config = commentjson.loads(f.read())

    return config


_core_change_lock = threading.RLock()


def _atomic_core_file(payload: str) -> None:
    directory = os.path.dirname(os.path.abspath(XRAY_JSON))
    fd, temporary = tempfile.mkstemp(prefix=".xray-pending-", dir=directory)
    try:
        os.fchmod(fd, os.stat(XRAY_JSON).st_mode & 0o777)
        with os.fdopen(fd, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, XRAY_JSON)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _apply_core_update(
    payload: dict,
    db: Session,
    *,
    rename: tuple[str, str] | None = None,
) -> dict:
    """Reconcile the DB and file, with compensating recovery on runtime failure."""
    with _core_change_lock:
        with open(XRAY_JSON, "r") as stream:
            previous_file = stream.read()
        previous_config = xray.config
        try:
            inbound_rows = payload["inbounds"]
            raw_tags = [row["tag"] for row in inbound_rows]
            if len(raw_tags) != len(set(raw_tags)):
                raise ValueError("Inbound tags must be unique")
            config = XRayConfig(payload, api_port=previous_config.api_port)
            snapshot = capture_network_state(db)
            changed = synchronize_inbounds(
                db, previous_config.inbounds_by_tag, config.inbounds_by_tag,
                rename=rename,
            )
            # Commit and atomic file replacement are both reversible here.
            db.flush()
        except (ValueError, KeyError, TypeError) as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            db.rollback()
            raise

        committed = False
        file_written = False
        try:
            _atomic_core_file(json.dumps(payload, indent=4))
            file_written = True
            db.commit()
            committed = True
            xray.config = config
            startup_config = config.include_db_users()
            xray.core.restart(startup_config)
            if XRAY_LOCAL_CORE_ENABLED and not xray.core.started:
                raise RuntimeError("Xray core did not start with the updated configuration")
            xray.hosts.update()
        except Exception as exc:
            db.rollback()
            failures = []
            # Restore persisted network state before restarting old Xray.
            if committed:
                try:
                    restore_network_state(db, snapshot)
                    db.commit()
                except Exception as restore_error:
                    db.rollback()
                    failures.append(f"DB restore failed: {restore_error}")
            if file_written:
                try:
                    _atomic_core_file(previous_file)
                except Exception as restore_error:
                    failures.append(f"Config restore failed: {restore_error}")
            xray.config = previous_config
            if committed and not failures:
                try:
                    xray.core.restart(previous_config.include_db_users())
                    xray.hosts.update()
                except Exception as restore_error:
                    failures.append(f"Runtime restore failed: {restore_error}")
            if failures:
                raise HTTPException(
                    status_code=503,
                    detail="Core update failed; recovery requires attention: " + "; ".join(failures),
                ) from exc
            raise HTTPException(status_code=503, detail="Core update failed; previous state restored") from exc

        # Nodes run asynchronously in the existing runtime architecture and
        # reconnect using the persisted current configuration if unavailable.
        for node_id, node in list(xray.nodes.items()):
            if node.connected:
                xray.operations.restart_node(node_id, startup_config)
        return changed


@router.put("/core/config", responses={403: responses._403})
def modify_core_config(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
) -> dict:
    """Update raw JSON. Removed tags are pruned; never infer a rename."""
    _apply_core_update(payload, db)
    AuditLogService.log(
        db, admin, "settings.core_update", "core_config",
        f"Admin {admin.username} updated the core configuration",
        details={
            "top_level_sections": sorted(str(key) for key in payload),
            "configuration_values_stored": False,
        },
        request=request,
    )
    return payload


@router.post("/core/inbounds/rename", responses={403: responses._403})
def rename_core_inbound(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
) -> dict:
    """Explicit tag identity transition. Never guess rename from a raw JSON diff."""
    old_tag, new_tag = payload.get("old_tag"), payload.get("new_tag")
    if not all(isinstance(t, str) and t.strip() == t and 0 < len(t) <= 256
               and "," not in t for t in (old_tag, new_tag)):
        raise HTTPException(status_code=400, detail="Both inbound tags must be non-empty valid names")
    if old_tag == new_tag:
        raise HTTPException(status_code=400, detail="New tag must differ from old tag")
    with _core_change_lock:
        with open(XRAY_JSON, "r") as stream:
            source = commentjson.loads(stream.read())
        inbounds = source.get("inbounds", [])
        if not any(row.get("tag") == old_tag for row in inbounds):
            raise HTTPException(status_code=404, detail="Source inbound does not exist")
        if any(row.get("tag") == new_tag for row in inbounds):
            raise HTTPException(status_code=409, detail="Target inbound already exists")
        for row in inbounds:
            if row.get("tag") == old_tag:
                row["tag"] = new_tag
        # Routing rules that explicitly name the source inbound refer to the
        # same identity after rename. Other inbounds and all ports are untouched.
        for rule in source.get("routing", {}).get("rules", []):
            if isinstance(rule.get("inboundTag"), list):
                rule["inboundTag"] = [
                    new_tag if tag == old_tag else tag for tag in rule["inboundTag"]
                ]
        result = _apply_core_update(source, db, rename=(old_tag, new_tag))
    AuditLogService.log(
        db, admin, "settings.core_inbound_rename", "core_config",
        f"Admin {admin.username} renamed a core inbound",
        details={"old_tag": old_tag, "new_tag": new_tag},
        request=request,
    )
    return result
