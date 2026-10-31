# v1.1.17

Fix the Access Group failure caused by stale Xray Inbound tags when an Inbound is removed from the core configuration.

- Remove references to a deleted Inbound and its group-level Host selections while leaving unrelated healthy Inbounds and Hosts intact.
- Provide an explicit, authenticated `POST /api/core/inbounds/rename` operation with `old_tag` and `new_tag`; migrate the associated Group, Host, Admin Inbound permissions and User exclusions. Raw JSON edits do not guess a rename from port or protocol.
- Never grant an independently created Inbound or Host to an existing Access Group. Newly added Inbounds keep the existing default Host behavior, without any Group assignment.
- Keep a group with no Inbounds persisted and fail closed with `network_status=NO_NETWORK_ACCESS` in the API. Preserve users, credentials, status, Plan, traffic, credit and accounting records.
- Reconcile existing User exclusion mappings for the main Xray core, including disabled and expired users without activating them. Existing Node restart/reconnect logic receives the current configuration and Access Group filtering.
- Stage network metadata changes in a database transaction, replace the configuration file atomically and attempt compensating recovery on runtime errors. Recovery of unexpected process/power loss and asynchronous remote Node failure is not independently proven.

CI scope: both MySQL 8.0 and 26.7.0, migrations/backup, dashboard source/build parity, release installer and Panel-to-Node mTLS. Tests cover inbound deletion, explicit rename, independent addition, deletion of a group's last Inbound, credentials/Plan invariants and mocked runtime recovery. A fresh production deployment, real Client Subscription/Node traffic under failure and crash recovery still require separate on-server qualification.

Do not change the existing installation until a verified pre-update snapshot and live-server health checks are complete. The established `marzban update --version v1.1.17` update path preserves the current data volume when the release is published.
