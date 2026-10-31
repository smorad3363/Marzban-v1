import os
import subprocess


os.environ.setdefault("DEBUG", "false")
_check_output = subprocess.check_output


def check_output(*args, **kwargs):
    command = args[0] if args else kwargs.get("args", [])
    command_parts = command if isinstance(command, (list, tuple)) else [command]
    if any("xray" in str(part).lower() for part in command_parts):
        return b"Xray 1.0.0\n"
    return _check_output(*args, **kwargs)


subprocess.check_output = check_output


# Public-address discovery happens during app import. Keep tests offline and
# deterministic rather than disclosing the runner address to external services.
try:
    import requests
except ImportError:
    requests = None  # Installer-only test jobs do not install application dependencies.
from types import SimpleNamespace

_original_get = requests.get if requests is not None else None
def _offline_address_discovery(url, *args, **kwargs):
    address_urls = {
        "http://api4.ipify.org/": "8.8.8.8",
        "http://ipv4.icanhazip.com/": "8.8.8.8",
        "https://ifconfig.io/ip": "8.8.8.8",
        "http://api6.ipify.org/": "2606:4700:4700::1111",
        "http://ipv6.icanhazip.com/": "2606:4700:4700::1111",
    }
    if url in address_urls:
        return SimpleNamespace(text=address_urls[url])
    return _original_get(url, *args, **kwargs)

if requests is not None:
    requests.get = _offline_address_discovery
