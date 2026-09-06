from __future__ import annotations

import logging
import ssl

import uvicorn

from node_runtime.certificates import ensure_server_certificate
from node_runtime.config import RuntimeSettings
from node_runtime.service import create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = RuntimeSettings.from_env()
    if not settings.ssl_client_cert_file.is_file():
        raise RuntimeError("SSL_CLIENT_CERT_FILE does not exist; strict mTLS is required")
    ensure_server_certificate(settings.ssl_cert_file, settings.ssl_key_file)
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        ssl_keyfile=str(settings.ssl_key_file),
        ssl_certfile=str(settings.ssl_cert_file),
        ssl_ca_certs=str(settings.ssl_client_cert_file),
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        access_log=False,
    )


if __name__ == "__main__":
    main()
