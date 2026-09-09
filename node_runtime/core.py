from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import threading
import time
from collections import deque
from typing import Any

from node_runtime.config import RuntimeSettings
from node_runtime.events import EventSpool


logger = logging.getLogger("marzban.node_runtime")


def prepare_xray_config(raw_config: str, peer_ip: str, settings: RuntimeSettings) -> dict[str, Any]:
    try:
        config = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to decode Xray config: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("Xray config must be a JSON object")
    api_tag = (config.get("api") or {}).get("tag")
    retained_inbounds = []
    for inbound in config.get("inbounds") or []:
        if not isinstance(inbound, dict):
            continue
        if inbound.get("protocol") == "dokodemo-door" and inbound.get("tag") == "API_INBOUND":
            continue
        if settings.inbounds and inbound.get("tag") not in settings.inbounds:
            continue
        retained_inbounds.append(inbound)
    config["inbounds"] = retained_inbounds
    routing = config.setdefault("routing", {})
    rules = routing.get("rules") or []
    if api_tag:
        rules = [rule for rule in rules if not (isinstance(rule, dict) and rule.get("outboundTag") == api_tag)]
    config["api"] = {
        "services": ["HandlerService", "StatsService", "LoggerService"],
        "tag": "API",
    }
    config["stats"] = {}
    api_inbound = {
        "listen": settings.api_host,
        "port": settings.api_port,
        "protocol": "dokodemo-door",
        "settings": {"address": "127.0.0.1"},
        "streamSettings": {
            "security": "tls",
            "tlsSettings": {
                "certificates": [{
                    "certificateFile": str(settings.ssl_cert_file),
                    "keyFile": str(settings.ssl_key_file),
                }]
            },
        },
        "tag": "API_INBOUND",
    }
    config["inbounds"].insert(0, api_inbound)
    rules.insert(0, {
        "inboundTag": ["API_INBOUND"],
        "source": ["127.0.0.1", peer_ip],
        "outboundTag": "API",
        "type": "field",
    })
    routing["rules"] = rules
    log_config = config.setdefault("log", {})
    if log_config.get("logLevel") in ("none", "error"):
        log_config["logLevel"] = "warning"
    return config


class XRayRuntimeCore:
    def __init__(self, settings: RuntimeSettings, spool: EventSpool):
        self.settings = settings
        self.spool = spool
        self.process: subprocess.Popen[str] | None = None
        self._lock = threading.RLock()
        self._last_logs: deque[str] = deque(maxlen=100)
        self.version = self._get_version()

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            self.spool.append(event_type, payload)
        except Exception as exc:
            logger.warning("Unable to spool structured runtime event %s: %s", event_type, exc)

    def _get_version(self) -> str | None:
        output = subprocess.check_output(
            [self.settings.xray_executable, "version"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
        match = re.match(r"^Xray (\d+\.\d+\.\d+)", output)
        return match.group(1) if match else None

    @property
    def started(self) -> bool:
        process = self.process
        return bool(process is not None and process.poll() is None)

    def _capture_logs(self, process: subprocess.Popen[str]) -> None:
        stream = process.stdout
        if stream is None:
            return
        while self.process is process:
            line = stream.readline()
            if not line:
                if process.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line = line.rstrip("\r\n")
            if not line:
                continue
            self._last_logs.append(line)
            try:
                self.spool.append("xray.log", {"line": line})
            except Exception as exc:
                logger.warning("Unable to spool Xray log event: %s", exc)

        return_code = process.poll()
        with self._lock:
            unexpected_exit = self.process is process and return_code is not None
            if unexpected_exit:
                self.process = None
        if unexpected_exit:
            self._emit(
                "runtime.core.exited",
                {
                    "severity": "error",
                    "reason_code": "process_exit",
                    "message": "Xray process exited unexpectedly",
                    "previous_state": "running",
                    "new_state": "stopped",
                    "metadata": {"return_code": int(return_code)},
                },
            )

    def start(self, raw_config: str, peer_ip: str) -> None:
        self._emit(
            "runtime.core.starting",
            {
                "severity": "info",
                "reason_code": "start_requested",
                "previous_state": "stopped",
                "new_state": "starting",
            },
        )
        try:
            with self._lock:
                if self.started:
                    raise RuntimeError("Xray is started already")
                prepared = prepare_xray_config(raw_config, peer_ip, self.settings)
                environment = os.environ.copy()
                environment["XRAY_LOCATION_ASSET"] = self.settings.xray_assets_path
                process = subprocess.Popen(
                    [self.settings.xray_executable, "run", "-config", "stdin:"],
                    env=environment,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                self.process = process
                if process.stdin is None:
                    self.process = None
                    process.kill()
                    raise RuntimeError("Unable to open Xray configuration stdin")
                process.stdin.write(json.dumps(prepared, ensure_ascii=False))
                process.stdin.flush()
                process.stdin.close()
                threading.Thread(target=self._capture_logs, args=(process,), daemon=True).start()
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.process = None
                    last_log = self._last_logs[-1] if self._last_logs else "Xray exited during startup"
                    raise RuntimeError(last_log)
                time.sleep(0.1)
        except Exception as exc:
            self._emit(
                "runtime.core.start_failed",
                {
                    "severity": "error",
                    "reason_code": type(exc).__name__[:64],
                    "message": str(exc)[:1024],
                    "previous_state": "starting",
                    "new_state": "stopped",
                },
            )
            raise
        self._emit(
            "runtime.core.started",
            {
                "severity": "info",
                "reason_code": "start_succeeded",
                "previous_state": "starting",
                "new_state": "running",
                "metadata": {"core_version": self.version},
            },
        )

    def stop(self) -> None:
        with self._lock:
            process = self.process
            if process is None:
                return
            self._emit(
                "runtime.core.stopping",
                {
                    "severity": "info",
                    "reason_code": "stop_requested",
                    "previous_state": "running",
                    "new_state": "stopping",
                },
            )
            self.process = None
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
        self._emit(
            "runtime.core.stopped",
            {
                "severity": "info",
                "reason_code": "stop_succeeded",
                "previous_state": "stopping",
                "new_state": "stopped",
            },
        )

    def restart(self, raw_config: str, peer_ip: str) -> None:
        self._emit(
            "runtime.core.restarting",
            {
                "severity": "info",
                "reason_code": "restart_requested",
                "previous_state": "running" if self.started else "stopped",
                "new_state": "restarting",
            },
        )
        try:
            self.stop()
            self.start(raw_config, peer_ip)
        except Exception as exc:
            self._emit(
                "runtime.core.restart_failed",
                {
                    "severity": "error",
                    "reason_code": type(exc).__name__[:64],
                    "message": str(exc)[:1024],
                    "previous_state": "restarting",
                    "new_state": "stopped",
                },
            )
            raise
        self._emit(
            "runtime.core.restarted",
            {
                "severity": "info",
                "reason_code": "restart_succeeded",
                "previous_state": "restarting",
                "new_state": "running",
            },
        )
