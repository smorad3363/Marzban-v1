# Marzban V1 Scope

## Identity

- Application version: `1.0.0`
- Release tag: `v1.0.0`
- Repository: `smorad3363/Marzban-v1`
- Default branch: `main`
- Container: `ghcr.io/smorad3363/marzban-v1`
- OCI source: `https://github.com/smorad3363/Marzban-v1`

## Architecture

- Plan contains commercial entitlement: traffic, duration, price, reset/renewal behavior, device/concurrency limits, and commercial metadata.
- Access Group contains network topology: Nodes, Inbounds, and Hosts.
- User creation combines Plan entitlement with an independently resolved Access Group.
- Missing required Access Group fails closed without broad or legacy network fallback.
- Renewal preserves the user's Access Group unless an explicit supported operation changes it.
- Plan create/update and Plan UI must not create, select, or modify network topology.
- Owner Access Group UI should complete the existing implementation, not create a parallel subsystem.

## Compatibility

- Existing Access Group models, services, propagation, migration, and backfill remain authoritative.
- Legacy Plan network data may remain readable only for migration or safe compatibility.
- Normal V1 runtime must not depend on legacy Plan network scope.
- Existing billing, hierarchy, device limits, backup/restore, branding, pagination, localization, security, and release protections remain intact.

## Release Contract

- Publish reviewed `main` to a new public repository only if `smorad3363/Marzban-v1` does not already exist.
- Tag `v1.0.0` and image `ghcr.io/smorad3363/marzban-v1:v1.0.0` must be immutable and point to the exact reviewed commit.
- Release must be stable, not draft, and not prerelease.
- Canonical install command:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.0.0/scripts/marzban.sh)" @ install --version v1.0.0 --database mysql
```

- Validate `marzban create-owner USERNAME` and `marzban version` before claiming readiness.
