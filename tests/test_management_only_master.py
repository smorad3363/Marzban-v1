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


def test_disabled_local_usage_skips_both_stats_endpoints(monkeypatch):
    from app.jobs import record_usages
    monkeypatch.setattr(record_usages,'XRAY_LOCAL_CORE_ENABLED',False)
    monkeypatch.setattr(xray,'nodes',{})
    users=Mock(side_effect=AssertionError('no local user polling'))
    outbounds=Mock(side_effect=AssertionError('no local outbound polling'))
    monkeypatch.setattr(record_usages,'get_user_counter_snapshot',users)
    monkeypatch.setattr(record_usages,'get_outbounds_stats',outbounds)
    record_usages.record_user_usages()
    record_usages.record_node_usages()
    users.assert_not_called();outbounds.assert_not_called()


def test_remote_usage_is_still_sampled_without_local_core(monkeypatch):
    from app.jobs import record_usages
    monkeypatch.setattr(record_usages,'XRAY_LOCAL_CORE_ENABLED',False)
    remote=SimpleNamespace(connected=True,started=True,usage_coefficient=1,api=object())
    monkeypatch.setattr(xray,'nodes',{7:remote})
    sample=Mock(return_value=None)
    monkeypatch.setattr(record_usages,'get_user_counter_snapshot',sample)
    record_usages.record_user_usages()
    sample.assert_called_once_with(remote.api)


def test_installer_only_disables_core_in_fresh_environment():
    from pathlib import Path
    source=Path('scripts/marzban.sh').read_text()
    occurrence=source.index("echo 'XRAY_LOCAL_CORE_ENABLED=false'")
    install=source.index('install_marzban()')
    assert install < occurrence < source.index('install_command()')
    assert source.count("echo 'XRAY_LOCAL_CORE_ENABLED=false'")==1
