# v1.1.25

The landing page combines users and compact statistics. Every user action is visible in a grouped toolbar. Charts expand on demand; service status sits beside the alert bell. Quick Plan creation generates an editable username and retains valid Plan/network choices. Reports separate activity, requests and alert history into tabs. Alert details allow credit and trial-quota actions and account editing without leaving the drawer. Admin trial quota is adjustable from the table. Currency inputs accept every whole Toman amount.

The dashboard keeps Plans as commercial entitlements and the Access Group as the sole network authority. No database migrations, accounting policy or Panel/Node protocol changes.

## Update and return

Update through the permanent installer or `marzban update --version v1.1.25`.
Return through `marzban update --version v1.1.24 --allow-downgrade` while the v1.1.25 CLI is installed. Only the qualified v1.1.25 to v1.1.24 pair is accepted, and both images must have identical migration sources. The existing pre-update database/configuration backup remains mandatory. Current data is retained; no schema downgrade is performed. The updater removes only the dashboard build override so the selected image supplies its own UI. Other volumes remain unchanged.
