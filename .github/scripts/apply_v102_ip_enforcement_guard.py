from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Engine: cache node IP-source trust so the hot log path never hits the DB.
replace_once(
    "app/device_limit/engine.py",
    '''    DeviceLimitUserState,
    DeviceSlot,
    User,
)''',
    '''    DeviceLimitUserState,
    DeviceSlot,
    Node,
    User,
)''',
)
replace_once(
    "app/device_limit/engine.py",
    '''    "rejected_runtime_disabled",
    "rejected_not_accepted",''',
    '''    "rejected_runtime_disabled",
    "rejected_untrusted_ip_source",
    "rejected_not_accepted",''',
)
replace_once(
    "app/device_limit/engine.py",
    '''        self._ip_detection_enabled = True
        self._limited_user_ids: set[int] | None = None
        self._last_user_cache_refresh = 0.0''',
    '''        self._ip_detection_enabled = True
        self._limited_user_ids: set[int] | None = None
        self._untrusted_ip_sources: set[str] = set()
        self._last_user_cache_refresh = 0.0''',
)
replace_once(
    "app/device_limit/engine.py",
    '''            with GetDB() as db:
                settings = db.get(DeviceLimitSettings, 1)''',
    '''            with GetDB() as db:
                self._refresh_node_ip_source_policies(db)
                settings = db.get(DeviceLimitSettings, 1)''',
)
replace_once(
    "app/device_limit/engine.py",
    '''    def stop(self) -> None:
        self._stop.set()

    def _configure_event_logger(self) -> None:''',
    '''    def stop(self) -> None:
        self._stop.set()

    def set_source_ip_trust(self, source_name: str, trusted: bool) -> None:
        """Update the in-memory trust decision for one log source."""
        if not source_name.startswith("node:"):
            return
        with self._lock:
            if trusted:
                self._untrusted_ip_sources.discard(source_name)
            else:
                self._untrusted_ip_sources.add(source_name)

    def forget_source_ip_trust(self, source_name: str) -> None:
        with self._lock:
            self._untrusted_ip_sources.discard(source_name)

    def _refresh_node_ip_source_policies(self, db) -> None:
        rows = db.query(Node.id, Node.ip_source_mode).all()
        untrusted = {
            f"node:{node_id}"
            for node_id, mode in rows
            if (mode or "direct") != "direct"
        }
        with self._lock:
            self._untrusted_ip_sources = untrusted

    def _configure_event_logger(self) -> None:''',
)
replace_once(
    "app/device_limit/engine.py",
    '''            limited_user_ids = (
                None
                if self._limited_user_ids is None
                else set(self._limited_user_ids)
            )
        if not runtime_enabled:''',
    '''            limited_user_ids = (
                None
                if self._limited_user_ids is None
                else set(self._limited_user_ids)
            )
            untrusted_ip_source = source_name in self._untrusted_ip_sources
        if not runtime_enabled:''',
)
replace_once(
    "app/device_limit/engine.py",
    '''            return 0

        parsed_events: list[tuple[int, int, str]] = []''',
    '''            return 0
        if untrusted_ip_source:
            counts["rejected_untrusted_ip_source"] = len(lines)
            with self._lock:
                self._diagnostic_counts.update(counts)
                self._last_log_seen_at = now
            return 0

        parsed_events: list[tuple[int, int, str]] = []''',
)
replace_once(
    "app/device_limit/engine.py",
    '''                    "ip_detection_enabled": self._ip_detection_enabled,
                    "active_collectors": sorted(''',
    '''                    "ip_detection_enabled": self._ip_detection_enabled,
                    "untrusted_ip_sources": sorted(self._untrusted_ip_sources),
                    "active_collectors": sorted(''',
)
replace_once(
    "app/device_limit/engine.py",
    '''    def evaluate(self) -> None:
        with GetDB() as db:
            settings = db.get(DeviceLimitSettings, 1)''',
    '''    def evaluate(self) -> None:
        with GetDB() as db:
            self._refresh_node_ip_source_policies(db)
            settings = db.get(DeviceLimitSettings, 1)''',
)

# Response model must expose the fail-safe decision rather than dropping it.
replace_once(
    "app/models/device_limit.py",
    '''    rejected_runtime_disabled: int
    rejected_not_accepted: int''',
    '''    rejected_runtime_disabled: int
    rejected_untrusted_ip_source: int
    rejected_not_accepted: int''',
)
replace_once(
    "app/models/device_limit.py",
    '''    active_collectors: list[str]
    received_lines: int''',
    '''    active_collectors: list[str]
    untrusted_ip_sources: list[str]
    received_lines: int''',
)

# Router: synchronize the cache immediately after a committed Node policy change.
replace_once(
    "app/routers/node.py",
    '''router = APIRouter(
    tags=["Node"], prefix="/api", responses={401: responses._401, 403: responses._403}
)


def add_host_if_needed''',
    '''router = APIRouter(
    tags=["Node"], prefix="/api", responses={401: responses._401, 403: responses._403}
)


def _sync_device_limit_ip_policy(dbnode) -> None:
    from app.device_limit.engine import engine as device_limit_engine

    mode = getattr(dbnode, "ip_source_mode", "direct") or "direct"
    device_limit_engine.set_source_ip_trust(f"node:{dbnode.id}", mode == "direct")


def _forget_device_limit_ip_policy(node_id: int) -> None:
    from app.device_limit.engine import engine as device_limit_engine

    device_limit_engine.forget_source_ip_trust(f"node:{node_id}")


def add_host_if_needed''',
)
replace_once(
    "app/routers/node.py",
    '''    bg.add_task(xray.operations.connect_node, node_id=dbnode.id)
    bg.add_task(add_host_if_needed, new_node, db)''',
    '''    _sync_device_limit_ip_policy(dbnode)
    bg.add_task(xray.operations.connect_node, node_id=dbnode.id)
    bg.add_task(add_host_if_needed, new_node, db)''',
)
replace_once(
    "app/routers/node.py",
    '''    updated_node = crud.update_node(db, dbnode, modified_node)
    bandwidth_store.forget(updated_node.id)''',
    '''    updated_node = crud.update_node(db, dbnode, modified_node)
    _sync_device_limit_ip_policy(updated_node)
    bandwidth_store.forget(updated_node.id)''',
)
replace_once(
    "app/routers/node.py",
    '''    crud.remove_node(db, dbnode)
    bandwidth_store.forget(target_id)''',
    '''    crud.remove_node(db, dbnode)
    _forget_device_limit_ip_policy(target_id)
    bandwidth_store.forget(target_id)''',
)

# Focused tests use a real Xray access-log shape, not a mocked parser.
test_path = Path("tests/test_v102_node_ip_policy.py")
test_text = test_path.read_text(encoding="utf-8")
replace_once(
    "tests/test_v102_node_ip_policy.py",
    '''from app.db.models import Node as DBNode
from app.models.node import NodeCreate, NodeModify
''',
    '''from app.db.models import Node as DBNode
from app.device_limit.engine import DeviceLimitEngine
from app.models.node import NodeCreate, NodeModify
''',
)
append = '''

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
'''
if "test_non_direct_node_is_fail_closed_until_secure_runtime_is_available" in test_text:
    raise SystemExit("enforcement guard tests already exist")
test_path.write_text(test_text + append, encoding="utf-8")
