"""Shadowsocks 2022 key handling shared by the core and subscription formats."""
import base64
import binascii
import secrets
import hashlib

METHOD = "2022-blake3-aes-256-gcm"
KEY_LENGTH = 32
KEY_PLACEHOLDER = "__AUTO_SS2022_SERVER_KEY__"


def generate_key():
    return base64.b64encode(secrets.token_bytes(KEY_LENGTH)).decode("ascii")


def valid_key(value):
    try:
        return isinstance(value, str) and len(base64.b64decode(value, validate=True)) == KEY_LENGTH
    except (ValueError, binascii.Error):
        return False


def require_key(value, description="Shadowsocks 2022"):
    if not valid_key(value):
        raise ValueError(f"{description} must be a base64-encoded 32-byte key")
    return value


def is_2022(method):
    return getattr(method, "value", method) == METHOD


def user_key_2022(settings):
    """Use existing 2022 PSK unchanged, or derive a stable one from classic SS.

    This never rewrites legacy credentials or changes a user's traffic accounting.
    The domain-separated hash yields the 32-byte AES-256-GCM key required by Xray.
    """
    password = settings.get("password")
    if not isinstance(password, str) or not password:
        raise ValueError("Shadowsocks user password must not be empty")
    if valid_key(password):
        return password
    digest = hashlib.sha256(b"marzban-v1/ss2022/user-key/v1\0" + password.encode()).digest()
    return base64.b64encode(digest).decode("ascii")


def legacy_method(settings, inbound_method):
    """Classic SS may choose a cipher per user; SS2022 cannot."""
    user_method = getattr(settings.get("method"), "value", settings.get("method"))
    if user_method in ("aes-128-gcm", "aes-256-gcm", "chacha20-ietf-poly1305"):
        return user_method
    method = getattr(inbound_method, "value", inbound_method)
    if method in ("aes-128-gcm", "aes-256-gcm", "chacha20-ietf-poly1305"):
        return method
    return "chacha20-ietf-poly1305"


def client_settings(settings, method):
    """Return an Xray-ready user, never a mixed 2022/classic cipher."""
    if is_2022(method):
        return {"password": user_key_2022(settings)}
    password = settings.get("password")
    if not isinstance(password, str) or not password:
        raise ValueError("Shadowsocks user password must not be empty")
    return {"password": password, "method": legacy_method(settings, method)}


def normalize_inbound_clients(inbound):
    """Last-mile guard for both master and node start/restart configurations."""
    if inbound.get("protocol") != "shadowsocks":
        return inbound
    settings = inbound.setdefault("settings", {})
    method = settings.get("method")
    for user in settings.get("clients") or []:
        original = dict(user)
        user.clear()
        user.update({key: original[key] for key in ("email", "level") if key in original})
        user.update(client_settings(original, method))
    return inbound


def subscription_settings(settings, method, server_key):
    result = dict(settings)
    if is_2022(method):
        require_key(server_key, "Shadowsocks 2022 server key")
        result["method"] = METHOD
        result["password"] = server_key + ":" + user_key_2022(settings)
    else:
        result["method"] = legacy_method(settings, method)
    return result
