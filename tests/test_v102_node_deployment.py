from pathlib import Path

import yaml


def test_node_compose_uses_same_release_image_without_database():
    compose_text = Path("docker-compose.node.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(compose_text)
    assert set(data["services"]) == {"marzban-node"}
    service = data["services"]["marzban-node"]
    assert service["image"].startswith("${MARZBAN_NODE_IMAGE")
    assert service["command"] == ["python", "-m", "node_runtime.main"]
    assert service["network_mode"] == "host"
    assert service["environment"]["SSL_CLIENT_CERT_FILE"] == "/var/lib/marzban-node/panel-client.crt"
    assert service["environment"]["EVENT_DB_PATH"] == "/var/lib/marzban-node/events.sqlite3"
    assert service["volumes"] == ["/var/lib/marzban-node:/var/lib/marzban-node"]
    lowered = compose_text.lower()
    assert "mysql" not in lowered
    assert "sqlalchemy" not in lowered
    assert "panel-client.key" not in lowered
    assert "node_runtime.main" in compose_text


def test_node_installer_is_release_verified_and_keeps_panel_private_key_off_node():
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    assert 'NODE_APP_DIR="$INSTALL_DIR/$NODE_APP_NAME"' in installer
    assert 'NODE_DATA_DIR="/var/lib/$NODE_APP_NAME"' in installer
    assert 'NODE_CLIENT_CERT_FILE="$NODE_DATA_DIR/panel-client.crt"' in installer
    assert 'MARZBAN_NODE_COMPOSE_PATH="${MARZBAN_NODE_COMPOSE_PATH:-docker-compose.node.yml}"' in installer
    assert 'node_source_supports_runtime "$requested_version"' in installer
    assert 'ensure_marzban_image "$requested_version"' in installer
    assert 'node_runtime/main.py' in installer
    assert 'openssl x509 -in "$path" -noout' in installer
    assert 'install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"' in installer
    assert 'verify_node_version_integrity "$requested_version"' in installer
    assert 'release_commit_for_version "$expected_version"' in installer
    assert 'org.opencontainers.image.revision' in installer
    assert 'Built-in Node deployment accepts published release versions only.' in installer
    assert 'marzban node <install|update|status|logs>' in installer
    assert 'shift; node_command "$@";;' in installer
    assert "panel-client.key" not in installer
    assert "NODE_CLIENT_KEY" not in installer


def test_node_install_requires_explicit_panel_certificate_and_separate_ports():
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    assert '--client-cert-file' in installer
    assert 'Node service and Xray API ports must differ.' in installer
    assert '--service-port' in installer
    assert '--api-port' in installer
    assert '--event-max-rows' in installer
    assert 'node_validate_event_rows' in installer
