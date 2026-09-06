# Marzban v1.0.2

Marzban v1.0.2 keeps the V1 commercial/network ownership contract intact while adding a production-ready **Built-in Node Runtime V2** and operational hardening.

## Highlights

- Built-in Node Runtime V2 ships in the same versioned Marzban image; Nodes do not require a separate Marzban-node image or MySQL service.
- Strict certificate-based Node transport. Nodes receive only the panel client certificate used for verification; the panel private key is never copied to a Node.
- Durable SQLite-backed Node event spool with deduplication and ACK only after the panel consumes the batch, protecting usage/device events across reconnects and restarts.
- Fail-closed client-IP trust: Node IP observations are accepted only when both the configured IP-source policy and the V2 runtime capability confirm direct client-IP support.
- Node bandwidth/resource reporting and dashboard visibility for operational capacity monitoring.
- Built-in `marzban node install`, `update`, `status`, and `logs` commands with release/source-integrity checks and isolated Node state under `/opt/marzban-node` and `/var/lib/marzban-node`.
- Co-located Node CLI updates cannot overwrite the panel CLI or panel release metadata.
- Conservative runtime resource defaults and opt-in tooling profile remain suitable for smaller installations.

## Compatibility and safety

- Plans remain commercial entitlements only; Access Group ownership of Nodes, Inbounds, and Hosts is unchanged.
- The one-time mature product-line transition remains exactly `v5.2.0 -> v1.0.0`. This release does not widen that downgrade/lineage exception.
- Existing V1 installations update normally from `v1.0.0` or `v1.0.1` to `v1.0.2` through the verified release path.
- Release image publication remains immutable: an existing release tag or image is never overwritten.
