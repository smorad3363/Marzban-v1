from pathlib import Path

SCRIPT = Path("scripts/marzban.sh")
TEST = Path("tests/test_v102_node_deployment.py")

script = SCRIPT.read_text(encoding="utf-8")

old_helper = '''node_validate_client_cert() {
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
'''

new_helper = '''node_validate_client_cert() {
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

NODE_INTERACTIVE_CERT_FILE=""

node_prompt_client_cert() {
    local temp_file line found_begin="false" found_end="false" line_count=0
    temp_file=$(mktemp /tmp/marzban-node-cert.XXXXXXXX)
    chmod 600 "$temp_file"

    colorized_echo blue "Paste the Marzban Node certificate from the Master panel."
    colorized_echo yellow "Paste the full PEM block including BEGIN/END CERTIFICATE lines. Input finishes automatically after END CERTIFICATE."

    while IFS= read -r line; do
        line="${line%$'\\r'}"
        if [ "$found_begin" = "false" ]; then
            [ "$line" = "-----BEGIN CERTIFICATE-----" ] || continue
            found_begin="true"
        fi
        printf '%s\\n' "$line" >> "$temp_file"
        line_count=$((line_count + 1))
        if [ "$line" = "-----END CERTIFICATE-----" ]; then
            found_end="true"
            break
        fi
        if [ "$line_count" -ge 256 ]; then
            break
        fi
    done

    if [ "$found_begin" != "true" ] || [ "$found_end" != "true" ]; then
        rm -f "$temp_file"
        colorized_echo red "Certificate paste was incomplete. Paste the full certificate from BEGIN CERTIFICATE through END CERTIFICATE."
        return 1
    fi
    if ! openssl x509 -in "$temp_file" -noout >/dev/null 2>&1; then
        rm -f "$temp_file"
        colorized_echo red "The pasted certificate is not a valid X.509 PEM certificate."
        return 1
    fi

    NODE_INTERACTIVE_CERT_FILE="$temp_file"
}

node_source_ref_path() {
'''

assert script.count(old_helper) == 1, "node certificate helper context changed"
script = script.replace(old_helper, new_helper)

old_install_head = '''node_install_command() {
    local requested_version="latest"
    local client_cert_file=""
    local service_port="62050"
    local api_port="62051"
    local event_max_rows="20000"
'''
new_install_head = '''node_install_command() {
    local requested_version="latest"
    local client_cert_file=""
    local service_port="62050"
    local api_port="62051"
    local event_max_rows="20000"
    NODE_INTERACTIVE_CERT_FILE=""
'''
assert script.count(old_install_head) == 1, "node install header context changed"
script = script.replace(old_install_head, new_install_head)

old_help = 'echo "Usage: marzban node install [--version VERSION] --client-cert-file PATH [--service-port PORT] [--api-port PORT] [--event-max-rows ROWS]"'
new_help = 'echo "Usage: marzban node install [--version VERSION] [--client-cert-file PATH] [--service-port PORT] [--api-port PORT] [--event-max-rows ROWS]"'
assert script.count(old_help) == 1, "node install help context changed"
script = script.replace(old_help, new_help)

old_validation = '''    node_validate_event_rows "$event_max_rows" || return 1
    node_validate_client_cert "$client_cert_file" || return 1
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    ensure_marzban_image "$requested_version" || return 1

    install -d -m 700 "$NODE_APP_DIR" "$NODE_DATA_DIR"
    install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"
'''
new_validation = '''    node_validate_event_rows "$event_max_rows" || return 1
    if [ -n "$client_cert_file" ]; then
        node_validate_client_cert "$client_cert_file" || return 1
    fi
    if ! node_source_supports_runtime "$requested_version"; then
        colorized_echo red "Release ${requested_version} does not contain the built-in Node Runtime V2."
        return 1
    fi
    ensure_marzban_image "$requested_version" || return 1

    if [ -z "$client_cert_file" ]; then
        node_prompt_client_cert || return 1
        client_cert_file="$NODE_INTERACTIVE_CERT_FILE"
    fi

    install -d -m 700 "$NODE_APP_DIR" "$NODE_DATA_DIR"
    if ! install -m 600 "$client_cert_file" "$NODE_CLIENT_CERT_FILE"; then
        [ -n "$NODE_INTERACTIVE_CERT_FILE" ] && rm -f "$NODE_INTERACTIVE_CERT_FILE"
        NODE_INTERACTIVE_CERT_FILE=""
        return 1
    fi
    if [ -n "$NODE_INTERACTIVE_CERT_FILE" ]; then
        rm -f "$NODE_INTERACTIVE_CERT_FILE"
        NODE_INTERACTIVE_CERT_FILE=""
    fi
'''
assert script.count(old_validation) == 1, "node certificate install context changed"
script = script.replace(old_validation, new_validation)

SCRIPT.write_text(script, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
assert "import subprocess\n" not in test
assert "import shlex\n" not in test

test = test.replace(
    "from pathlib import Path\n\nimport yaml\n",
    "from pathlib import Path\nimport shlex\nimport subprocess\n\nimport yaml\n",
    1,
)

old_test = '''def test_node_install_requires_explicit_panel_certificate_and_separate_ports():
    installer = Path("scripts/marzban.sh").read_text(encoding="utf-8")
    assert '--client-cert-file' in installer
    assert 'Node service and Xray API ports must differ.' in installer
    assert '--service-port' in installer
    assert '--api-port' in installer
    assert '--event-max-rows' in installer
    assert 'node_validate_event_rows' in installer
'''

new_test = '''def test_node_install_supports_interactive_certificate_and_explicit_file():
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
    script = f'''\nsource scripts/marzban.sh\nNODE_INTERACTIVE_CERT_FILE=\"\"\nnode_prompt_client_cert < {shlex.quote(str(cert))}\ntest -f \"$NODE_INTERACTIVE_CERT_FILE\"\nopenssl x509 -in \"$NODE_INTERACTIVE_CERT_FILE\" -noout >/dev/null\nrm -f \"$NODE_INTERACTIVE_CERT_FILE\"\n'''
    subprocess.run(["bash", "-c", script], check=True)


def test_node_interactive_certificate_prompt_rejects_incomplete_paste():
    script = '''\nsource scripts/marzban.sh\nNODE_INTERACTIVE_CERT_FILE=\"\"\nnode_prompt_client_cert\n'''
    result = subprocess.run(
        ["bash", "-c", script],
        input="-----BEGIN CERTIFICATE-----\\nnot-a-complete-certificate\\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode != 0
    assert "Certificate paste was incomplete" in result.stdout
'''

assert test.count(old_test) == 1, "node deployment test context changed"
test = test.replace(old_test, new_test)
TEST.write_text(test, encoding="utf-8")
