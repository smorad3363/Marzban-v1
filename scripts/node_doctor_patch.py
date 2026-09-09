from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


installer = "scripts/marzban.sh"
doctor_code = r'''
node_doctor_pass() {
    NODE_DOCTOR_PASSED=$((NODE_DOCTOR_PASSED + 1))
    colorized_echo green "[PASS] $1"
}

node_doctor_warn() {
    NODE_DOCTOR_WARNINGS=$((NODE_DOCTOR_WARNINGS + 1))
    colorized_echo yellow "[WARN] $1"
}

node_doctor_fail() {
    NODE_DOCTOR_FAILURES=$((NODE_DOCTOR_FAILURES + 1))
    colorized_echo red "[FAIL] $1"
}

node_doctor_detect_compose() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        COMPOSE='docker compose'
        return 0
    fi
    if command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
        COMPOSE='docker-compose'
        return 0
    fi
    return 1
}

node_doctor_check_private_mode() {
    local path="$1"
    local label="$2"
    local mode=""
    mode=$(stat -c '%a' "$path" 2>/dev/null || true)
    if [ -z "$mode" ]; then
        node_doctor_warn "$label permissions could not be inspected."
        return 0
    fi
    if [ "${mode: -2}" = "00" ]; then
        node_doctor_pass "$label is not readable or writable by group/others (mode $mode)."
    else
        node_doctor_fail "$label is exposed to group/others (mode $mode)."
    fi
}

node_doctor_check_expected_mode() {
    local path="$1"
    local label="$2"
    local mode=""
    mode=$(stat -c '%a' "$path" 2>/dev/null || true)
    if [ -z "$mode" ]; then
        node_doctor_warn "$label permissions could not be inspected."
    elif [ "$mode" = "600" ] || [ "$mode" = "400" ]; then
        node_doctor_pass "$label permissions are restricted (mode $mode)."
    else
        node_doctor_warn "$label uses mode $mode; installer-managed files normally use 600."
    fi
}

node_doctor_command() {
    if [ "$#" -gt 0 ]; then
        if [ "$#" -eq 1 ] && { [ "$1" = "-h" ] || [ "$1" = "--help" ]; }; then
            echo "Usage: marzban node doctor"
            echo "Runs local, non-mutating Node readiness and integrity diagnostics."
            return 0
        fi
        colorized_echo red "Usage: marzban node doctor"
        return 1
    fi

    check_running_as_root
    NODE_DOCTOR_PASSED=0
    NODE_DOCTOR_WARNINGS=0
    NODE_DOCTOR_FAILURES=0

    local server_cert_file="$NODE_DATA_DIR/ssl_cert.pem"
    local server_key_file="$NODE_DATA_DIR/ssl_key.pem"
    local event_db_file="$NODE_DATA_DIR/events.sqlite3"
    local service_port=""
    local api_port=""
    local event_max_rows=""
    local configured_image=""
    local runtime_version=""
    local cli_version=""
    local stored_revision=""
    local container_id=""
    local state=""
    local health=""
    local running_image=""
    local image_id=""
    local running_revision=""
    local compose_ready="false"

    colorized_echo cyan "Marzban Node doctor (local diagnostics; no configuration is changed)"

    if [ -f "$NODE_COMPOSE_FILE" ]; then
        node_doctor_pass "Node compose file exists: $NODE_COMPOSE_FILE"
        node_doctor_check_expected_mode "$NODE_COMPOSE_FILE" "Node compose file"
    else
        node_doctor_fail "Node compose file is missing: $NODE_COMPOSE_FILE"
    fi

    if [ -f "$NODE_ENV_FILE" ]; then
        node_doctor_pass "Node environment file exists: $NODE_ENV_FILE"
        node_doctor_check_private_mode "$NODE_ENV_FILE" "Node environment file"
    else
        node_doctor_fail "Node environment file is missing: $NODE_ENV_FILE"
    fi

    if command -v openssl >/dev/null 2>&1; then
        node_doctor_pass "OpenSSL is available."
        if [ -f "$NODE_CLIENT_CERT_FILE" ]; then
            if openssl x509 -in "$NODE_CLIENT_CERT_FILE" -noout >/dev/null 2>&1; then
                node_doctor_pass "Stored panel client certificate is valid X.509 PEM."
                if openssl x509 -checkend 0 -noout -in "$NODE_CLIENT_CERT_FILE" >/dev/null 2>&1; then
                    node_doctor_pass "Stored panel client certificate is not expired."
                    if ! openssl x509 -checkend 604800 -noout -in "$NODE_CLIENT_CERT_FILE" >/dev/null 2>&1; then
                        node_doctor_warn "Stored panel client certificate expires within 7 days."
                    fi
                else
                    node_doctor_fail "Stored panel client certificate is expired."
                fi
            else
                node_doctor_fail "Stored panel client certificate is not valid X.509 PEM."
            fi
            node_doctor_check_expected_mode "$NODE_CLIENT_CERT_FILE" "Stored panel client certificate"
        else
            node_doctor_fail "Stored panel client certificate is missing: $NODE_CLIENT_CERT_FILE"
        fi

        if [ -f "$server_cert_file" ]; then
            if openssl x509 -in "$server_cert_file" -noout >/dev/null 2>&1; then
                node_doctor_pass "Node server certificate is valid X.509 PEM."
                if openssl x509 -checkend 0 -noout -in "$server_cert_file" >/dev/null 2>&1; then
                    node_doctor_pass "Node server certificate is not expired."
                else
                    node_doctor_fail "Node server certificate is expired."
                fi
            else
                node_doctor_fail "Node server certificate is not valid X.509 PEM."
            fi
        else
            node_doctor_fail "Node server certificate is missing: $server_cert_file"
        fi

        if [ -f "$server_key_file" ]; then
            if openssl pkey -in "$server_key_file" -check -noout >/dev/null 2>&1; then
                node_doctor_pass "Node server private key is valid."
            else
                node_doctor_fail "Node server private key is invalid."
            fi
            node_doctor_check_private_mode "$server_key_file" "Node server private key"
        else
            node_doctor_fail "Node server private key is missing: $server_key_file"
        fi
    else
        node_doctor_fail "OpenSSL is unavailable; certificate diagnostics cannot run."
    fi

    if [ -f "$event_db_file" ]; then
        node_doctor_pass "Node event spool exists: $event_db_file"
    else
        node_doctor_warn "Node event spool is not present yet: $event_db_file"
    fi

    if [ -f "$NODE_ENV_FILE" ]; then
        service_port=$(node_env_value NODE_RUNTIME_PORT 62050)
        api_port=$(node_env_value XRAY_API_PORT 62051)
        event_max_rows=$(node_env_value EVENT_MAX_ROWS 20000)
        configured_image=$(node_env_value MARZBAN_NODE_IMAGE "")
        runtime_version=$(node_env_value NODE_RUNTIME_VERSION "")

        if node_validate_port "$service_port" "NODE_RUNTIME_PORT" >/dev/null 2>&1; then
            node_doctor_pass "Node service port is valid: $service_port"
        else
            node_doctor_fail "Node service port is invalid."
        fi
        if node_validate_port "$api_port" "XRAY_API_PORT" >/dev/null 2>&1; then
            node_doctor_pass "Xray API port is valid: $api_port"
        else
            node_doctor_fail "Xray API port is invalid."
        fi
        if [ "$service_port" = "$api_port" ]; then
            node_doctor_fail "Node service and Xray API ports must differ."
        else
            node_doctor_pass "Node service and Xray API ports are distinct."
        fi
        if node_validate_event_rows "$event_max_rows" >/dev/null 2>&1; then
            node_doctor_pass "Event retention row limit is valid: $event_max_rows"
        else
            node_doctor_fail "Event retention row limit is invalid."
        fi
        if [ -n "$configured_image" ]; then
            node_doctor_pass "Configured Node image is present: $configured_image"
        else
            node_doctor_fail "MARZBAN_NODE_IMAGE is missing from the Node environment file."
        fi
        if [ -n "$runtime_version" ]; then
            node_doctor_pass "Configured runtime version is present: $runtime_version"
        else
            node_doctor_fail "NODE_RUNTIME_VERSION is missing from the Node environment file."
        fi
    fi

    if [ -f "$NODE_CLI_VERSION_FILE" ]; then
        cli_version=$(tr -d '[:space:]' < "$NODE_CLI_VERSION_FILE")
        if [ -n "$cli_version" ]; then
            node_doctor_pass "Node CLI version marker is present: $cli_version"
            if [ -n "$runtime_version" ] && [ "$cli_version" != "$runtime_version" ]; then
                node_doctor_fail "Node CLI version ($cli_version) differs from runtime version ($runtime_version)."
            fi
        else
            node_doctor_warn "Node CLI version marker is empty."
        fi
    else
        node_doctor_warn "Node CLI version marker is missing: $NODE_CLI_VERSION_FILE"
    fi

    if [ -f "$NODE_RELEASE_REVISION_FILE" ]; then
        stored_revision=$(tr -d '[:space:]' < "$NODE_RELEASE_REVISION_FILE")
        if [[ "$stored_revision" =~ ^[0-9a-f]{40}$ ]]; then
            node_doctor_pass "Stored release revision marker is valid."
        else
            node_doctor_fail "Stored release revision marker is invalid."
        fi
    else
        node_doctor_warn "Stored release revision marker is missing: $NODE_RELEASE_REVISION_FILE"
    fi

    if command -v docker >/dev/null 2>&1; then
        node_doctor_pass "Docker CLI is available."
    else
        node_doctor_fail "Docker CLI is unavailable."
    fi

    if node_doctor_detect_compose; then
        compose_ready="true"
        node_doctor_pass "Docker Compose is available."
        if [ -f "$NODE_COMPOSE_FILE" ] && [ -f "$NODE_ENV_FILE" ]; then
            if node_compose config >/dev/null 2>&1; then
                node_doctor_pass "Node compose configuration renders successfully."
            else
                node_doctor_fail "Node compose configuration does not render successfully."
            fi
        fi
    else
        node_doctor_fail "Docker Compose is unavailable."
    fi

    if [ "$compose_ready" = "true" ] && [ -f "$NODE_COMPOSE_FILE" ] && [ -f "$NODE_ENV_FILE" ]; then
        container_id=$(node_service_container 2>/dev/null || true)
        if [ -z "$container_id" ]; then
            node_doctor_fail "Marzban Node container is not running."
        else
            node_doctor_pass "Marzban Node container exists."
            state=$(docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
            health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container_id" 2>/dev/null || true)
            if [ "$state" = "running" ]; then
                node_doctor_pass "Marzban Node container state is running."
            else
                node_doctor_fail "Marzban Node container state is ${state:-unknown}."
            fi
            if [ "$health" = "healthy" ]; then
                node_doctor_pass "Marzban Node container health is healthy."
            elif [ -z "$health" ]; then
                node_doctor_warn "Marzban Node container health status is unavailable."
            else
                node_doctor_fail "Marzban Node container health is $health."
            fi

            running_image=$(docker inspect --format '{{.Config.Image}}' "$container_id" 2>/dev/null || true)
            if [ -n "$configured_image" ] && [ "$running_image" = "$configured_image" ]; then
                node_doctor_pass "Running Node image matches configured image."
            elif [ -n "$configured_image" ]; then
                node_doctor_fail "Running Node image (${running_image:-unavailable}) differs from configured image ($configured_image)."
            else
                node_doctor_warn "Running image comparison was skipped because the configured image is unavailable."
            fi

            image_id=$(docker inspect --format '{{.Image}}' "$container_id" 2>/dev/null || true)
            if [ -n "$image_id" ]; then
                running_revision=$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image_id" 2>/dev/null || true)
            fi
            if [ -n "$stored_revision" ] && [ -n "$running_revision" ]; then
                if [ "$stored_revision" = "$running_revision" ]; then
                    node_doctor_pass "Running image source revision matches the stored release revision."
                else
                    node_doctor_fail "Running image source revision differs from the stored release revision."
                fi
            elif [ -n "$stored_revision" ]; then
                node_doctor_warn "Running image source revision label is unavailable."
            fi
        fi
    fi

    echo "Node doctor summary: ${NODE_DOCTOR_PASSED} passed, ${NODE_DOCTOR_WARNINGS} warnings, ${NODE_DOCTOR_FAILURES} failures."
    [ "$NODE_DOCTOR_FAILURES" -eq 0 ]
}

'''
replace_once(installer, "\nnode_logs_command() {", "\n" + doctor_code + "node_logs_command() {")
replace_once(
    installer,
    '''        status) node_status_command "$@" ;;
        logs) node_logs_command "$@" ;;
        help|-h|--help)
            echo "Usage: marzban node <install|update|status|logs> [options]"
            ;;
        *)
            colorized_echo red "Unknown node command: $action"
            echo "Usage: marzban node <install|update|status|logs> [options]"''',
    '''        status) node_status_command "$@" ;;
        doctor) node_doctor_command "$@" ;;
        logs) node_logs_command "$@" ;;
        help|-h|--help)
            echo "Usage: marzban node <install|update|status|doctor|logs> [options]"
            ;;
        *)
            colorized_echo red "Unknown node command: $action"
            echo "Usage: marzban node <install|update|status|doctor|logs> [options]"''',
)


test_path = Path("tests/test_node_deployment_contract.py")
test_text = test_path.read_text(encoding="utf-8")
test_text = test_text.replace(
    "assert 'marzban node <install|update|status|logs>' in installer",
    "assert 'marzban node <install|update|status|doctor|logs>' in installer",
    1,
)
if "test_node_doctor_reports_local_readiness_without_leaking_env" not in test_text:
    test_text += r'''


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

    shell = f'''source scripts/marzban.sh
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
'''
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
'''

test_path.write_text(test_text, encoding="utf-8")


docs = Path("docs/NODE_OPERATIONS_V2_FA.md")
docs.write_text(
    '''# Node Operations V2 — راهنمای عملیات و عیب‌یابی\n\n## نمای یکپارچه\n\nNode Operations V2 وضعیت عملیاتی، ترافیک لحظه‌ای، میانگین‌های پایدار ۱ و ۲۴ ساعت، تاریخچه ترافیک و رخدادهای تشخیصی sanitize‌شده را در همان workspace مدیریت Node نمایش می‌دهد. مسیر قدیمی API مربوط به `/api/nodes/usage` برای سازگاری باقی مانده است، اما UI جداگانه Nodes Usage دیگر در ناوبری نمایش داده نمی‌شود.\n\nAPIهای افزایشی این قابلیت:\n\n- `GET /api/nodes/operations` برای summary همه Nodeها؛\n- `GET /api/node/{node_id}/operations/history` برای تاریخچه persisted و bounded؛\n- `GET /api/node/{node_id}/events` برای timeline صفحه‌بندی‌شده و sanitize‌شده.\n\nجمع‌آوری ترافیک Xray مسیر جدیدی ایجاد نمی‌کند: همان collector موجود که reset-counter را برای accounting می‌خواند، نمونه موفق را برای telemetry پایدار نیز ثبت می‌کند.\n\n## عیب‌یابی Node نصب‌شده\n\nروی سرور Node اجرا کنید:\n\n```bash\nsudo marzban node doctor\n```\n\nیا در hostهایی که CLI اختصاصی Node را استفاده می‌کنند:\n\n```bash\nsudo marzban-node node doctor\n```\n\n`doctor` فقط بررسی محلی انجام می‌دهد و configuration را تغییر نمی‌دهد. موارد اصلی بررسی‌شده:\n\n- وجود و permission فایل‌های compose و `.env`؛\n- اعتبار و تاریخ انقضای certificate پنل که روی Node ذخیره شده؛\n- اعتبار certificate و private key خود Node و محدود بودن permission کلید؛\n- صحت portها و `EVENT_MAX_ROWS`؛\n- render شدن Docker Compose؛\n- running/health وضعیت container؛\n- تطابق image در حال اجرا با image تنظیم‌شده؛\n- تطابق OCI source revision image با revision ثبت‌شده هنگام نصب/آپدیت.\n\nخروجی از `[PASS]`، `[WARN]` و `[FAIL]` استفاده می‌کند. warning به‌تنهایی exit code را fail نمی‌کند؛ وجود failure باعث exit code غیرصفر می‌شود. محتوای PEM، private key یا `.env` در خروجی چاپ نمی‌شود.\n\n## نکات mTLS\n\nمالکیت credentialها تغییر نکرده است: Node فقط certificate پنل موردنیاز قرارداد موجود را دریافت می‌کند و private key پنل روی Node کپی نمی‌شود. certificate/key سرور Node در `/var/lib/marzban-node/` متعلق به runtime Node هستند.\n\nاگر doctor خطای certificate بدهد، فایل‌ها را دستی از پنل دیگری جایگزین نکنید. ابتدا علت provisioning/expiry را بررسی کنید و سپس از مسیر نصب/آپدیت مستند Node استفاده کنید.\n\n## رخدادها و retention\n\nرخدادهای runtime و reconnect قبل از نمایش sanitize می‌شوند. spool محلی و storage سمت پنل bounded هستند؛ telemetry یا persistence failure نباید مسیر accounting یا reconnect موجود را متوقف کند.\n''',
    encoding="utf-8",
)
