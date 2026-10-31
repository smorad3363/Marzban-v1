import importlib
import importlib.util
from types import SimpleNamespace
from unittest.mock import Mock

from app import xray
core_module = importlib.import_module("app.xray.core")


def test_disabled_local_core_never_starts_even_after_restart(monkeypatch):
    monkeypatch.setattr(core_module, 'XRAY_LOCAL_CORE_ENABLED', False)
    core = core_module.XRayCore('/usr/bin/xray')
    launch = Mock(side_effect=AssertionError('local process must not start'))
    monkeypatch.setattr(core_module.subprocess, 'Popen', launch)
    core.start({})
    core.restart({})
    assert not core.started
    launch.assert_not_called()


def test_management_only_health_keeps_remote_node_check(monkeypatch):
    spec = importlib.util.spec_from_file_location('management_health', 'app/jobs/0_xray_core.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'XRAY_LOCAL_CORE_ENABLED', False)
    local = SimpleNamespace(started=False, restart=Mock())
    remote = SimpleNamespace(connected=True, started=True, api=SimpleNamespace(get_sys_stats=Mock()))
    monkeypatch.setattr(xray, 'core', local)
    monkeypatch.setattr(xray, 'nodes', {12: remote})
    module.core_health_check()
    local.restart.assert_not_called()
    remote.api.get_sys_stats.assert_called_once()
