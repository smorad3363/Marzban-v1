# v1.1.26

The dashboard user workspace now uses the owner-approved card design. Desktop screens show two users per row; smaller screens show one full-width card. Each user has a clear border, identity/status row, compact Plan/expiry/device facts, traffic progress, Admin/activity metadata and all existing direct operations. Desktop actions fit one row; mobile controls use two comfortable rows. Bulk selection, cross-page selections, pagination, read-only permissions, device settings and lazy detail/renewal dialogs are retained.

Plans remain commercial entitlements; the Access Group remains the sole network authority. No database migrations, accounting policy or Panel/Node API changes.

Update with the permanent installer or `marzban update --version v1.1.26`.
Return to the previous design with `marzban update --version v1.1.25 --allow-downgrade`. The qualified pair requires identical migration sources and the normal recovery snapshot. Current data is retained. The existing v1.1.25 to v1.1.24 compatible return remains supported.
