from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import crud
from app.db.models import Node as DBNode
from app.device_limit.engine import DeviceLimitEngine
from app.models.node import NodeCreate, NodeModify


def _base(**overrides):
    data = {
        "name": "edge-1",
        "address": "127.0.0.1",
        "port": 62050,
        "api_port": 62051,
        "usage_coefficient": 1.0,
        "watchdog_enabled": True,
    }
    data.update(overrides)
    return data


def test_direct_is_default_and_rejects_trust_material():
    direct = NodeCreate(**_base())
    assert direct.ip_source_mode.value == "direct"
    assert direct.cdn_provider is None
    assert direct.trusted_proxy_cidrs is None
    with pytest.raises(ValidationError):
        NodeCreate(**_base(cdn_provider="cloudflare"))


def test_custom_xff_requires_and_canonicalizes_cidrs():
    with pytest.raises(ValidationError):
        NodeCreate(**_base(ip_source_mode="trusted_xff", cdn_provider="custom"))
    node = NodeCreate(**_base(
        ip_source_mode="trusted_xff",
        cdn_provider="custom",
        trusted_proxy_cidrs=["10.1.2.3/8", "10.0.0.0/8", "2001:db8::1/32"],
    ))
    assert node.trusted_proxy_cidrs == ["10.0.0.0/8", "2001:db8::/32"]


def test_cloudflare_xff_can_defer_managed_ranges_to_runtime():
    node = NodeCreate(**_base(ip_source_mode="trusted_xff", cdn_provider="cloudflare"))
    assert node.cdn_provider.value == "cloudflare"
    assert node.trusted_proxy_cidrs is None


def test_proxy_protocol_requires_trusted_peer_and_no_cdn_provider():
    with pytest.raises(ValidationError):
        NodeCreate(**_base(ip_source_mode="proxy_protocol"))
    with pytest.raises(ValidationError):
        NodeCreate(**_base(
            ip_source_mode="proxy_protocol",
            cdn_provider="cloudflare",
            trusted_proxy_cidrs=["10.0.0.0/8"],
        ))


def test_policy_update_is_atomic_at_api_model_boundary():
    with pytest.raises(ValidationError):
        NodeModify(ip_source_mode="trusted_xff")
    update = NodeModify(
        ip_source_mode="trusted_xff",
        cdn_provider="custom",
        trusted_proxy_cidrs=["192.0.2.10/24"],
    )
    assert update.trusted_proxy_cidrs == ["192.0.2.0/24"]


def test_crud_round_trip_persists_node_ip_policy():
    engine = create_engine("sqlite:///:memory:")
    DBNode.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        created = crud.create_node(db, NodeCreate(**_base(
            ip_source_mode="trusted_xff",
            cdn_provider="custom",
            trusted_proxy_cidrs=["192.0.2.8/24"],
        )))
        assert created.ip_source_mode == "trusted_xff"
        assert created.cdn_provider == "custom"
        assert created.trusted_proxy_cidrs == ["192.0.2.0/24"]

        updated = crud.update_node(db, created, NodeModify(
            ip_source_mode="proxy_protocol",
            cdn_provider=None,
            trusted_proxy_cidrs=["198.51.100.7/24"],
        ))
        assert updated.ip_source_mode == "proxy_protocol"
        assert updated.cdn_provider is None
        assert updated.trusted_proxy_cidrs == ["198.51.100.0/24"]
    finally:
        db.close()


def test_migration_is_single_extension_of_access_group_head():
    migration = Path("app/db/migrations/versions/f6b2c9d4e701_add_node_ip_source_policy.py").read_text(encoding="utf-8")
    assert 'revision = "f6b2c9d4e701"' in migration
    assert 'down_revision = "c9e1f4a7b203"' in migration
    assert 'server_default="direct"' in migration


def test_frontend_exposes_safe_node_ip_source_controls():
    context = Path("app/dashboard/src/contexts/NodesContext.tsx").read_text(encoding="utf-8")
    workspace = Path("app/dashboard/src/components/NodesManagementWorkspace.tsx").read_text(encoding="utf-8")
    assert 'z.enum(["direct", "trusted_xff", "proxy_protocol"])' in context
    assert 'name="ip_source_mode"' in workspace
    assert 'name="trusted_proxy_cidrs"' in workspace
    assert 'تنظیمات منبع IP فقط باید برای پراکسی‌های کاملاً مورد اعتماد فعال شود.' in workspace


_XRAY_ACCEPTED = (
    "2026/09/06 12:00:00 8.8.8.8:51000 accepted tcp:example.com:443 "
    "[vless >> direct] email: 42.demo.slot1"
)


def _limited_tracker() -> DeviceLimitEngine:
    tracker = DeviceLimitEngine()
    tracker.configure(True, "hybrid", True)
    tracker._limited_user_ids = {42}
    return tracker


def test_non_direct_node_is_fail_closed_until_secure_runtime_is_available():
    tracker = _limited_tracker()
    tracker.set_source_ip_trust("node:9", False)
    assert tracker.record_log(_XRAY_ACCEPTED, "node:9") == 0
    diagnostics = tracker.diagnostics()
    assert diagnostics["rejected_untrusted_ip_source"] == 1
    assert diagnostics["untrusted_ip_sources"] == ["node:9"]
    addresses, sources, per_slot = tracker.live_snapshot(42, 300, 1)
    assert addresses == set()
    assert sources == set()
    assert per_slot == {}


def test_source_trust_toggle_is_immediate_and_master_is_never_blocked_by_node_policy():
    tracker = _limited_tracker()
    tracker.set_source_ip_trust("node:9", False)
    assert tracker.record_log(_XRAY_ACCEPTED, "node:9") == 0
    assert tracker.record_log(_XRAY_ACCEPTED, "master") == 1
    tracker.set_source_ip_trust("node:9", True)
    assert tracker.record_log(_XRAY_ACCEPTED, "node:9") == 1
    addresses, sources, _ = tracker.live_snapshot(42, 300, 1)
    assert addresses == {"8.8.8.8"}
    assert sources == {"master", "node:9"}


def test_db_policy_refresh_is_one_query_boundary_not_a_log_path_lookup():
    engine = create_engine("sqlite:///:memory:")
    DBNode.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        node = crud.create_node(db, NodeCreate(**_base(
            ip_source_mode="trusted_xff",
            cdn_provider="custom",
            trusted_proxy_cidrs=["192.0.2.0/24"],
        )))
        tracker = _limited_tracker()
        tracker._refresh_node_ip_source_policies(db)
        assert tracker.record_log(_XRAY_ACCEPTED, f"node:{node.id}") == 0
        node.ip_source_mode = "direct"
        node.cdn_provider = None
        node.trusted_proxy_cidrs = None
        db.commit()
        tracker._refresh_node_ip_source_policies(db)
        assert tracker.record_log(_XRAY_ACCEPTED, f"node:{node.id}") == 1
    finally:
        db.close()


def test_node_router_synchronizes_enforcement_cache_after_mutations():
    source = Path("app/routers/node.py").read_text(encoding="utf-8")
    assert "_sync_device_limit_ip_policy(dbnode)" in source
    assert "_sync_device_limit_ip_policy(updated_node)" in source
    assert "_forget_device_limit_ip_policy(target_id)" in source
