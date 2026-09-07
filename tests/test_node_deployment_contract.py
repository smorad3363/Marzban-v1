from pathlib import Path
import shlex
import subprocess

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
    assert 'NODE_SCRIPT_PATH="/usr/local/bin/marzban-node"' in installer
    node_section = installer.split("node_is_installed()", 1)[1].split("rollback_command()", 1)[0]
    assert 'install_node_script_from_repo "$requested_version"' in node_section
    assert 'install_marzban_script_from_repo' not in node_section
    assert 'if ! is_marzban_installed; then' in node_section
    assert 'install -m 755 "$temp_script" /usr/local/bin/marzban' in node_section
    assert "panel-client.key" not in installer
    assert "NODE_CLIENT_KEY" not in installer


def test_node_install_supports_interactive_certificate_and_explicit_file():
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    assert '--client-cert-file' in installer
    assert 'node_prompt_client_cert' in installer
    assert 'Paste the Marzban Node certificate from the Master panel.' in installer
    assert 'if [ -z "$client_cert_file" ]; then' in installer
    assert 'client_cert_file="$NODE_INTERACTIVE_CERT_FILE"' in installer
    assert 'Node service and Xray API ports must differ.' in installer
    assert '--service-port' in installer
    assert '--api-port' in installer
    assert '--event-max-rows' in installer
    assert 'node_validate_event_rows' in installer


def _make_test_certificate(tmp_path: Path) -> Path:
    cert = tmp_path / "panel-client.crt"
    key = tmp_path / "panel-client.key"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-subj",
            "/CN=Marzban Node Test",
            "-days",
            "1",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return cert


def test_node_interactive_certificate_prompt_accepts_pasted_pem(tmp_path):
    cert = _make_test_certificate(tmp_path)
    script = (
        "source scripts/marzban.sh\n"
        'NODE_INTERACTIVE_CERT_FILE=""\n'
        f"node_prompt_client_cert < {shlex.quote(str(cert))}\n"
        'test -f "$NODE_INTERACTIVE_CERT_FILE"\n'
        'openssl x509 -in "$NODE_INTERACTIVE_CERT_FILE" -noout >/dev/null\n'
        'rm -f "$NODE_INTERACTIVE_CERT_FILE"\n'
    )
    subprocess.run(["bash", "-c", script], check=True)


def test_node_interactive_certificate_prompt_rejects_incomplete_paste():
    script = (
        "source scripts/marzban.sh\n"
        'NODE_INTERACTIVE_CERT_FILE=""\n'
        "node_prompt_client_cert\n"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        input="-----BEGIN CERTIFICATE-----\nnot-a-complete-certificate\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "Certificate paste was incomplete" in result.stdout


def test_node_interactive_certificate_prompt_rejects_missing_pem_header():
    script = (
        "source scripts/marzban.sh\n"
        'NODE_INTERACTIVE_CERT_FILE=""\n'
        "node_prompt_client_cert\n"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        input="not-a-certificate\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "Certificate paste must start with -----BEGIN CERTIFICATE-----." in result.stdout


def test_node_interactive_certificate_prompt_rejects_complete_invalid_x509():
    script = (
        "source scripts/marzban.sh\n"
        'NODE_INTERACTIVE_CERT_FILE=""\n'
        "node_prompt_client_cert\n"
    )
    result = subprocess.run(
        ["bash", "-c", script],
        input=(
            "-----BEGIN CERTIFICATE-----\n"
            "not-a-valid-x509-certificate\n"
            "-----END CERTIFICATE-----\n"
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "The pasted certificate is not a valid X.509 PEM certificate." in result.stdout
