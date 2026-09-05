from collections import defaultdict

import pytest
import sqlalchemy as sa
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app import xray
from app.db.base import Base
from app.db.models import (
    Admin,
    AdminAccountStatus,
    AdminHierarchySettings,
    AdminRole,
    AdminSuspensionReason,
    AdminUserCreationMode,
    AdminUserPlan,
    AdminUserPlanHost,
    AdminUserPlanInbound,
    AdminUserPlanVersion,
    MarzhelpAdminSettings,
    ProxyHost,
    ProxyInbound,
    User,
    UserPlanAssignment,
)
from app.models.admin_hierarchy import AccessGroupInput, PlanCreate, PlanUpdate, PlanVersionInput
from app.models.proxy import ProxySettings, ProxyTypes
from app.models import user as user_models
from app.models.user import UserResponse
from app.subscription import share
from app.utils import access_groups, admin_hierarchy, admin_plans


@pytest.fixture()
def db():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all(
        [
            AdminRole(id=1, code="OWNER"),
            AdminRole(id=2, code="SUPER_ADMIN"),
            AdminRole(id=3, code="ADMIN"),
            AdminUserCreationMode(id=1, code="FREE_FORM"),
            AdminUserCreationMode(id=2, code="PLAN_ONLY"),
            AdminAccountStatus(id=1, code="ACTIVE"),
            AdminAccountStatus(id=2, code="SUSPENDED"),
            AdminAccountStatus(id=3, code="DISABLED"),
            AdminSuspensionReason(id=1, code="MANUAL"),
            AdminSuspensionReason(id=2, code="CREDIT_EXHAUSTED"),
            AdminSuspensionReason(id=3, code="ACCOUNT_EXPIRED"),
            AdminHierarchySettings(id=1, enabled=False, max_depth=64),
        ]
    )
    owner = Admin(username="owner", hashed_password="x", is_sudo=True)
    session.add(owner)
    session.flush()
    session.add(
        MarzhelpAdminSettings(
            admin_id=owner.id,
            total_traffic=None,
            calculate_volume="used_traffic",
        )
    )
    session.commit()
    admin_hierarchy.set_owner(session, owner.username)
    session.refresh(owner)
    try:
        yield session, owner
    finally:
        session.close()


def _configure_network(db, monkeypatch):
    tag = "VLESS TCP"
    inbound_config = {
        "tag": tag,
        "protocol": "vless",
        "network": "tcp",
        "tls": "none",
        "port": 443,
        "sni": [],
        "host": [],
        "path": "",
        "header_type": "none",
    }
    monkeypatch.setattr(xray.config, "inbounds_by_tag", {tag: inbound_config})
    monkeypatch.setattr(xray.config, "inbounds_by_protocol", {"vless": [inbound_config]})
    inbound = ProxyInbound(tag=tag)
    db.add(inbound)
    db.flush()
    first = ProxyHost(remark="selected {USERNAME}", address="one.example", inbound=inbound)
    second = ProxyHost(remark="not-selected {USERNAME}", address="two.example", inbound=inbound)
    db.add_all([first, second])
    db.commit()
    return tag, first, second


def _version(tag: str, host_id: int) -> PlanVersionInput:
    return PlanVersionInput(
        data_limit=1024,
        duration_days=30,
        concurrent_user_limit=1,
    )


def _runtime_host(host_id: int, remark: str, address: str) -> dict:
    return {
        "_id": host_id,
        "remark": remark,
        "address": [address],
        "port": 443,
        "path": None,
        "sni": [],
        "host": [],
        "alpn": "",
        "fingerprint": "",
        "tls": None,
        "allowinsecure": False,
        "mux_enable": False,
        "fragment_setting": None,
        "noise_setting": None,
        "random_user_agent": False,
        "use_sni_as_host": False,
    }


class _CaptureConfiguration:
    def __init__(self):
        self.remarks = []

    def add(self, *, remark, address, inbound, settings):
        self.remarks.append((remark, address))

    def render(self, reverse=False):
        return self.remarks


def test_plan_request_contract_rejects_network_fields():
    commercial = PlanVersionInput(data_limit=1, duration_days=1)
    assert commercial.model_dump() == {
        "price_toman": 0,
        "data_limit": 1,
        "duration_days": 1,
        "concurrent_user_limit": None,
        "reset_strategy": "no_reset",
        "renewal_volume_strategy": "replace",
        "renewal_time_strategy": "extend_max",
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanVersionInput(
            data_limit=1,
            duration_days=1,
            inbounds=["VLESS TCP"],
            hosts={"VLESS TCP": [1]},
        )


def test_commercial_plan_and_access_group_are_independent(db, monkeypatch):
    session, owner = db
    tag, first, second = _configure_network(session, monkeypatch)
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(
            name="commercial-only",
            version=PlanVersionInput(data_limit=30 * 1024**3, duration_days=30, price_toman=33_000),
        ),
    )
    group = access_groups.create(
        session,
        owner,
        AccessGroupInput(name="primary access", inbounds=[tag], hosts={tag: [first.id]}),
    )
    user, _, created = admin_plans.create_user_from_plan(
        session,
        actor=owner,
        plan_id=plan.id,
        access_group_id=group.id,
        username="separate-access-user",
        status="active",
        note=None,
        idempotency_key="separate-access-create",
    )
    assert created is True
    assert user.access_group_id == group.id
    assert admin_plans.subscription_host_scope(session, user) == {tag: {first.id}}

    synced = access_groups.update(
        session,
        owner,
        group,
        AccessGroupInput(name="primary access", inbounds=[tag], hosts={tag: [second.id]}),
    )
    assert synced == [user.id]
    assert admin_plans.subscription_host_scope(session, user) == {tag: {second.id}}
    assert admin_plans.subscription_host_scopes(session, [user]) == {user.id: {tag: {second.id}}}
    assert admin_plans.plan_response(session, plan).version.inbounds == []
    user.status = user_models.UserStatus.disabled
    session.commit()
    access_groups.archive(session, owner, group)
    with pytest.raises(admin_hierarchy.HierarchyError, match="Access Group is unavailable"):
        admin_plans.renew_user_from_plan(session, actor=owner, user=user, plan_id=plan.id,
                                       idempotency_key="archived-access-renew")


def test_plan_user_creation_requires_access_group_before_trial_mutation(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    settings = session.get(MarzhelpAdminSettings, owner.id)
    settings.trial_quota = 2
    session.commit()
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(
            name="trial-requires-access",
            is_trial=True,
            version=_version(tag, first.id),
        ),
    )

    with pytest.raises(admin_hierarchy.HierarchyError) as exc:
        admin_plans.create_user_from_plan(
            session,
            actor=owner,
            plan_id=plan.id,
            username="missing-access-user",
            status="active",
            note=None,
            idempotency_key="missing-access-create",
        )

    assert exc.value.code == "access_group_required"
    session.expire(settings)
    assert settings.trial_quota == 2
    assert settings.trials_used == 0
    assert session.query(User).filter_by(username="missing-access-user").count() == 0
    assert session.query(UserPlanAssignment).count() == 0


def test_plan_renewal_preserves_access_group_topology_by_default(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(name="renew-commercial", version=_version(tag, first.id)),
    )
    group = access_groups.create(
        session,
        owner,
        AccessGroupInput(name="renew-access", inbounds=[tag], hosts={tag: [first.id]}),
    )
    user, _, _ = admin_plans.create_user_from_plan(
        session,
        actor=owner,
        plan_id=plan.id,
        access_group_id=group.id,
        username="renew-preserves-access",
        status="active",
        note=None,
        idempotency_key="renew-preserves-create",
    )
    before_inbounds = {proxy_type: list(tags) for proxy_type, tags in user.inbounds.items()}
    before_proxies = sorted((proxy.type, dict(proxy.settings)) for proxy in user.proxies)
    before_hosts = [
        (row.inbound_tag, row.host_id)
        for row in session.query(access_groups.AccessGroupHost)
        .filter_by(access_group_id=group.id)
        .order_by(access_groups.AccessGroupHost.inbound_tag, access_groups.AccessGroupHost.host_id)
    ]

    admin_plans.update_plan(
        session,
        owner,
        plan,
        PlanUpdate(
            description="commercial renewal changed",
            version=PlanVersionInput(data_limit=2048, duration_days=60),
        ),
    )
    renewed, _, created = admin_plans.renew_user_from_plan(
        session,
        actor=owner,
        user=user,
        plan_id=plan.id,
        idempotency_key="renew-preserves-renewal",
    )

    assert created is True
    assert renewed.access_group_id == group.id
    assert renewed.inbounds == before_inbounds
    assert sorted((proxy.type, dict(proxy.settings)) for proxy in renewed.proxies) == before_proxies
    assert [
        (row.inbound_tag, row.host_id)
        for row in session.query(access_groups.AccessGroupHost)
        .filter_by(access_group_id=group.id)
        .order_by(access_groups.AccessGroupHost.inbound_tag, access_groups.AccessGroupHost.host_id)
    ] == before_hosts
    assert admin_plans.subscription_host_scope(session, renewed) == {tag: {first.id}}


def test_plan_assignment_without_access_group_fails_subscription_closed(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(name="legacy-no-access", version=_version(tag, first.id)),
    )
    user = User(username="legacy-no-access", admin_id=owner.id, status=user_models.UserStatus.active)
    session.add(user)
    session.flush()
    session.add(UserPlanAssignment(
        user_id=user.id,
        plan_id=plan.id,
        version_id=plan.current_version_id,
        actor_admin_id=owner.id,
        operation_type="create",
        idempotency_key="legacy-no-access-assignment",
    ))
    session.commit()

    assert admin_plans.subscription_host_scope(session, user) == {}
    assert admin_plans.subscription_host_scopes(session, [user]) == {user.id: {}}


def test_node_scope_filters_all_slots_and_preserves_source_config(db, monkeypatch):
    from contextlib import contextmanager
    from app.db.models import AccessGroupNode, User
    from app.xray.config import XRayConfig
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    group = access_groups.create(session, owner, AccessGroupInput(name="node scoped", inbounds=[tag], hosts={tag: [first.id]}))
    session.add(AccessGroupNode(access_group_id=group.id, node_id=7))
    user = User(username="node-scoped-user", admin_id=owner.id, access_group_id=group.id)
    session.add(user)
    session.commit()
    @contextmanager
    def get_db():
        yield session
    monkeypatch.setattr("app.db.GetDB", get_db)
    config = XRayConfig.__new__(XRayConfig)
    config.update({"inbounds": [{"settings": {"clients": [
        {"email": f"{user.id}.node-scoped-user"}, {"email": f"{user.id}.node-scoped-user.slot2"},
        {"email": "static@example.test"},
    ]}}]})
    assert access_groups.user_node_scope(user) == {7}
    assert len(access_groups.filter_node_config(config, 7)["inbounds"][0]["settings"]["clients"]) == 3
    assert len(access_groups.filter_node_config(config, None)["inbounds"][0]["settings"]["clients"]) == 1
    assert len(config["inbounds"][0]["settings"]["clients"]) == 3


def test_plan_create_and_update_do_not_write_network_topology(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(name="commercial", version=_version(tag, first.id)),
    )
    first_version_id = plan.current_version_id
    assert session.query(AdminUserPlanInbound).count() == 0
    assert session.query(AdminUserPlanHost).count() == 0

    session.add(AdminUserPlanInbound(version_id=first_version_id, inbound_tag=tag))
    session.add(AdminUserPlanHost(version_id=first_version_id, inbound_tag=tag, host_id=first.id))
    session.commit()

    updated = admin_plans.update_plan(
        session,
        owner,
        plan,
        PlanUpdate(
            description="new commercial terms",
            version=PlanVersionInput(data_limit=2048, duration_days=60),
        ),
    )
    assert updated.current_version_id != first_version_id
    assert session.query(AdminUserPlanVersion).count() == 2
    assert session.query(AdminUserPlanInbound).filter_by(version_id=first_version_id).count() == 1
    assert session.query(AdminUserPlanHost).filter_by(version_id=first_version_id).count() == 1
    assert session.query(AdminUserPlanInbound).filter_by(version_id=updated.current_version_id).count() == 0
    assert session.query(AdminUserPlanHost).filter_by(version_id=updated.current_version_id).count() == 0
    assert admin_plans.plan_response(session, updated).version.inbounds == []


def test_subscription_emits_only_explicit_active_plan_hosts(db, monkeypatch):
    session, owner = db
    tag, first, second = _configure_network(session, monkeypatch)
    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(name="subscription-scope", version=_version(tag, first.id)),
    )
    group = access_groups.create(
        session,
        owner,
        AccessGroupInput(name="subscription access", inbounds=[tag], hosts={tag: [first.id]}),
    )
    user, _, _ = admin_plans.create_user_from_plan(
        session,
        actor=owner,
        plan_id=plan.id,
        username="subscription-user",
        status="active",
        note=None,
        idempotency_key="stage4-subscription-user",
        access_group_id=group.id,
    )
    scope = admin_plans.subscription_host_scope(session, user)
    assert scope == {tag: {first.id}}
    monkeypatch.setattr(
        share.xray,
        "hosts",
        {
            tag: [
                _runtime_host(first.id, "selected {USERNAME}", "one.example"),
                _runtime_host(second.id, "not-selected {USERNAME}", "two.example"),
            ]
        },
    )
    monkeypatch.setattr(user_models, "create_subscription_token", lambda username: "token")
    response = UserResponse.model_validate(user, context={"host_scope": scope})
    assert len(response.links) == 1
    assert "one.example" in response.links[0]
    assert "two.example" not in response.links[0]
    api_response = admin_plans.scoped_user_response(session, user)
    list_response = admin_plans.scoped_user_responses(session, [user])[0]
    assert api_response.links == response.links
    assert list_response.links == response.links
    proxies = {
        ProxyTypes(proxy.type): ProxySettings.from_dict(ProxyTypes(proxy.type), proxy.settings)
        for proxy in user.proxies
    }
    capture = _CaptureConfiguration()
    rendered = share.process_inbounds_and_tags(
        user.inbounds,
        proxies,
        defaultdict(lambda: "", {"USERNAME": user.username, "PROTOCOL": "vless"}),
        capture,
        host_scope=scope,
    )
    assert rendered == [(f"selected {user.username}", "one.example")]


def test_plan_create_rejects_network_payload_before_service_execution(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanCreate(
            name="forbidden-network",
            version=PlanVersionInput.model_validate(
                {
                    "data_limit": 1024,
                    "duration_days": 30,
                    "inbounds": [tag],
                    "hosts": {tag: [first.id]},
                }
            ),
        )


def test_plan_access_grant_is_independent_from_target_network_scope(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    child = Admin(username="child", hashed_password="x", is_sudo=False)
    session.add(child)
    session.flush()
    session.add(
        MarzhelpAdminSettings(
            admin_id=child.id,
            all_inbounds=False,
            calculate_volume="used_traffic",
        )
    )
    session.commit()
    admin_hierarchy.attach_new_child(
        session,
        actor=owner,
        parent=owner,
        child=child,
        child_role=admin_hierarchy.ADMIN,
    )

    plan = admin_plans.create_plan(
        session,
        owner,
        PlanCreate(
            name="target-commercial-access",
            version=_version(tag, first.id),
            allowed_admin_ids=[child.id],
        ),
    )
    assert admin_plans.can_use_plan(session, child, plan.id)
    assert session.query(AdminUserPlanInbound).count() == 0
    assert session.query(AdminUserPlanHost).count() == 0


def test_plan_response_batch_has_constant_query_count(db, monkeypatch):
    session, owner = db
    tag, first, _ = _configure_network(session, monkeypatch)
    for number in range(3):
        admin_plans.create_plan(
            session,
            owner,
            PlanCreate(name=f"batch-{number}", version=_version(tag, first.id)),
        )
    plans = admin_plans.effective_plans_query(session, owner).order_by(AdminUserPlan.id).all()
    statements = []

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        responses = admin_plans.plan_responses(session, plans)
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)

    assert [response.name for response in responses] == ["batch-0", "batch-1", "batch-2"]
    assert len(statements) == 4
