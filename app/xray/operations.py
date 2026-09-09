from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.exc import SQLAlchemyError

from app import logger, xray
from app.db import GetDB, crud
from app.db.node_operations import create_node_event
from app.models.node import NodeStatus
from app.models.user import UserResponse
from app.device_limit.slots import enabled_device_slots, slot_email
from app.utils.concurrency import threaded_function
from app.xray.node import XRayNode
from xray_api import XRay as XRayAPI
from xray_api.types.account import Account, XTLSFlows

if TYPE_CHECKING:
    from app.db import User as DBUser
    from app.db.models import Node as DBNode


@lru_cache(maxsize=None)
def get_tls():
    from app.db import GetDB, get_tls_certificate
    with GetDB() as db:
        tls = get_tls_certificate(db)
        return {
            "key": tls.key,
            "certificate": tls.certificate
        }


@threaded_function
def _add_user_to_inbound(api: XRayAPI, inbound_tag: str, account: Account):
    try:
        api.add_inbound_user(tag=inbound_tag, user=account, timeout=30)
    except (xray.exc.EmailExistsError, xray.exc.ConnectionError):
        pass


@threaded_function
def _remove_user_from_inbound(api: XRayAPI, inbound_tag: str, email: str):
    try:
        api.remove_inbound_user(tag=inbound_tag, email=email, timeout=30)
    except (xray.exc.EmailNotFoundError, xray.exc.ConnectionError):
        pass


@threaded_function
def _replace_inbound_users(
    api: XRayAPI,
    inbound_tag: str,
    emails: tuple[str, ...],
    accounts: tuple[Account, ...],
):
    """Replace all slot accounts in one ordered HandlerService operation."""

    for email in emails:
        try:
            api.remove_inbound_user(tag=inbound_tag, email=email, timeout=30)
        except (xray.exc.EmailNotFoundError, xray.exc.ConnectionError):
            pass
    for account in accounts:
        try:
            api.add_inbound_user(tag=inbound_tag, user=account, timeout=30)
        except (xray.exc.EmailExistsError, xray.exc.ConnectionError):
            pass


def add_user(dbuser: "DBUser"):
    from app.utils.access_groups import user_node_scope
    node_scope = user_node_scope(dbuser)
    user = UserResponse.model_validate(dbuser)

    slots = enabled_device_slots(dbuser)
    credential_sets = (
        [(slot.slot_index, slot.credentials) for slot in slots]
        if slots
        else [(1, {key.value: value.dict(no_obj=True) for key, value in user.proxies.items()})]
    )

    for proxy_type, inbound_tags in user.inbounds.items():
        for inbound_tag in inbound_tags:
            inbound = xray.config.inbounds_by_tag.get(inbound_tag, {})
            for slot_index, credentials in credential_sets:
                proxy_settings = credentials.get(proxy_type.value)
                if not proxy_settings:
                    continue
                account = proxy_type.account_model(
                    email=slot_email(dbuser.id, dbuser.username, slot_index),
                    **proxy_settings,
                )

                # XTLS currently only supports transmission methods of TCP and mKCP
                if getattr(account, 'flow', None) and (
                    inbound.get('network', 'tcp') not in ('tcp', 'kcp')
                    or
                    (
                        inbound.get('network', 'tcp') in ('tcp', 'kcp')
                        and
                        inbound.get('tls') not in ('tls', 'reality')
                    )
                    or
                    inbound.get('header_type') == 'http'
                ):
                    account.flow = XTLSFlows.NONE

                if node_scope is None:
                    _add_user_to_inbound(xray.api, inbound_tag, account)  # main core
                for node_id, node in list(xray.nodes.items()):
                    if (node_scope is None or node_id in node_scope) and node.connected and node.started:
                        _add_user_to_inbound(node.api, inbound_tag, account)


def add_user_by_id(user_id: int):
    """Load committed relationships in a fresh session before background sync.

    Passing request-scoped ORM objects to a FastAPI background task can leave
    proxies, slots or ownership detached and previously produced incomplete
    delegated-admin accounts/EOF failures.
    """

    with GetDB() as db:
        dbuser = crud.get_user_by_id(db, user_id)
        if dbuser is not None:
            add_user(dbuser)


def remove_user(dbuser: "DBUser"):
    emails = {f"{dbuser.id}.{dbuser.username}"}
    emails.update(
        slot_email(dbuser.id, dbuser.username, slot.slot_index)
        for slot in dbuser.device_slots
    )

    for inbound_tag in xray.config.inbounds_by_tag:
        for email in emails:
            _remove_user_from_inbound(xray.api, inbound_tag, email)
            for node in list(xray.nodes.values()):
                if node.connected and node.started:
                    _remove_user_from_inbound(node.api, inbound_tag, email)


def remove_user_by_id(user_id: int):
    """Load the user in a fresh session before background removal."""

    with GetDB() as db:
        dbuser = crud.get_user_by_id(db, user_id)
        if dbuser is not None:
            remove_user(dbuser)


def restart_all_cores(config=None):
    """Reload all running cores, terminating already-established streams."""

    if config is None:
        config = xray.config.include_db_users()

    if xray.core.started:
        xray.core.restart(config)

    for node_id, node in list(xray.nodes.items()):
        if node.connected:
            restart_node(node_id, config)


def update_user(dbuser: "DBUser"):
    """Atomically replace a user's slot accounts without restarting Xray."""

    from app.utils.access_groups import user_node_scope
    node_scope = user_node_scope(dbuser)
    user = UserResponse.model_validate(dbuser)
    all_emails = tuple({
        f"{dbuser.id}.{dbuser.username}",
        *(
            slot_email(dbuser.id, dbuser.username, slot.slot_index)
            for slot in dbuser.device_slots
        ),
    })
    slots = enabled_device_slots(dbuser)
    credential_sets = (
        [(slot.slot_index, slot.credentials) for slot in slots]
        if slots
        else [(1, {key.value: value.dict(no_obj=True) for key, value in user.proxies.items()})]
    )

    accounts_by_inbound: dict[str, list[Account]] = {
        inbound_tag: [] for inbound_tag in xray.config.inbounds_by_tag
    }
    for proxy_type, inbound_tags in user.inbounds.items():
        for inbound_tag in inbound_tags:
            inbound = xray.config.inbounds_by_tag.get(inbound_tag, {})
            for slot_index, credentials in credential_sets:
                proxy_settings = credentials.get(proxy_type.value)
                if not proxy_settings:
                    continue
                account = proxy_type.account_model(
                    email=slot_email(dbuser.id, dbuser.username, slot_index),
                    **proxy_settings,
                )
                if getattr(account, "flow", None) and (
                    inbound.get("network", "tcp") not in ("tcp", "kcp")
                    or inbound.get("tls") not in ("tls", "reality")
                    or inbound.get("header_type") == "http"
                ):
                    account.flow = XTLSFlows.NONE
                accounts_by_inbound.setdefault(inbound_tag, []).append(account)

    for inbound_tag, accounts in accounts_by_inbound.items():
        account_tuple = tuple(accounts)
        _replace_inbound_users(xray.api, inbound_tag, all_emails, account_tuple if node_scope is None else ())
        for node_id, node in list(xray.nodes.items()):
            if node.connected and node.started:
                _replace_inbound_users(node.api, inbound_tag, all_emails,
                                       account_tuple if node_scope is None or node_id in node_scope else ())


def update_user_by_id(user_id: int):
    with GetDB() as db:
        dbuser = crud.get_user_by_id(db, user_id)
        if dbuser is not None:
            update_user(dbuser)


global _connecting_nodes, _outage_started_at
_connecting_nodes = {}
_outage_started_at = {}


def _status_value(status) -> str | None:
    return getattr(status, "value", status) if status is not None else None


def _record_connection_event(
    node_id: int,
    event_type: str,
    *,
    occurred_at: datetime,
    severity: str = "info",
    reason_code: str | None = None,
    trigger_reason: str | None = None,
    root_cause: str | None = None,
    message: str | None = None,
    previous_state: str | None = None,
    new_state: str | None = None,
    reconnect_mode: str | None = None,
    reconnect_attempt: int | None = None,
    reconnect_result: str | None = None,
    downtime_seconds: int | None = None,
    metadata=None,
) -> None:
    """Best-effort connection telemetry; never blocks the reconnect engine."""

    try:
        with GetDB() as db:
            create_node_event(
                db,
                node_id=node_id,
                event_type=event_type,
                source="master",
                occurred_at=occurred_at,
                severity=severity,
                reason_code=reason_code,
                trigger_reason=trigger_reason,
                root_cause=root_cause,
                message=message,
                previous_state=previous_state,
                new_state=new_state,
                reconnect_mode=reconnect_mode,
                reconnect_attempt=reconnect_attempt,
                reconnect_result=reconnect_result,
                downtime_seconds=downtime_seconds,
                metadata=metadata,
            )
            db.commit()
    except Exception as exc:
        logger.warning("Unable to persist node %s connection event: %s", node_id, exc)


def remove_node(node_id: int, *, forget_outage: bool = True):
    if node_id in xray.nodes:
        try:
            xray.nodes[node_id].disconnect()
        except Exception:
            pass
        finally:
            try:
                del xray.nodes[node_id]
            except KeyError:
                pass
    if forget_outage:
        _outage_started_at.pop(node_id, None)


def add_node(dbnode: "DBNode"):
    # Replacing the transport object during a retry must not reset outage age.
    remove_node(dbnode.id, forget_outage=False)

    tls = get_tls()
    xray.nodes[dbnode.id] = XRayNode(address=dbnode.address,
                                     port=dbnode.port,
                                     api_port=dbnode.api_port,
                                     ssl_key=tls['key'],
                                     ssl_cert=tls['certificate'],
                                     usage_coefficient=dbnode.usage_coefficient)
    xray.nodes[dbnode.id].node_id = dbnode.id

    return xray.nodes[dbnode.id]


def _change_node_status(node_id: int, status: NodeStatus, message: str = None, version: str = None):
    with GetDB() as db:
        try:
            dbnode = crud.get_node_by_id(db, node_id)
            if not dbnode:
                return

            if dbnode.status == NodeStatus.disabled:
                remove_node(dbnode.id)
                return

            crud.update_node_status(db, dbnode, status, message, version)
        except SQLAlchemyError:
            db.rollback()


@threaded_function
def connect_node(
    node_id,
    config=None,
    reconnect_mode: str = "system",
    trigger_reason: str | None = None,
    reconnect_attempt: int | None = None,
):
    global _connecting_nodes, _outage_started_at

    if _connecting_nodes.get(node_id):
        return

    with GetDB() as db:
        dbnode = crud.get_node_by_id(db, node_id)
        if dbnode:
            previous_status = dbnode.status
            previous_status_change = dbnode.last_status_change
        else:
            previous_status = None
            previous_status_change = None

    if not dbnode:
        return

    try:
        node = xray.nodes[dbnode.id]
        assert node.connected
    except (KeyError, AssertionError):
        node = xray.operations.add_node(dbnode)

    attempt_started_at = datetime.utcnow()
    if node_id not in _outage_started_at:
        if previous_status == NodeStatus.connected:
            _outage_started_at[node_id] = attempt_started_at
        else:
            _outage_started_at[node_id] = previous_status_change or attempt_started_at
    attempt_number = max(1, int(reconnect_attempt or 1))

    try:
        _connecting_nodes[node_id] = True
        _record_connection_event(
            node_id,
            "node.connection.attempt",
            occurred_at=attempt_started_at,
            severity="warning" if previous_status not in (None, NodeStatus.connected) else "info",
            reason_code="reconnect_attempt",
            trigger_reason=trigger_reason or "system",
            previous_state=_status_value(previous_status),
            new_state=NodeStatus.connecting.value,
            reconnect_mode=reconnect_mode,
            reconnect_attempt=attempt_number,
            reconnect_result="started",
        )

        _change_node_status(node_id, NodeStatus.connecting)
        logger.info(f"Connecting to \"{dbnode.name}\" node")

        if config is None:
            config = xray.config.include_db_users()

        node.start(config)
        version = node.get_version()
        _change_node_status(node_id, NodeStatus.connected, version=version)
        finished_at = datetime.utcnow()
        outage_started = _outage_started_at.pop(node_id, attempt_started_at)
        downtime = max(0, int((finished_at - outage_started).total_seconds()))
        _record_connection_event(
            node_id,
            "node.connection.succeeded",
            occurred_at=finished_at,
            reason_code="connected",
            trigger_reason=trigger_reason or "system",
            previous_state=NodeStatus.connecting.value,
            new_state=NodeStatus.connected.value,
            reconnect_mode=reconnect_mode,
            reconnect_attempt=attempt_number,
            reconnect_result="success",
            downtime_seconds=downtime,
            metadata={"xray_version": version},
        )
        logger.info(f"Connected to \"{dbnode.name}\" node, xray run on v{version}")

    except Exception as e:
        failed_at = datetime.utcnow()
        outage_started = _outage_started_at.get(node_id, attempt_started_at)
        downtime = max(0, int((failed_at - outage_started).total_seconds()))
        _change_node_status(node_id, NodeStatus.error, message=str(e))
        _record_connection_event(
            node_id,
            "node.connection.failed",
            occurred_at=failed_at,
            severity="error",
            reason_code="connection_failed",
            trigger_reason=trigger_reason or "system",
            root_cause=type(e).__name__,
            message=str(e),
            previous_state=NodeStatus.connecting.value,
            new_state=NodeStatus.error.value,
            reconnect_mode=reconnect_mode,
            reconnect_attempt=attempt_number,
            reconnect_result="failure",
            downtime_seconds=downtime,
        )
        logger.info(f"Unable to connect to \"{dbnode.name}\" node")

    finally:
        try:
            del _connecting_nodes[node_id]
        except KeyError:
            pass


@threaded_function
def restart_node(node_id, config=None):
    with GetDB() as db:
        dbnode = crud.get_node_by_id(db, node_id)

    if not dbnode:
        return

    try:
        node = xray.nodes[dbnode.id]
    except KeyError:
        node = xray.operations.add_node(dbnode)

    if not node.connected:
        return connect_node(
            node_id,
            config,
            reconnect_mode="system",
            trigger_reason="core_restart_fallback",
        )

    try:
        logger.info(f"Restarting Xray core of \"{dbnode.name}\" node")

        if config is None:
            config = xray.config.include_db_users()

        node.restart(config)
        logger.info(f"Xray core of \"{dbnode.name}\" node restarted")
    except Exception as e:
        _change_node_status(node_id, NodeStatus.error, message=str(e))
        logger.info(f"Unable to restart node {node_id}")
        try:
            node.disconnect()
        except Exception:
            pass


__all__ = [
    "add_user",
    "remove_user",
    "remove_user_by_id",
    "restart_all_cores",
    "add_node",
    "remove_node",
    "connect_node",
    "restart_node",
]
