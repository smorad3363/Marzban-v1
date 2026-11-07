"""Resource defaults for the standalone node, independent of the panel/database."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping


MEMORY_BUDGET_PERCENT = 75
SS2022_POLICY_CORE_VERSION = (26, 10, 31)
LEVEL_LIMITS = {"handshake": 15, "connIdle": 120, "bufferSize": 64}


def effective_memory_bytes(
    meminfo: Path = Path("/proc/meminfo"),
    cgroup_limits: tuple[Path, ...] = (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ),
) -> int:
    total = int(next(
        line.split()[1] for line in meminfo.read_text().splitlines()
        if line.startswith("MemTotal:")
    )) * 1024
    for filename in cgroup_limits:
        try:
            value = filename.read_text().strip()
        except OSError:
            continue
        if value.isdigit() and int(value) > 0:
            total = min(total, int(value))
    if total <= 0:
        raise ValueError("Unable to determine the node memory budget")
    return total


def _memory_bytes(value: str) -> int:
    match = re.fullmatch(r"([0-9]+)(B|KiB|MiB|GiB|TiB)", value)
    if not match or int(match[1]) <= 0:
        raise ValueError("GOMEMLIMIT must be a positive Go byte size or off")
    return int(match[1]) * {"B": 1, "KiB": 1024, "MiB": 1024**2,
                           "GiB": 1024**3, "TiB": 1024**4}[match[2]]


def xray_environment(
    source: Mapping[str, str], assets_path: str, memory_profile: str,
) -> dict[str, str]:
    environment = dict(source)
    environment["XRAY_LOCATION_ASSET"] = assets_path
    if memory_profile == "off":
        return environment
    if memory_profile != "balanced":
        raise ValueError("XRAY_NODE_MEMORY_PROFILE must be balanced or off")
    budget_mib = max(1, effective_memory_bytes() * MEMORY_BUDGET_PERCENT // (100 * 1024**2))
    configured = environment.get("GOMEMLIMIT", "").strip()
    # A deliberately smaller limit supports hosts shared with other services.
    # Larger limits (including off) cannot disable the balanced profile's budget.
    if not configured or configured == "off" or _memory_bytes(configured) > budget_mib * 1024**2:
        environment["GOMEMLIMIT"] = f"{budget_mib}MiB"
    else:
        environment["GOMEMLIMIT"] = configured
    if not environment.get("GOGC", "").strip():
        environment["GOGC"] = "50"
    return environment


def apply_memory_policy(config: dict[str, Any], memory_profile: str) -> None:
    if memory_profile == "off":
        return
    if memory_profile != "balanced":
        raise ValueError("XRAY_NODE_MEMORY_PROFILE must be balanced or off")
    policy = config.setdefault("policy", {})
    if not isinstance(policy, dict):
        raise ValueError("Xray policy must be an object")
    levels = policy.setdefault("levels", {})
    if not isinstance(levels, dict):
        raise ValueError("Xray policy levels must be an object")
    levels.setdefault("0", {})
    for values in levels.values():
        if not isinstance(values, dict):
            raise ValueError("Each Xray policy level must be an object")
        for name, limit in LEVEL_LIMITS.items():
            current = values.get(name)
            values[name] = min(current, limit) if type(current) in (int, float) and current >= 0 else limit


def legacy_ss2022_core(version: str | None) -> bool:
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", version or "")
    return not match or tuple(map(int, match.groups())) < SS2022_POLICY_CORE_VERSION
