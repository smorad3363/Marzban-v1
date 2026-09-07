#!/usr/bin/env bash
set -Eeuo pipefail

image="${1:-marzban-v1:ci}"
runtime_port="${NODE_E2E_RUNTIME_PORT:-62150}"
api_port="${NODE_E2E_API_PORT:-62151}"
workdir="$(mktemp -d /tmp/marzban-node-e2e.XXXXXXXX)"
node_name="marzban-node-e2e-${GITHUB_RUN_ID:-$$}-${GITHUB_RUN_ATTEMPT:-1}"

cleanup() {
    status=$?
    if [ "${status}" -ne 0 ]; then
        echo "Node E2E failed; runtime logs follow:" >&2
        docker logs "${node_name}" >&2 2>/dev/null || true
    fi
    docker rm --force "${node_name}" >/dev/null 2>&1 || true
    rm -rf -- "${workdir}"
}
trap cleanup EXIT

mkdir -p "${workdir}/node-data"

# The panel keeps the private key. The Node receives only the public client
# certificate and uses it as its trust anchor for strict mutual TLS.
openssl req \
    -x509 \
    -newkey rsa:2048 \
    -nodes \
    -days 1 \
    -subj "/CN=Marzban Panel E2E" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,digitalSignature,keyCertSign" \
    -addext "extendedKeyUsage=clientAuth" \
    -keyout "${workdir}/panel-client.key" \
    -out "${workdir}/panel-client.crt" \
    >/dev/null 2>&1

chmod 600 "${workdir}/panel-client.key"
install -m 600 "${workdir}/panel-client.crt" "${workdir}/node-data/panel-client.crt"
test ! -e "${workdir}/node-data/panel-client.key"

docker run --detach \
    --name "${node_name}" \
    --network host \
    --volume "${workdir}/node-data:/var/lib/marzban-node" \
    --env SSL_CLIENT_CERT_FILE=/var/lib/marzban-node/panel-client.crt \
    --env NODE_RUNTIME_HOST=127.0.0.1 \
    --env NODE_RUNTIME_PORT="${runtime_port}" \
    --env XRAY_API_HOST=127.0.0.1 \
    --env XRAY_API_PORT="${api_port}" \
    --env NODE_RUNTIME_VERSION=e2e \
    --entrypoint python \
    "${image}" \
    -m node_runtime.main \
    >/dev/null

handshake_file="${workdir}/handshake.json"
for _attempt in $(seq 1 60); do
    if curl \
        --silent \
        --show-error \
        --fail \
        --insecure \
        --cert "${workdir}/panel-client.crt" \
        --key "${workdir}/panel-client.key" \
        --header 'Content-Type: application/json' \
        --data '{}' \
        "https://127.0.0.1:${runtime_port}/v2/handshake" \
        >"${handshake_file}" 2>/dev/null; then
        break
    fi
    sleep 0.5
done

test -s "${handshake_file}"
python - "${handshake_file}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

assert payload["protocol"] == "marzban-node-v2"
assert payload["protocol_version"] == 2
assert {"control_v1", "event_ack_v1", "client_ip_direct_v1"}.issubset(payload["capabilities"])
PY

# Strict mTLS must reject a panel connection that does not present the client cert.
if curl \
    --silent \
    --show-error \
    --fail \
    --insecure \
    --header 'Content-Type: application/json' \
    --data '{}' \
    "https://127.0.0.1:${runtime_port}/v2/handshake" \
    >/dev/null 2>&1; then
    echo "Node runtime accepted a TLS connection without the panel client certificate." >&2
    exit 1
fi

# Exercise the real panel-side V2 client against the real TLS Node runtime.
docker run --rm --interactive \
    --network host \
    --volume "${workdir}:/e2e:ro" \
    --env SQLALCHEMY_DATABASE_URL=mysql+pymysql://probe:probe@127.0.0.1/probe \
    --env NODE_E2E_RUNTIME_PORT="${runtime_port}" \
    --env NODE_E2E_API_PORT="${api_port}" \
    --entrypoint python \
    "${image}" - <<'PY'
import os
from pathlib import Path

from app.xray.node import V2ReSTXRayNode

cert = Path("/e2e/panel-client.crt").read_text(encoding="utf-8")
key = Path("/e2e/panel-client.key").read_text(encoding="utf-8")
node = V2ReSTXRayNode(
    address="127.0.0.1",
    port=int(os.environ["NODE_E2E_RUNTIME_PORT"]),
    api_port=int(os.environ["NODE_E2E_API_PORT"]),
    ssl_key=key,
    ssl_cert=cert,
)

assert node.probe_runtime(), "Panel could not complete the v2 mTLS handshake"
assert node.runtime_handshake is not None
assert node.runtime_handshake.protocol_version == 2
assert {"control_v1", "event_ack_v1", "client_ip_direct_v1"}.issubset(node.capabilities)

node.connect()
assert node.connected, "Panel /connect + /ping path did not become healthy"
assert node.get_version(), "Node status did not expose the Xray runtime version"
node.disconnect()
assert not node.connected
PY

test -s "${workdir}/node-data/ssl_cert.pem"
test -s "${workdir}/node-data/ssl_key.pem"
test -s "${workdir}/node-data/events.sqlite3"
test ! -e "${workdir}/node-data/panel-client.key"

echo "PANEL_NODE_MTLS_E2E_PASS"
