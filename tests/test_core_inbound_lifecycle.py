"""Regressions for core tag identity, independent additions and fail-closed groups."""
import pytest

from app import xray
from app.db.models import (
    AccessGroupHost, AccessGroupInbound, MarzhelpAdminInboundPermission,
    ProxyHost, ProxyInbound, User,
)
from app.models.admin_hierarchy import AccessGroupInput, PlanCreate, PlanVersionInput
from app.models.user import UserStatus
from app.utils import access_groups, admin_plans
from app.utils.core_inbound_sync import (
    capture_network_state, restore_network_state, synchronize_inbounds,
)
from test_stage4_plan_network_scope import db, _configure_network


def _new_inbound(session, tag, protocol="vless"):
    row = ProxyInbound(tag=tag)
    session.add(row)
    session.flush()
    host = ProxyHost(inbound=row, remark=f"host-{tag}", address=f"{tag.lower().replace(' ', '-')}.test")
    session.add(host)
    session.commit()
    return host, {"tag": tag, "protocol": protocol, "port": 8443, "network": "tcp", "tls": "none"}


def _users(session, owner, group):
    plan = admin_plans.create_plan(
        session, owner, PlanCreate(
            name="commercial-remains-unchanged",
            version=PlanVersionInput(data_limit=123456789, duration_days=30),
        ),
    )
    users = []
    for index, status in enumerate(
        (UserStatus.active, UserStatus.on_hold, UserStatus.disabled, UserStatus.expired)
    ):
        user, _, _ = admin_plans.create_user_from_plan(
            session, actor=owner, plan_id=plan.id, access_group_id=group.id,
            username=f"core-sync-{index}", status="active", note=None,
            idempotency_key=f"core-sync-{index}-create",
        )
        user.status = status
        users.append(user)
    session.commit()
    return users, plan


def _state(users):
    return [
        (
            user.id, user.status, user.data_limit, user.expire,
            tuple(sorted((str(proxy.type), repr(proxy.settings)) for proxy in user.proxies)),
        )
        for user in users
    ]


def _config(monkeypatch, inbounds):
    monkeypatch.setattr(xray.config, "inbounds_by_tag", inbounds)
    by_protocol = {}
    for item in inbounds.values():
        by_protocol.setdefault(item["protocol"], []).append(item)
    monkeypatch.setattr(xray.config, "inbounds_by_protocol", by_protocol)


def test_delete_prunes_only_removed_tag_and_preserves_users_and_commerce(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    retained_host, retained = _new_inbound(session, "UNCHANGED VLESS")
    before = dict(xray.config.inbounds_by_tag)
    before[retained["tag"]] = retained
    _config(monkeypatch, before)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="retain-other-inbound", inbounds=list(before),
        hosts={old: [host.id], retained["tag"]: [retained_host.id]},
    ))
    users, plan = _users(session, owner, group)
    snapshot = _state(users)

    after = {retained["tag"]: retained}
    result = synchronize_inbounds(session, before, after)
    session.commit()
    _config(monkeypatch, after)

    assert result["removed_tags"] == [old]
    assert access_groups._scope(session, group.id)[0] == {retained["tag"]}
    assert access_groups._scope(session, group.id)[1] == {retained["tag"]: {retained_host.id}}
    assert all(access_groups.user_inbound_scope(u) == {retained["tag"]} for u in users)
    assert all(admin_plans.subscription_host_scope(session, u) == {
        retained["tag"]: {retained_host.id}
    } for u in users)
    assert session.get(ProxyHost, host.id).is_legacy is True
    assert _state(users) == snapshot
    assert plan.current_version.data_limit == 123456789


def test_explicit_rename_moves_host_id_group_admin_permission_and_credentials(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    before = dict(xray.config.inbounds_by_tag)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="rename-group", inbounds=[old], hosts={old: [host.id]},
    ))
    users, _ = _users(session, owner, group)
    snapshot = _state(users)
    session.add(MarzhelpAdminInboundPermission(admin_id=owner.id, inbound_tag=old))
    session.commit()
    renamed = "RENAMED VLESS"
    after = {renamed: {**before[old], "tag": renamed}}
    result = synchronize_inbounds(session, before, after, rename=(old, renamed))
    session.commit()
    _config(monkeypatch, after)

    assert result["renamed"] == [old, renamed]
    assert access_groups._scope(session, group.id)[0] == {renamed}
    assert access_groups._scope(session, group.id)[1] == {renamed: {host.id}}
    assert session.get(ProxyHost, host.id).inbound_tag == renamed
    assert session.query(MarzhelpAdminInboundPermission).filter_by(inbound_tag=renamed).count() == 1
    assert all(access_groups.user_inbound_scope(user) == {renamed} for user in users)
    assert all(admin_plans.subscription_host_scope(session, user) == {renamed: {host.id}} for user in users)
    assert _state(users) == snapshot


def test_independent_addition_never_expands_group_even_on_main_core(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    before = dict(xray.config.inbounds_by_tag)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="no-auto-grant", inbounds=[old], hosts={old: [host.id]},
    ))
    users, _ = _users(session, owner, group)
    new_tag = "INDEPENDENT VLESS"
    after = {**before, new_tag: {**before[old], "tag": new_tag, "port": 5555}}
    synchronize_inbounds(session, before, after)
    session.commit()
    _config(monkeypatch, after)

    assert access_groups._scope(session, group.id)[0] == {old}
    assert all(access_groups.user_inbound_scope(user) == {old} for user in users)
    assert all(
        new_tag in {inbound.tag for proxy in user.proxies for inbound in proxy.excluded_inbounds}
        for user in users
    )
    assert session.query(AccessGroupInbound).filter_by(inbound_tag=new_tag).count() == 0
    assert session.query(AccessGroupHost).filter_by(inbound_tag=new_tag).count() == 0


def test_last_inbound_removal_retains_group_and_denies_all_without_account_changes(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    before = dict(xray.config.inbounds_by_tag)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="empty-deny-all", inbounds=[old], hosts={old: [host.id]},
    ))
    users, _ = _users(session, owner, group)
    snapshot = _state(users)
    result = synchronize_inbounds(session, before, {})
    session.commit()
    _config(monkeypatch, {})

    assert group.id in result["groups_without_network"]
    assert access_groups.response(session, group).network_status == "NO_NETWORK_ACCESS"
    assert access_groups._scope(session, group.id)[0] == set()
    assert all(access_groups.user_inbound_scope(user) == set() for user in users)
    assert all(admin_plans.subscription_host_scope(session, user) == {} for user in users)
    assert session.query(User).filter_by(access_group_id=group.id).count() == 4
    assert _state(users) == snapshot


def test_invalid_rename_cannot_infer_or_merge_an_independent_tag(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    other, _ = _new_inbound(session, "DESTINATION VLESS")
    before = dict(xray.config.inbounds_by_tag)
    after = {"DESTINATION VLESS": {**before[old], "tag": "DESTINATION VLESS"}}
    with pytest.raises(ValueError, match="Destination inbound identity already exists"):
        synchronize_inbounds(session, before, after, rename=(old, "DESTINATION VLESS"))
    session.rollback()
    assert session.get(ProxyHost, host.id).inbound_tag == old


def test_snapshot_restores_previous_network_metadata_after_restart_failure(db, monkeypatch):
    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    before = dict(xray.config.inbounds_by_tag)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="rollback-group", inbounds=[old], hosts={old: [host.id]},
    ))
    users, _ = _users(session, owner, group)
    snapshot = capture_network_state(session)
    after = {"RENAMED": {**before[old], "tag": "RENAMED"}}
    synchronize_inbounds(session, before, after, rename=(old, "RENAMED"))
    session.commit()
    restore_network_state(session, snapshot)
    session.commit()
    _config(monkeypatch, before)
    assert access_groups._scope(session, group.id)[0] == {old}
    assert session.get(ProxyHost, host.id).inbound_tag == old
    assert all(access_groups.user_inbound_scope(user) == {old} for user in users)


def test_core_update_restores_db_and_file_after_runtime_restart_error(
    db, monkeypatch, tmp_path,
):
    import json
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.routers import core

    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="failed-runtime-group", inbounds=[old], hosts={old: [host.id]},
    ))
    _users(session, owner, group)
    original = {
        "inbounds": [{"tag": old, "protocol": "vless", "port": 443}],
        "outbounds": [{"tag": "DIRECT", "protocol": "freedom"}],
    }
    path = tmp_path / "xray.json"
    path.write_text(json.dumps(original))

    class FakeConfig:
        def __init__(self, data, api_port=65000):
            self.api_port = api_port
            self.inbounds_by_tag = {item["tag"]: item for item in data["inbounds"]}

        def include_db_users(self):
            return self

    previous = FakeConfig(original)
    monkeypatch.setattr(core, "XRAY_JSON", str(path))
    monkeypatch.setattr(core, "XRayConfig", FakeConfig)
    monkeypatch.setattr(core.xray, "config", previous)
    count = []
    def restart(_config):
        count.append(1)
        if len(count) == 1:
            raise RuntimeError("simulated Xray rejection")
    monkeypatch.setattr(core.xray, "core", SimpleNamespace(restart=restart, started=True))
    monkeypatch.setattr(core.xray, "hosts", SimpleNamespace(update=lambda: None))
    monkeypatch.setattr(core.xray, "nodes", {})

    updated = {
        "inbounds": [{"tag": "RENAMED", "protocol": "vless", "port": 443}],
        "outbounds": original["outbounds"],
    }
    with pytest.raises(HTTPException) as error:
        core._apply_core_update(updated, session, rename=(old, "RENAMED"))
    assert error.value.status_code == 503
    assert len(count) == 2
    assert json.loads(path.read_text()) == original
    assert core.xray.config is previous
    session.expire_all()
    assert access_groups._scope(session, group.id)[0] == {old}
    assert session.get(ProxyHost, host.id).inbound_tag == old


def test_core_update_success_restarts_connected_nodes_and_prunes_only_deleted_tag(
    db, monkeypatch, tmp_path,
):
    import json
    from types import SimpleNamespace
    from app.routers import core

    session, owner = db
    old, host, _ = _configure_network(session, monkeypatch)
    kept_host, kept = _new_inbound(session, "KEEP VLESS")
    before = dict(xray.config.inbounds_by_tag)
    before[kept["tag"]] = kept
    _config(monkeypatch, before)
    group = access_groups.create(session, owner, AccessGroupInput(
        name="live-transition", inbounds=list(before),
        hosts={old: [host.id], kept["tag"]: [kept_host.id]},
    ))
    _users(session, owner, group)
    original = {
        "inbounds": [{"tag": tag, "protocol": "vless", "port": 443} for tag in before],
        "outbounds": [{"tag": "DIRECT", "protocol": "freedom"}],
    }
    path = tmp_path / "xray.json"
    path.write_text(json.dumps(original))

    class FakeConfig:
        def __init__(self, data, api_port=65000):
            self.api_port = api_port
            self.inbounds_by_tag = {item["tag"]: item for item in data["inbounds"]}
        def include_db_users(self):
            return self

    previous = FakeConfig(original)
    monkeypatch.setattr(core, "XRAY_JSON", str(path))
    monkeypatch.setattr(core, "XRayConfig", FakeConfig)
    monkeypatch.setattr(core.xray, "config", previous)
    restarted = []
    monkeypatch.setattr(core.xray, "core", SimpleNamespace(
        restart=lambda config: restarted.append("main"), started=True
    ))
    monkeypatch.setattr(core.xray, "hosts", SimpleNamespace(update=lambda: None))
    monkeypatch.setattr(core.xray, "nodes", {
        7: SimpleNamespace(connected=True), 8: SimpleNamespace(connected=False),
    })
    monkeypatch.setattr(core.xray.operations, "restart_node", lambda node_id, config: restarted.append(node_id))
    updated = {"inbounds": [original["inbounds"][1]], "outbounds": original["outbounds"]}
    core._apply_core_update(updated, session)
    assert restarted == ["main", 7]
    assert access_groups._scope(session, group.id)[0] == {kept["tag"]}
    assert len(json.loads(path.read_text())["inbounds"]) == 1
