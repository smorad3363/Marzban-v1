# Marzban V1 Scope

> Historical V1 scope and release contract below are retained unchanged for compatibility; they do **not** override the user-approved Product-first v3.1 revised Persian roadmap or later explicit decisions for new workflows. Current work/release gate: `docs/exec-plans/active/product-first-r05a-instruction-checkpoint.md` and the latest branch SHA. In particular, the old v1.0.0 publication instructions here are history, not a current release order.

## Product-first v3.1 addendum — only new flows

- Owner manages Product name, selected Inbound/Host, positive multiplier and access/lifecycle. New Admin create/edit/renew/reserve/Trial flows select exactly one authorized Product; they must not use a hidden commercial Plan, expose separate Access Group/Node/raw-network choices to Admin, or store quota/duration/base Admin price in Product.
- The existing Access Group topology, Host/Inbound validation, actual Node relationships, Admin inbound ceilings, fail-closed guarantees, and historical Plan assignments remain preserved. A validated Access Group may be an internal network implementation detail of Product, never a second independent Admin selection. Do not assume Host determines Node until R06 confirms the real relationship.
- The latest **valid** Product network configuration always governs current Product users and a previously accepted pending renewal at activation; keep the original Product identity and purchased period/rate/amount snapshots. Owner archive/revocation blocks **new selections only**; preserve active/pending entitlements, and never fall back to broader access if the chosen network becomes invalid.
- All three new billing modes debit one Admin Toman wallet. Initial funding at creation is the immutable debt-limit base and may be zero. All further detailed terms (five-percent default editable debt limit, fifteen-percent hard limit, ninety-percent warning, Owner subtree freeze/recovery, cost-free Trial and 30-day months) derive from the revised roadmap and confirmed decisions, not historical Plan fields. No application-code change is authorized by this documentation edit alone.
- Preserve V1 database/migration, installer, security and release invariants; Product-first target 1.1.20 remains locked pending all stages, same-SHA checks, user's own successful test confirmation and a separate release instruction.

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
