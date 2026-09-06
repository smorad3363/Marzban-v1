from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one context match, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "scripts/marzban.sh",
    '''ENV_FILE="$APP_DIR/.env"\nLAST_XRAY_CORES=10\n''',
    '''ENV_FILE="$APP_DIR/.env"\nNODE_APP_NAME="marzban-node"\nNODE_APP_DIR="$INSTALL_DIR/$NODE_APP_NAME"\nNODE_DATA_DIR="/var/lib/$NODE_APP_NAME"\nNODE_COMPOSE_FILE="$NODE_APP_DIR/docker-compose.yml"\nNODE_ENV_FILE="$NODE_APP_DIR/.env"\nNODE_CLIENT_CERT_FILE="$NODE_DATA_DIR/panel-client.crt"\nNODE_RELEASE_REVISION_FILE="$NODE_APP_DIR/.release-revision"\nNODE_CLI_VERSION_FILE="$NODE_APP_DIR/.cli-version"\nLAST_XRAY_CORES=10\n''',
)

replace_once(
    "scripts/marzban.sh",
    '''MARZBAN_DOCKER_IMAGE="${MARZBAN_DOCKER_IMAGE:-ghcr.io/smorad3363/marzban-v1}"\nMYSQL_TARGET_VERSION="26.7.0"\n''',
    '''MARZBAN_DOCKER_IMAGE="${MARZBAN_DOCKER_IMAGE:-ghcr.io/smorad3363/marzban-v1}"\nMARZBAN_NODE_COMPOSE_PATH="${MARZBAN_NODE_COMPOSE_PATH:-docker-compose.node.yml}"\nMYSQL_TARGET_VERSION="26.7.0"\n''',
)

node_functions = r'''node_is_installed() {
    [ -f "$NODE_COMPOSE_FILE" ] && [ -f "$NODE_ENV_FILE" ]
}

node_prepare_host() {
    detect_os
    if ! command -v jq >/dev/null 2>&1; then
        install_package jq
    fi
    if ! command -v curl >/dev/null 2>&1; then
        install_package curl
    fi
    if ! command -v tar >/dev/null 2>&1; then
        install_package tar
    fi
    if ! command -v openssl >/dev/null 2>&1; then
        install_package openssl
    fi
    if ! command -v docker >/dev/null 2>&1; then
        install_docker
    fi
    detect_compose
}

node_validate_port() {
    local value="$1"
    local name="$2"
    if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
        colorized_echo red "$name must be an integer between 1 and 65535."
        return 1
    fi
}

node_validate_event_rows() {
    local value="$1"
    if [[ ! "$value" =~ ^[0-9]+$ ]] || [ "$value" -lt 1000 ] || [ "$value" -gt 1000000 ]; then
        colorized_echo red "--event-max-rows must be between 1000 and 1000000."
        return 1
    fi
}

node_validate_client_cert() {
    local path="$1"
    if [ -z "$path" ] || [ ! -f "$path" ]; then
        colorized_echo red "A readable panel certificate is required with --client-cert-file."
        return 1
    fi
    if ! openssl x509 -in "$path" -noout >/dev/null 2>&1; then
        colorized_echo red "--client-cert-file is not a valid X.509 PEM certificate."
        return 1
    fi
}

node_source_ref_path() {
    local requested_version="$1"
    local ref
    ref=$(marzban_script_ref "$requested_version")
    if [ "$ref" = "$MARZBAN_GITHUB_BRANCH" ]; then
        printf 'refs/heads/%s\n' "$ref"
    else
        printf '%s\n' "$ref"
    fi
}

node_source_supports_runtime() {
    local requested_version="$1"
    local ref_path
    ref_path=$(node_source_ref_path "$requested_version")
    github_download -fsSL \
        "https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/node_runtime/main.py" \
        -o /dev/null 2>/dev/null
}

node_fetch_compose() {
    local requested_version="$1"
    local ref_path
    ref_path=$(node_source_ref_path "$requested_version")
    install -d -m 700 "$NODE_APP_DIR"
    github_download -fsSL \
        "https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/${MARZBAN_NODE_COMPOSE_PATH}" \
        -o "$NODE_COMPOSE_FILE"
    chmod 600 "$NODE_COMPOSE_FILE"
}

node_env_value() {
    local key="$1"
    local fallback="$2"
    local value=""
    if [ -f "$NODE_ENV_FILE" ]; then
        value=$(sed -n "s/^${key}=//p" "$NODE_ENV_FILE" | tail -n 1)
    fi
    printf '%s\n' "${value:-$fallback}"
}

node_write_env() {
    local requested_version="$1"
    local service_port="$2"
    local api_port="$3"
    local event_max_rows="$4"
    umask 077
    cat > "$NODE_ENV_FILE" <<EOF
MARZBAN_NODE_IMAGE=$(marzban_docker_image "$requested_version")
NODE_RUNTIME_VERSION=$requested_version
NODE_RUNTIME_PORT=$service_port
XRAY_API_PORT=$api_port
EVENT_MAX_ROWS=$event_max_rows
EOF
    chmod 600 "$NODE_ENV_FILE"
}

node_compose() {
    $COMPOSE --env-file "$NODE_ENV_FILE" -f "$NODE_COMPOSE_FILE" -p "$NODE_APP_NAME" "$@"
}

node_service_container() {
    node_compose ps -q marzban-node 2>/dev/null
}

node_wait_for_health() {
    local container_id=""
    local state=""
    local health=""
    local attempt
    for attempt in $(seq 1 45); do
        container_id=$(node_service_container)
        if [ -n "$container_id" ]; then
            state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
            health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id" 2>/dev/null || true)
            if [ "$state" = "running" ] && { [ "$health" = "healthy" ] || [ -z "$health" ]; }; then
                return 0
            fi
            if [ "$state" = "exited" ] || [ "$state" = "dead" ]; then
                break
            fi
        fi
        sleep 2
    done
    colorized_echo red "Marzban Node did not become healthy."
    if [ -n "$container_id" ]; then
        docker logs --tail 200 "$container_id" || true
    fi
    return 1
}

verify_node_version_integrity() {
    local expected_version="$1"
    local expected_image expected_revision container_id running_image image_id running_revision
    expected_image=$(marzban_docker_image "$expected_version")
    expected_revision=$(release_commit_for_version "$expected_version")
    [[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] || {
        colorized_echo red "Node integrity failed: release source revision is unavailable."
        return 1
    }
    container_id=$(node_service_container)
    [ -n "$container_id" ] || { colorized_echo red "Node integrity failed: container is not running."; return 1; }
    running_image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
    [ "$running_image" = "$expected_image" ] || {
        colorized_echo red "Node integrity failed: running image is ${running_image:-unavailable}, expected ${expected_image}."
        return 1
    }
    image_id=$(docker inspect --format '{{.Image}}' "$container_id" 2>/dev/null || true)
    running_revision=$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image_id" 2>/dev/null || true)
    [ "$running_revision" = "$expected_revision" ] || {
        colorized_echo red "Node integrity failed: source revision is ${running_revision:-unavailable}, expected ${expected_revision}."
        return 1
    }
    printf '%s\n' "$expected_revision" > "$NODE_RELEASE_REVISION_FILE"
    printf '%s\n' "$expected_version" > "$NODE_CLI_VERSION_FILE"
    chmod 644 "$NODE_RELEASE_REVISION_FILE" "$NODE_CLI_VERSION_FILE"
    colorized_echo green "Node image integrity verified for ${expected_version}."
}

node_install_command() {
    local requested_version="latest"
    local client_cert_file=""
    local service_port="62050"
    local api_port="62051"
    local event_max_rows="20000"
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -v|--version)
                [ -n "${2:-}" ] || { colorized_echo red "--version requires a value."; return 1; }
                requested_version="$2"; shift 2 ;;
            --client-cert-file)
                [ -n "${2:-}" ] || { colorized_echo red "--client-cert-file requires a path."; return 1; }
                client_cert_file="$2"; shift 2 ;;
            --service-port)
                [ -n "${2:-}" ] || { colorized_echo red "--service-port requires a value."; return 1; }
                service_port="$2"; shift 2 ;;
            --api-port)
                [ -n "${2:-}" ] || { colorized_echo red "--api-port requires a value."; return 1; }
                api_port="$2"; shift 2 ;;
            --event-max-rows)
                [ -n "${2:-}" ] || { colorized_echo red "--event-max-rows requires a value."; return 1; }
                event_max_rows="$2"; shift 2 ;;
            -h|--help)
                echo "Usage: marzban node install [--version VERSION] --client-cert-file PATH [--service-port PORT] [--api-port PORT] [--event-max-rows ROWS]"
                return 0 ;;
            *)
                colorized_echo red "Unknown node install option: $1"
                return 1 ;;
        esac
    done

    check_running_as_root
    if node_is_installed; then
        colorized_echo red "Marzban Node already exists at $NODE_APP_DIR. Use: marzban node update"
        return 1
    fi
    node_prepare_host
    requested_version=$(resolve_requested_version "$requested_version") || return 1
    if ! is_release_version "$requested_version"; then
        colorized_echo red "Built-in Node deployment accepts published release versions only."
        return 1
    fi
    node_validate_port "$service_port" "--service-port" || return 1
    node_validate_port "$api_port" "--api-port" || return 1
    [ "$service_port" != "$api_port" ] || { colorized_echo red "Node service and Xray API ports must differ."; return 1; }
    node_validate_event_rows "$event_max_rows" || return 1
    node_validate_client_cert "$client_cert_file" || return 1
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    ensure_marzban_image "$requested_version" || return 1

    install -d -m 700 "$NODE_APP_DIR" "$NODE_DATA_DIR"
    install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"
    node_fetch_compose "$requested_version" || return 1
    node_write_env "$requested_version" "$service_port" "$api_port" "$event_max_rows"
    node_compose up -d --remove-orphans || return 1
    node_wait_for_health || return 1
    verify_node_version_integrity "$requested_version" || return 1
    install_marzban_script_from_repo "$requested_version" || return 1
    colorized_echo green "Marzban Node ${requested_version} is installed and healthy."
    colorized_echo blue "Node data: $NODE_DATA_DIR"
    colorized_echo blue "Panel certificate: $NODE_CLIENT_CERT_FILE"
}

node_update_command() {
    local requested_version="latest"
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -v|--version)
                [ -n "${2:-}" ] || { colorized_echo red "--version requires a value."; return 1; }
                requested_version="$2"; shift 2 ;;
            -h|--help)
                echo "Usage: marzban node update [--version VERSION]"
                return 0 ;;
            *)
                colorized_echo red "Unknown node update option: $1"
                return 1 ;;
        esac
    done

    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    node_prepare_host
    requested_version=$(resolve_requested_version "$requested_version") || return 1
    if ! is_release_version "$requested_version"; then
        colorized_echo red "Built-in Node deployment accepts published release versions only."
        return 1
    fi
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    [ -f "$NODE_CLIENT_CERT_FILE" ] || { colorized_echo red "Stored panel certificate is missing: $NODE_CLIENT_CERT_FILE"; return 1; }
    node_validate_client_cert "$NODE_CLIENT_CERT_FILE" || return 1
    ensure_marzban_image "$requested_version" || return 1

    local service_port api_port event_max_rows backup_dir
    service_port=$(node_env_value NODE_RUNTIME_PORT 62050)
    api_port=$(node_env_value XRAY_API_PORT 62051)
    event_max_rows=$(node_env_value EVENT_MAX_ROWS 20000)
    node_validate_port "$service_port" "NODE_RUNTIME_PORT" || return 1
    node_validate_port "$api_port" "XRAY_API_PORT" || return 1
    node_validate_event_rows "$event_max_rows" || return 1
    backup_dir="$NODE_APP_DIR/update-backup-$(date +%Y%m%d%H%M%S)"
    install -d -m 700 "$backup_dir"
    cp "$NODE_COMPOSE_FILE" "$backup_dir/docker-compose.yml"
    cp "$NODE_ENV_FILE" "$backup_dir/.env"
    chmod 600 "$backup_dir/.env" "$backup_dir/docker-compose.yml"

    node_fetch_compose "$requested_version" || return 1
    node_write_env "$requested_version" "$service_port" "$api_port" "$event_max_rows"
    if ! node_compose up -d --remove-orphans || ! node_wait_for_health || ! verify_node_version_integrity "$requested_version"; then
        colorized_echo red "Node update failed. Previous configuration is preserved at $backup_dir."
        return 1
    fi
    install_marzban_script_from_repo "$requested_version" || return 1
    colorized_echo green "Marzban Node updated successfully to ${requested_version}."
}

node_status_command() {
    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    detect_compose
    local container_id state health image version revision
    container_id=$(node_service_container)
    if [ -z "$container_id" ]; then
        colorized_echo red "Marzban Node is down."
        return 1
    fi
    state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
    health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id" 2>/dev/null || true)
    image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
    version=$(node_env_value NODE_RUNTIME_VERSION unknown)
    revision=$(cat "$NODE_RELEASE_REVISION_FILE" 2>/dev/null || true)
    echo "Status: ${state:-unknown}"
    echo "Health: ${health:-unavailable}"
    echo "Runtime version: ${version}"
    echo "Image: ${image:-unavailable}"
    echo "Source revision: ${revision:-unavailable}"
}

node_logs_command() {
    local follow="true"
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -n|--no-follow) follow="false"; shift ;;
            -h|--help)
                echo "Usage: marzban node logs [--no-follow]"
                return 0 ;;
            *) colorized_echo red "Unknown node logs option: $1"; return 1 ;;
        esac
    done
    check_running_as_root
    node_is_installed || { colorized_echo red "Marzban Node is not installed."; return 1; }
    detect_compose
    if [ "$follow" = "true" ]; then
        node_compose logs -f marzban-node
    else
        node_compose logs marzban-node
    fi
}

node_command() {
    local action="${1:-help}"
    [ "$#" -gt 0 ] && shift || true
    case "$action" in
        install) node_install_command "$@" ;;
        update) node_update_command "$@" ;;
        status) node_status_command "$@" ;;
        logs) node_logs_command "$@" ;;
        help|-h|--help)
            echo "Usage: marzban node <install|update|status|logs> [options]"
            ;;
        *)
            colorized_echo red "Unknown node command: $action"
            echo "Usage: marzban node <install|update|status|logs> [options]"
            return 1
            ;;
    esac
}

'''

replace_once(
    "scripts/marzban.sh",
    '''rollback_command() {\n''',
    node_functions + '''rollback_command() {\n''',
)

replace_once(
    "scripts/marzban.sh",
    '''    colorized_echo yellow "  mysql-upgrade   $(tput sgr0)– Safely migrate MySQL to ${MYSQL_TARGET_IMAGE}"\n    colorized_echo yellow "  uninstall       $(tput sgr0)– Uninstall Marzban"\n''',
    '''    colorized_echo yellow "  mysql-upgrade   $(tput sgr0)– Safely migrate MySQL to ${MYSQL_TARGET_IMAGE}"\n    colorized_echo yellow "  node            $(tput sgr0)– Install, update, inspect, or read logs from built-in Node Runtime V2"\n    colorized_echo yellow "  uninstall       $(tput sgr0)– Uninstall Marzban"\n''',
)

replace_once(
    "scripts/marzban.sh",
    '''    mysql-upgrade)\n        shift; mysql_upgrade_command "$@";;\n    uninstall)\n''',
    '''    mysql-upgrade)\n        shift; mysql_upgrade_command "$@";;\n    node)\n        shift; node_command "$@";;\n    uninstall)\n''',
)

Path("docker-compose.node.yml").write_text('''services:\n  marzban-node:\n    image: ${MARZBAN_NODE_IMAGE:?MARZBAN_NODE_IMAGE is required}\n    restart: unless-stopped\n    network_mode: host\n    command: ["python", "-m", "node_runtime.main"]\n    environment:\n      NODE_RUNTIME_VERSION: ${NODE_RUNTIME_VERSION:?NODE_RUNTIME_VERSION is required}\n      NODE_RUNTIME_PORT: ${NODE_RUNTIME_PORT:-62050}\n      XRAY_API_PORT: ${XRAY_API_PORT:-62051}\n      EVENT_MAX_ROWS: ${EVENT_MAX_ROWS:-20000}\n      SSL_CLIENT_CERT_FILE: /var/lib/marzban-node/panel-client.crt\n      SSL_CERT_FILE: /var/lib/marzban-node/ssl_cert.pem\n      SSL_KEY_FILE: /var/lib/marzban-node/ssl_key.pem\n      EVENT_DB_PATH: /var/lib/marzban-node/events.sqlite3\n    volumes:\n      - /var/lib/marzban-node:/var/lib/marzban-node\n    healthcheck:\n      test:\n        - CMD\n        - python\n        - -c\n        - >-\n          import os,socket; s=socket.create_connection(("127.0.0.1", int(os.getenv("NODE_RUNTIME_PORT", "62050"))), 2); s.close()\n      start_period: 5s\n      interval: 10s\n      timeout: 3s\n      retries: 6\n''', encoding="utf-8")

Path("tests/test_v102_node_deployment.py").write_text('''from pathlib import Path\n\nimport yaml\n\n\ndef test_node_compose_uses_same_release_image_without_database():\n    compose_text = Path("docker-compose.node.yml").read_text(encoding="utf-8")\n    data = yaml.safe_load(compose_text)\n    assert set(data["services"]) == {"marzban-node"}\n    service = data["services"]["marzban-node"]\n    assert service["image"].startswith("${MARZBAN_NODE_IMAGE")\n    assert service["command"] == ["python", "-m", "node_runtime.main"]\n    assert service["network_mode"] == "host"\n    assert service["environment"]["SSL_CLIENT_CERT_FILE"] == "/var/lib/marzban-node/panel-client.crt"\n    assert service["environment"]["EVENT_DB_PATH"] == "/var/lib/marzban-node/events.sqlite3"\n    assert service["volumes"] == ["/var/lib/marzban-node:/var/lib/marzban-node"]\n    lowered = compose_text.lower()\n    assert "mysql" not in lowered\n    assert "sqlalchemy" not in lowered\n    assert "panel-client.key" not in lowered\n    assert "node_runtime.main" in compose_text\n\n\ndef test_node_installer_is_release_verified_and_keeps_panel_private_key_off_node():\n    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")\n    assert 'NODE_APP_DIR="$INSTALL_DIR/$NODE_APP_NAME"' in installer\n    assert 'NODE_DATA_DIR="/var/lib/$NODE_APP_NAME"' in installer\n    assert 'NODE_CLIENT_CERT_FILE="$NODE_DATA_DIR/panel-client.crt"' in installer\n    assert 'MARZBAN_NODE_COMPOSE_PATH="${MARZBAN_NODE_COMPOSE_PATH:-docker-compose.node.yml}"' in installer\n    assert 'node_source_supports_runtime "$requested_version"' in installer\n    assert 'ensure_marzban_image "$requested_version"' in installer\n    assert 'node_runtime/main.py' in installer\n    assert 'openssl x509 -in "$path" -noout' in installer\n    assert 'install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"' in installer\n    assert 'verify_node_version_integrity "$requested_version"' in installer\n    assert 'release_commit_for_version "$expected_version"' in installer\n    assert 'org.opencontainers.image.revision' in installer\n    assert 'Built-in Node deployment accepts published release versions only.' in installer\n    assert 'marzban node <install|update|status|logs>' in installer\n    assert 'shift; node_command "$@";;' in installer\n    assert "panel-client.key" not in installer\n    assert "NODE_CLIENT_KEY" not in installer\n\n\ndef test_node_install_requires_explicit_panel_certificate_and_separate_ports():\n    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")\n    assert '--client-cert-file' in installer\n    assert 'Node service and Xray API ports must differ.' in installer\n    assert '--service-port' in installer\n    assert '--api-port' in installer\n    assert '--event-max-rows' in installer\n    assert 'node_validate_event_rows' in installer\n''', encoding="utf-8")

replace_once(
    ".github/workflows/v1.0.2-checkpoints.yml",
    '''          docker compose -f docker-compose.yml --profile tools config --services | grep -qx phpmyadmin\n''',
    '''          docker compose -f docker-compose.yml --profile tools config --services | grep -qx phpmyadmin\n      - name: Built-in Node deployment contract\n        env:\n          MARZBAN_NODE_IMAGE: ghcr.io/smorad3363/marzban-v1:v1.0.1\n          NODE_RUNTIME_VERSION: v1.0.1\n        run: |\n          bash tests/test_installer_v1_contract.sh\n          docker compose -f docker-compose.node.yml config > /tmp/node-compose.yml\n          test "$(docker compose -f docker-compose.node.yml config --services)" = "marzban-node"\n          grep -F 'command:' /tmp/node-compose.yml >/dev/null\n          grep -F 'node_runtime.main' docker-compose.node.yml >/dev/null\n          grep -F 'SSL_CLIENT_CERT_FILE: /var/lib/marzban-node/panel-client.crt' /tmp/node-compose.yml >/dev/null\n          if grep -Eiq 'mysql|sqlalchemy' /tmp/node-compose.yml; then\n            echo 'Node compose must not contain database services or SQLAlchemy configuration' >&2\n            exit 1\n          fi\n''',
)
