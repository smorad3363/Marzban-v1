# Marzban v1.1.10 — Maintenance release

This patch consolidates V1 active documentation and records the Owner decision: fresh empty-MySQL install, no prior operational Users/Admins/database migration required. Retains current Plan-as-commerce, Access Group as network authority, backend security, accounting, authorized usage, current migration, backup/restore, Panel-to-Node mTLS and two-MySQL-engine matrix. Preserves the dashboard source/TypeScript build and committed artifact parity and keeps the Access Group network-authorization contracts. Removes obsolete workflow expectations for historical application upgrade qualification while retaining logical backup transfer between both supported MySQL versions and aligns release versions. No new business features or UI redesign. The existing dashboard is preserved with its committed production build and parity checks.

**Published on 2026-10-16** from reviewed commit `b09801ca922199b06eaf43938664544331328668` (verified by the canonical Release workflow).

## Update after publication
```bash
marzban update --version v1.1.10
```

## Install after publication
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
```
