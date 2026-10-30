# v1.1.13

Dashboard Access Group navigation scrolls within Plans without replacing the
HashRouter route. Existing #access-groups links redirect to Plans safely.
Admin creation permissions refresh in already-open sessions every 10 seconds;
Admin edits invalidate the account summary immediately. Form-only, Plan-only
and Both capabilities remain backend-enforced. This patch does not grant new
network or financial permissions. Access Groups remain network authority.

The permanent installer and `marzban update` install the latest stable version.
Accounting durability and real-traffic qualification limitations in v1.1.11
remain unchanged. Full dashboard parity, both MySQL engines and installer/Node
checks are required before publication.
