"""Shadowsocks 2022 key handling shared by the core and subscription formats."""
import base64
import binascii
import secrets

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


def client_settings(settings, method):
    """Keep the SS2022 algorithm on the inbound; omit the per-user method."""
    client = dict(settings)
    if is_2022(method):
        require_key(client["password"], "Shadowsocks 2022 client key")
        client.pop("method", None)
    return client


def subscription_settings(settings, method, server_key):
    """SS2022 clients require server and user PSKs in this exact order."""
    result = dict(settings)
    if is_2022(method):
        require_key(server_key, "Shadowsocks 2022 server key")
        require_key(result["password"], "Shadowsocks 2022 user key")
        result["method"] = METHOD
        result["password"] = server_key + ":" + result["password"]
    return result
