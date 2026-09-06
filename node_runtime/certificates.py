from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def ensure_server_certificate(cert_path: Path, key_path: Path) -> None:
    cert_exists = cert_path.is_file()
    key_exists = key_path.is_file()
    if cert_exists and key_exists:
        return
    if cert_exists != key_exists:
        raise RuntimeError("Node TLS certificate/key pair is incomplete; refusing to overwrite it")
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Gozargah")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("Gozargah")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_bytes = certificate.public_bytes(serialization.Encoding.PEM)
    key_tmp = key_path.with_suffix(key_path.suffix + ".tmp")
    cert_tmp = cert_path.with_suffix(cert_path.suffix + ".tmp")
    key_tmp.write_bytes(key_bytes)
    cert_tmp.write_bytes(cert_bytes)
    os.chmod(key_tmp, 0o600)
    os.chmod(cert_tmp, 0o644)
    os.replace(key_tmp, key_path)
    os.replace(cert_tmp, cert_path)
