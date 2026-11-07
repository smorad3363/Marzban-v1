"""Disposable image lab: real mTLS, both SS formats, data, UDP and idle cleanup."""
from __future__ import annotations

import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import threading
import time

from app.utils.shadowsocks2022 import METHOD, client_settings, generate_key, subscription_settings
from app.xray.node import V2ReSTXRayNode


PAYLOAD = b"bounded-node-memory-e2e\n" * 24000


def free_port():
    for _ in range(100):
        with socket.socket() as tcp, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            tcp.bind(("127.0.0.1", 0))
            port = tcp.getsockname()[1]
            try:
                udp.bind(("127.0.0.1", port))
                return port
            except OSError:
                pass
    raise RuntimeError("No free TCP/UDP fixture port")


def exact(stream, size):
    result = b""
    while len(result) < size:
        part = stream.recv(size - len(result))
        if not part:
            raise RuntimeError("Unexpected fixture connection EOF")
        result += part
    return result


def socks_connect(port, destination):
    stream = socket.create_connection(("127.0.0.1", port), timeout=5)
    stream.sendall(b"\x05\x01\x00")
    assert exact(stream, 2) == b"\x05\x00"
    stream.sendall(b"\x05\x01\x00\x01" + socket.inet_aton("127.0.0.1") + struct.pack("!H", destination))
    reply = exact(stream, 4)
    assert reply[1] == 0 and reply[3] == 1, reply
    exact(stream, 6)
    return stream


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):
        pass


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while data := self.request.recv(4096):
            self.request.sendall(data)


def main():
    origin = ThreadingHTTPServer(("127.0.0.1", 0), HTTPHandler)
    echo = socketserver.ThreadingTCPServer(("127.0.0.1", 0), EchoHandler)
    echo.daemon_threads = True
    for server in (origin, echo):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("127.0.0.1", 0))
    udp.settimeout(.5)
    closed = threading.Event()

    def echo_udp():
        while not closed.is_set():
            try:
                data, peer = udp.recvfrom(65536)
                udp.sendto(data, peer)
            except socket.timeout:
                pass
            except OSError:
                return

    threading.Thread(target=echo_udp, daemon=True).start()
    cert = Path("/e2e/panel-client.crt").read_text()
    key = Path("/e2e/panel-client.key").read_text()
    node = V2ReSTXRayNode("127.0.0.1", int(os.environ["NODE_E2E_RUNTIME_PORT"]),
                        int(os.environ["NODE_E2E_API_PORT"]), key, cert)
    server_key = generate_key()
    # The same legacy credential must work unchanged on the classic inbound,
    # and through the panel's stable key mapping on the SS2022 inbound.
    account = {"password": "existing-classic-fixture-secret", "method": "chacha20-ietf-poly1305"}
    cases = [(METHOD, free_port()), ("chacha20-ietf-poly1305", free_port())]
    inbounds = []
    for method, port in cases:
        settings = {"method": method, "network": "tcp,udp",
                    "clients": [{"email": "fixture-user", **client_settings(account, method)}]}
        if method == METHOD:
            settings["password"] = server_key
            settings["clients"][0]["method"] = METHOD  # Older-panel wire regression.
        inbounds.append({"tag": f"fixture-{port}", "listen": "127.0.0.1", "port": port,
                         "protocol": "shadowsocks", "settings": settings})
    configuration = {
        "log": {"loglevel": "warning"}, "inbounds": inbounds,
        "outbounds": [{"protocol": "freedom", "settings": {
            # Only the disposable fixture permits its controlled loopback target.
            "finalRules": [{"action": "allow", "ip": ["127.0.0.1/32"]}],
        }}],
        "policy": {"levels": {"0": {"connIdle": 2, "uplinkOnly": 1, "downlinkOnly": 1,
                                        "statsUserUplink": True, "statsUserDownlink": True}}},
    }
    try:
        assert node.probe_runtime()
        node.connect()
        # This lab has no panel DB/Access Groups. Exercise the real authenticated
        # control wire; scope enforcement remains covered by backend checkpoints.
        result = node.make_request("/start", timeout=12, config=json.dumps(configuration))
        assert result["started"]
        for method, port in cases:
            mapped = subscription_settings(account, method, server_key)
            socks_port = free_port()
            client_config = {
                "log": {"loglevel": "warning"},
                "inbounds": [{"listen": "127.0.0.1", "port": socks_port, "protocol": "socks",
                              "settings": {"auth": "noauth", "udp": True}}],
                "outbounds": [{"protocol": "shadowsocks", "settings": {"servers": [{
                    "address": "127.0.0.1", "port": port,
                    "method": mapped["method"], "password": mapped["password"],
                }]}}],
            }
            client = subprocess.Popen(["/usr/local/bin/xray", "run", "-config", "stdin:"],
                                      stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, text=True)
            try:
                client.stdin.write(json.dumps(client_config))
                client.stdin.close()
                for _ in range(50):
                    try:
                        with socket.create_connection(("127.0.0.1", socks_port), timeout=.1):
                            break
                    except OSError:
                        time.sleep(.1)
                for _ in range(3):
                    with socks_connect(socks_port, origin.server_address[1]) as stream:
                        stream.sendall(b"GET /payload HTTP/1.1\r\nHost: fixture\r\nConnection: close\r\n\r\n")
                        response = http.client.HTTPResponse(stream)
                        response.begin()
                        assert response.status == 200
                        assert hashlib.sha256(response.read()).digest() == hashlib.sha256(PAYLOAD).digest()
                with socket.create_connection(("127.0.0.1", socks_port), timeout=5) as control:
                    control.sendall(b"\x05\x01\x00")
                    assert exact(control, 2) == b"\x05\x00"
                    control.sendall(b"\x05\x03\x00\x01" + b"\0" * 6)
                    reply = exact(control, 4)
                    assert reply[1] == 0 and reply[3] == 1
                    address = socket.inet_ntoa(exact(control, 4))
                    relay_port = struct.unpack("!H", exact(control, 2))[0]
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as datagram:
                        datagram.settimeout(5)
                        payload = os.urandom(512)
                        datagram.sendto(b"\0\0\0\x01" + socket.inet_aton("127.0.0.1") +
                                        struct.pack("!H", udp.getsockname()[1]) + payload,
                                        (address, relay_port))
                        received, _ = datagram.recvfrom(4096)
                        assert received[10:] == payload
                with socks_connect(socks_port, echo.server_address[1]) as stream:
                    stream.sendall(b"idle-check")
                    assert exact(stream, 10) == b"idle-check"
                    stream.settimeout(6)
                    assert stream.recv(1) == b"", "Idle connection was not released"
                print(f"NODE_MEMORY_DATA_UDP_IDLE_PASS {method}", flush=True)
            finally:
                client.terminate()
                client.wait(timeout=5)
        node.make_request("/restart", timeout=12, config=json.dumps(configuration))
        events = node.make_request("/v2/events", timeout=5, consumer_id="memory-e2e", after_id=0, limit=256)["events"]
        started = [item for item in events if item["type"] == "runtime.core.started"]
        assert started
        assert started[-1]["payload"]["metadata"]["go_memory_limit"] == "288MiB"
        assert started[-1]["payload"]["metadata"]["memory_profile"] == "balanced"
        assert node.connected and node.started
        # Leave the real core alive for the host's /proc environment check.
        # The shell EXIT trap removes the entire disposable container afterwards.
        print("NODE_MEMORY_RESTART_PASS", flush=True)
    finally:
        closed.set()
        udp.close()
        origin.shutdown()
        echo.shutdown()
        origin.server_close()
        echo.server_close()


if __name__ == "__main__":
    main()
