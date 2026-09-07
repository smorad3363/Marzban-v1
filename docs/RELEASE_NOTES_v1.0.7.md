# Marzban v1.0.7

## Dashboard and Node management

- Ported the reviewed `test/node-dashboard-combined` Node Management workspace onto the current mainline without rolling back v1.0.6 Access Group or theme changes.
- Removed the live Node Bandwidth panel from the main Dashboard; live bandwidth remains available inside Node Management where it belongs.
- Reorganized user management controls for RTL: direct sort buttons, Admin-only dropdown filtering, compact Search / status / create / refresh controls.
- Moved bulk-user actions into the table header area, converted selected-user bulk operations to direct buttons, and hide them until at least one user is selected.
- Restored the compact Device Limit shield/warning action in each applicable user row while keeping the modern kebab menu for secondary row actions.

## Access Groups and UI polish

- Completed the Access Group section under Plans with a dedicated full-width section and quick navigation link.
- Normalized mixed Persian/English labels for Access Groups, Nodes, Inbounds and Hosts while preserving technical values and API behavior.
- Preserved the v1.0.6 Light/Dark palette, soft status badges, thin traffic progress bars, 12/16px radius system and current Admin Management architecture.

## Verification

- Dashboard TypeScript/Vite production build.
- Access Group and Admin UI contract checks.
- v1.0.7 Node/Dashboard UI contract.
- Official MySQL 8.0 and 26.7.0 regression/migration/backup/rollback compatibility workflow before release.

## نصب و به‌روزرسانی

برای نصب یا به‌روزرسانی از ابزار مدیریت Marzban استفاده کنید:

```bash
marzban update
```
