# Marzban v1.1.10 — Maintenance candidate

This patch consolidates V1 active documentation and records the Owner decision: fresh empty-MySQL install, no prior operational Users/Admins/database migration required. Retains current Plan-as-commerce, Access-Group-as-network, backend security, accounting, authorized usage, current migration, backup/restore, Panel-to-Node mTLS and two-MySQL-engine matrix. Removes obsolete workflow expectations for historical application/DB upgrade qualification and aligns release versions. No new business features or UI redesign.

**NOT PUBLISHED** until exact reviewed main SHA is tagged, release CI passes, GHCR digest/source/multiarch checks succeed and GitHub Release exists.

## Update after publication
```bash
marzban update --version v1.1.10
```

## Install after publication
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.10/scripts/marzban.sh)" @ install --version v1.1.10 --database mysql
```
