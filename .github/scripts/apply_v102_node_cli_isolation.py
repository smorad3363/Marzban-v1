from pathlib import Path

script = Path("scripts/marzban.sh")
text = script.read_text(encoding="utf-8")

old = 'NODE_CLI_VERSION_FILE="$NODE_APP_DIR/.cli-version"\nLAST_XRAY_CORES=10\n'
new = 'NODE_CLI_VERSION_FILE="$NODE_APP_DIR/.cli-version"\nNODE_SCRIPT_PATH="/usr/local/bin/marzban-node"\nLAST_XRAY_CORES=10\n'
if text.count(old) != 1:
    raise SystemExit(f"node script constant context mismatch: {text.count(old)}")
text = text.replace(old, new, 1)

marker = "node_source_supports_runtime() {\n"
helper = r'''install_node_script_from_repo() {
    local requested_version="$1"
    local ref_path script_url temp_script
    ref_path=$(node_source_ref_path "$requested_version")
    script_url="https://raw.githubusercontent.com/${MARZBAN_GITHUB_REPO}/${ref_path}/${MARZBAN_SCRIPTS_PATH}"
    temp_script=$(mktemp)
    if ! github_download -fsSL "$script_url" -o "$temp_script"; then
        rm -f "$temp_script"
        colorized_echo red "Could not download Node CLI from ${requested_version}."
        return 1
    fi
    if ! bash -n "$temp_script"; then
        rm -f "$temp_script"
        colorized_echo red "Downloaded Node CLI failed syntax validation."
        return 1
    fi
    if ! install -m 755 "$temp_script" "$NODE_SCRIPT_PATH"; then
        rm -f "$temp_script"
        return 1
    fi
    # A co-located panel owns /usr/local/bin/marzban and its CLI metadata.
    # Never replace either from a Node install/update. Node-only hosts keep the
    # familiar `marzban node ...` command in addition to `marzban-node node ...`.
    if ! is_marzban_installed; then
        if ! install -m 755 "$temp_script" /usr/local/bin/marzban; then
            rm -f "$temp_script"
            return 1
        fi
    fi
    rm -f "$temp_script"
    printf '%s\n' "$requested_version" > "$NODE_CLI_VERSION_FILE"
    chmod 644 "$NODE_CLI_VERSION_FILE"
    colorized_echo green "Node CLI installed at $NODE_SCRIPT_PATH"
}

'''
if text.count(marker) != 1:
    raise SystemExit(f"node helper insertion context mismatch: {text.count(marker)}")
text = text.replace(marker, helper + marker, 1)

old_call = '    install_marzban_script_from_repo "$requested_version" || return 1\n'
if text.count(old_call) != 2:
    raise SystemExit(f"expected two Node generic CLI calls, found {text.count(old_call)}")
text = text.replace(old_call, '    install_node_script_from_repo "$requested_version" || return 1\n')
script.write_text(text, encoding="utf-8")

tests = Path("tests/test_v102_node_deployment.py")
test_text = tests.read_text(encoding="utf-8")
anchor = '''    assert 'shift; node_command "$@";;' in installer\n    assert "panel-client.key" not in installer\n'''
replacement = '''    assert 'shift; node_command "$@";;' in installer\n    assert 'NODE_SCRIPT_PATH="/usr/local/bin/marzban-node"' in installer\n    node_section = installer.split("node_is_installed()", 1)[1].split("rollback_command()", 1)[0]\n    assert 'install_node_script_from_repo "$requested_version"' in node_section\n    assert 'install_marzban_script_from_repo' not in node_section\n    assert 'if ! is_marzban_installed; then' in node_section\n    assert 'install -m 755 "$temp_script" /usr/local/bin/marzban' in node_section\n    assert "panel-client.key" not in installer\n'''
if test_text.count(anchor) != 1:
    raise SystemExit(f"deployment test context mismatch: {test_text.count(anchor)}")
tests.write_text(test_text.replace(anchor, replacement, 1), encoding="utf-8")
