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
    assert 'marzban node <install|update|status|doctor|logs>' in installer
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



def test_node_doctor_is_local_non_mutating_and_wired_into_cli():
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    doctor = installer.split("node_doctor_command()", 1)[1].split("node_logs_command()", 1)[0]
    assert 'doctor) node_doctor_command "$@" ;;' in installer
    assert 'Usage: marzban node doctor' in doctor
    assert 'openssl x509 -checkend 0' in doctor
    assert 'node_compose config' in doctor
    assert 'org.opencontainers.image.revision' in doctor
    assert 'NODE_RUNTIME_PORT' in doctor and 'XRAY_API_PORT' in doctor
    assert 'EVENT_MAX_ROWS' in doctor
    assert 'cat "$NODE_ENV_FILE"' not in doctor
    assert 'cat "$NODE_CLIENT_CERT_FILE"' not in doctor
    assert 'github_download' not in doctor
    assert 'node_compose up' not in doctor
    assert 'node_compose down' not in doctor
    assert 'install_package' not in doctor


def test_node_doctor_reports_local_readiness_without_leaking_env(tmp_path):
    cert = _make_test_certificate(tmp_path)
    server_cert = tmp_path / "ssl_cert.pem"
    server_key = tmp_path / "ssl_key.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(server_key),
            "-out",
            str(server_cert),
            "-subj",
            "/CN=Marzban Node Runtime Test",
            "-days",
            "2",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    compose = tmp_path / "docker-compose.yml"
    env_file = tmp_path / ".env"
    client_cert = tmp_path / "panel-client.crt"
    event_db = tmp_path / "events.sqlite3"
    revision = "1" * 40
    image = "ghcr.io/smorad3363/marzban-v1:v1.1.6"
    compose.write_text("services: {}\n", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                f"MARZBAN_NODE_IMAGE={image}",
                "NODE_RUNTIME_VERSION=v1.1.6",
                "NODE_RUNTIME_PORT=62050",
                "XRAY_API_PORT=62051",
                "EVENT_MAX_ROWS=20000",
                "DO_NOT_LEAK_THIS=super-secret-sentinel",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    client_cert.write_bytes(cert.read_bytes())
    event_db.write_bytes(b"sqlite-placeholder")
    for path in (compose, env_file, client_cert, event_db, server_key):
        path.chmod(0o600)
    server_cert.chmod(0o644)
    revision_file = tmp_path / ".release-revision"
    version_file = tmp_path / ".cli-version"
    revision_file.write_text(revision + "\n", encoding="utf-8")
    version_file.write_text("v1.1.6\n", encoding="utf-8")

    shell = f"""source scripts/marzban.sh
NODE_APP_DIR={shlex.quote(str(tmp_path))}
NODE_DATA_DIR={shlex.quote(str(tmp_path))}
NODE_COMPOSE_FILE={shlex.quote(str(compose))}
NODE_ENV_FILE={shlex.quote(str(env_file))}
NODE_CLIENT_CERT_FILE={shlex.quote(str(client_cert))}
NODE_RELEASE_REVISION_FILE={shlex.quote(str(revision_file))}
NODE_CLI_VERSION_FILE={shlex.quote(str(version_file))}
check_running_as_root() {{ :; }}
node_doctor_detect_compose() {{ COMPOSE=mock_compose; return 0; }}
mock_compose() {{ return 0; }}
node_service_container() {{ printf '%s\\n' node-container-id; }}
docker() {{
  case "$*" in
    *'.State.Status'*) printf '%s\\n' running ;;
    *'.State.Health'*) printf '%s\\n' healthy ;;
    *'.Config.Image'*) printf '%s\\n' {shlex.quote(image)} ;;
    *'{{.Image}}'*) printf '%s\\n' sha256:test-image-id ;;
    *'org.opencontainers.image.revision'*) printf '%s\\n' {revision} ;;
    *) return 0 ;;
  esac
}}
node_doctor_command
"""
    result = subprocess.run(
        ["bash", "-c", shell],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Node doctor summary:" in result.stdout
    assert "0 failures" in result.stdout
    assert "super-secret-sentinel" not in result.stdout
    assert "super-secret-sentinel" not in result.stderr

    client_cert.unlink()
    failed = subprocess.run(
        ["bash", "-c", shell],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert failed.returncode != 0
    assert "Stored panel client certificate is missing" in failed.stdout
    assert "super-secret-sentinel" not in failed.stdout
