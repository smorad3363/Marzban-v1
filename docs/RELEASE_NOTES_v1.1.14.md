# v1.1.14

Dashboard Access Group saves now preserve existing permissions.

Existing Access Group Admin grants are retained during network maintenance,
so an already-authorized suspended Admin no longer blocks saving the group.
New Admin grants still require active status, valid role, hierarchy and network
scope. No suspended account is reactivated by this change.

Group edits synchronize the network bindings and device-slot protocol credentials
of all bound users, including disabled/expired users for future reactivation.
Active/on-hold users receive immediate queued Xray updates after commit. Each
subscription request uses the current explicit Host scope. New Inbounds/Hosts
never join an existing group automatically; Owner must explicitly select them.
Plans remain commercial terms; Access Groups remain the sole network authority.
Existing slot credentials are preserved for retained protocols.

Use the permanent installer or `marzban update`. Accounting durability/real-traffic
qualification limits documented in v1.1.11 remain unchanged.
