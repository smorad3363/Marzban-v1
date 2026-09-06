# Marzban v1.0.3

Marzban v1.0.3 is a focused installer UX hotfix on top of the validated v1.0.2 runtime.

## Change

- Restores the familiar **interactive Node certificate paste** flow: when `--client-cert-file` is omitted, `marzban node install` asks for the complete PEM copied from Master > Nodes and finishes input automatically at `END CERTIFICATE`.
- Keeps `--client-cert-file /path/to/panel-client.crt` available for unattended automation.
- The pasted certificate is validated as X.509, handled through a mode-600 temporary file, and only the public certificate is stored on the Node. The panel private key is never requested or copied.

## Compatibility

- This is a patch on top of v1.0.2; Node Runtime V2, durable event delivery, Device Limit behavior, CDN/IP-source policy, Access Group ownership, and low-memory defaults are unchanged.
- Historical V1 lineage remains exactly `v5.2.0 -> v1.0.0`.
- Published v1.0.0, v1.0.1, and v1.0.2 artifacts remain immutable.
