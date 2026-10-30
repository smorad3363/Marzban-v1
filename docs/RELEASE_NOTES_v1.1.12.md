# v1.1.12

Dashboard Host settings load their own Inbound metadata on every page and tolerate
missing metadata without crashing. New/duplicated Host rows show explicit feedback;
invalid submissions show a notification. Database Host IDs are kept separate from
React form row keys; clones receive a new database identity. Nullable API IDs are
normalized before submission. Successful saves update the Host store and refresh
Access Group network choices immediately, avoiding stale no-active-host messages.

The permanent latest-stable installer and `marzban update` install the published
version. Access Groups remain the authority for Inbounds, Hosts and Nodes.

Host form regressions, dashboard UI contracts, TypeScript/build parity and the
existing two-MySQL backend/installer/mTLS gates are required before release.
Real traffic/load qualification and volatile-counter limitations documented in
v1.1.11 remain applicable. No change to accounting or network authorization policy.
