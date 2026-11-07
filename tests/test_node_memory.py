from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from node_runtime import memory
from node_runtime.config import RuntimeSettings


def test_effective_memory_uses_the_smaller_container_limit(tmp_path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal:       8388608 kB\nMemAvailable: 1024 kB\n")
    v2, v1 = tmp_path / "memory.max", tmp_path / "memory.limit_in_bytes"
    v2.write_text("max\n")
    v1.write_text(str(2**63 - 4096))
    assert memory.effective_memory_bytes(meminfo, (v2, v1)) == 8 * 1024**3
    v2.write_text(str(384 * 1024**2))
    assert memory.effective_memory_bytes(meminfo, (v2, v1)) == 384 * 1024**2
    v1.write_text(str(256 * 1024**2))
    assert memory.effective_memory_bytes(meminfo, (v2, v1)) == 256 * 1024**2


@pytest.mark.parametrize("gib", [1, 2, 4, 8, 16, 32])
def test_balanced_budget_is_75_percent_and_reaches_a_real_child(monkeypatch, gib):
    monkeypatch.setattr(memory, "effective_memory_bytes", lambda: gib * 1024**3)
    source = {"PATH": "/usr/bin:/bin", "KEEP_EXISTING": "yes"}
    environment = memory.xray_environment(source, "/assets", "balanced")
    child = subprocess.run(
        [sys.executable, "-c", "import os,json;print(json.dumps({k:os.getenv(k) for k in ['GOGC','GOMEMLIMIT','XRAY_LOCATION_ASSET','KEEP_EXISTING']}))"],
        env=environment, check=True, text=True, capture_output=True,
    )
    assert json.loads(child.stdout) == {
        "GOGC": "50", "GOMEMLIMIT": f"{gib * 768}MiB",
        "XRAY_LOCATION_ASSET": "/assets", "KEEP_EXISTING": "yes",
    }
    assert "GOGC" not in source and "GOMEMLIMIT" not in source


def test_explicit_smaller_budget_survives_and_larger_budget_is_capped(monkeypatch):
    monkeypatch.setattr(memory, "effective_memory_bytes", lambda: 4 * 1024**3)
    assert memory.xray_environment({"GOGC": "100", "GOMEMLIMIT": "1GiB"}, "/a", "balanced")["GOMEMLIMIT"] == "1GiB"
    assert memory.xray_environment({"GOGC": "100"}, "/a", "balanced")["GOGC"] == "100"
    for value in ("8GiB", "off", ""):
        assert memory.xray_environment({"GOMEMLIMIT": value}, "/a", "balanced")["GOMEMLIMIT"] == "3072MiB"
    with pytest.raises(ValueError, match="GOMEMLIMIT"):
        memory.xray_environment({"GOMEMLIMIT": "bad-value"}, "/a", "balanced")


def test_policy_keeps_both_shadowsocks_formats_keys_and_accounting():
    config = {
        "inbounds": [
            {"protocol": "shadowsocks", "settings": {"method": "2022-blake3-aes-256-gcm", "password": "server-psk", "clients": [{"email": "1.fixture", "password": "user-psk"}]}},
            {"protocol": "shadowsocks", "settings": {"clients": [{"email": "1.fixture", "method": "chacha20-ietf-poly1305", "password": "legacy-key"}]}},
        ],
        "outbounds": [{"tag": "keep", "protocol": "freedom"}],
        "policy": {"levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True, "statsUserOnline": True}, "3": {"handshake": 3, "connIdle": 30, "bufferSize": 0}}, "system": {"statsOutboundDownlink": True}},
    }
    before = copy.deepcopy(config)
    memory.apply_memory_policy(config, "balanced")
    assert config["inbounds"] == before["inbounds"]
    assert config["outbounds"] == before["outbounds"]
    assert config["policy"]["system"] == before["policy"]["system"]
    assert config["policy"]["levels"]["3"] == before["policy"]["levels"]["3"]
    level = config["policy"]["levels"]["0"]
    assert level == {"statsUserUplink": True, "statsUserDownlink": True, "statsUserOnline": True, "handshake": 15, "connIdle": 120, "bufferSize": 64}
    once = copy.deepcopy(config)
    memory.apply_memory_policy(config, "balanced")
    assert config == once


def test_profile_off_preserves_custom_environment_and_policy(monkeypatch):
    monkeypatch.setattr(memory, "effective_memory_bytes", lambda: pytest.fail("off must not inspect RAM"))
    source = {"GOGC": "100", "GOMEMLIMIT": "off"}
    assert memory.xray_environment(source, "/assets", "off") == {**source, "XRAY_LOCATION_ASSET": "/assets"}
    config = {"policy": {"levels": {"0": {"connIdle": 900}}}}
    before = copy.deepcopy(config)
    memory.apply_memory_policy(config, "off")
    assert config == before


def test_runtime_last_mile_ss2022_guard_keeps_keys_and_classic_cipher(monkeypatch, tmp_path):
    from node_runtime.core import prepare_xray_config
    monkeypatch.setenv("SSL_CLIENT_CERT_FILE", str(tmp_path / "panel.crt"))
    modern = {"tag": "modern", "protocol": "shadowsocks", "settings": {
        "method": "2022-blake3-aes-256-gcm", "password": "server-psk", "clients": [
            {"email": "1.fixture", "level": 0, "password": "user-psk", "method": "2022-blake3-aes-256-gcm"},
        ],
    }}
    classic = {"tag": "classic", "protocol": "shadowsocks", "settings": {
        "clients": [{"email": "1.fixture", "password": "legacy-secret", "method": "chacha20-ietf-poly1305"}],
    }}
    result = prepare_xray_config(json.dumps({"inbounds": [modern, classic]}), "203.0.113.1", RuntimeSettings.from_env())
    modern_result = next(i for i in result["inbounds"] if i.get("tag") == "modern")
    assert modern_result["settings"]["password"] == "server-psk"
    assert modern_result["settings"]["clients"] == [{"email": "1.fixture", "level": 0, "password": "user-psk"}]
    assert next(i for i in result["inbounds"] if i.get("tag") == "classic") == classic
    assert "method" in modern["settings"]["clients"][0]


def test_runtime_profile_validation(monkeypatch, tmp_path):
    monkeypatch.setenv("SSL_CLIENT_CERT_FILE", str(tmp_path / "panel.crt"))
    monkeypatch.delenv("XRAY_NODE_MEMORY_PROFILE", raising=False)
    assert RuntimeSettings.from_env().memory_profile == "balanced"
    monkeypatch.setenv("XRAY_NODE_MEMORY_PROFILE", "off")
    assert RuntimeSettings.from_env().memory_profile == "off"
    monkeypatch.setenv("XRAY_NODE_MEMORY_PROFILE", "unknown")
    with pytest.raises(RuntimeError, match="XRAY_NODE_MEMORY_PROFILE"):
        RuntimeSettings.from_env()


def test_legacy_core_detection_does_not_treat_a_budget_as_an_ss2022_fix():
    for version in (None, "unknown", "25.3.6", "26.3.27", "26.9.9"):
        assert memory.legacy_ss2022_core(version)
    for version in ("26.10.31", "26.11.1", "27.1.1"):
        assert not memory.legacy_ss2022_core(version)


def test_node_installer_preserves_memory_settings_across_update(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GOGC=100\nGOMEMLIMIT=512MiB\nXRAY_NODE_MEMORY_PROFILE=balanced\n")
    script = "source scripts/marzban.sh\n" + f"NODE_ENV_FILE={str(env_file)!r}\n" + "node_write_env v1.1.24 61050 61051 12345\n"
    subprocess.run(["bash", "-c", script], check=True)
    result = dict(line.split("=", 1) for line in env_file.read_text().splitlines())
    assert result["GOGC"] == "100"
    assert result["GOMEMLIMIT"] == "512MiB"
    assert result["NODE_RUNTIME_PORT"] == "61050"
    assert result["XRAY_API_PORT"] == "61051"
    assert result["EVENT_MAX_ROWS"] == "12345"


def test_image_core_is_pinned_and_verified_on_both_supported_platforms():
    installer = Path("scripts/install-xray.sh").read_text()
    assert "e4bd9119f50ae7c41658b1abd0679ae06f98bd864a2907ff33f2f2cf7081b214" in installer
    assert "1811c8f1da0c3b6dc707ebaf1c8390e987ba39859a8f0a7aadd8526157f2ec8d" in installer
    assert "sha256sum --check" in installer
    for path in ("Dockerfile", "scripts/Dockerfile.dev"):
        dockerfile = Path(path).read_text()
        assert "ARG XRAY_VERSION=v26.10.31" in dockerfile
        assert 'bash /tmp/install-xray.sh "$XRAY_VERSION"' in dockerfile
        assert "install_latest_xray.sh" not in dockerfile
