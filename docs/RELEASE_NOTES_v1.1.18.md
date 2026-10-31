# v1.1.18

- Flush pending financial changes before reloading locked rows. Initial funding, grants, refunds and charges now persist with the production `autoflush=False` Session configuration. Preserve overlapping financial holds in the same reconciliation pass.
- Distinguish legacy automatic suspension from explicit Owner Freeze in Admin responses. Legacy recovery validates current debt/expiry conditions and restores only matching, unchanged users; expired, exhausted, manually changed or device-blocked users stay restricted.
- Return scoped Admin usernames in alerts. Refresh displayed wallet balances after a successful adjustment.
- Allow Owner to prepare Access Group permissions for suspended/disabled Admins while preserving runtime account restrictions, hierarchy/network ceilings and retired-account rejection.
- Accept whole arbitrary Form durations within configured inclusive upper-bound intervals. Snapshot the server-selected coefficient for each new Form account. Apply it to allocated Form prices or actual-usage wallet settlement, using exact integer remainders; keep real traffic counters unchanged. Existing accounts retain coefficient 1 unless explicitly changed. Existing Owner interval endpoints/rates remain unchanged and can be edited in Settings.
- Expose Trial grant/reclaim/reset for Plan and Allocated Traffic Admins. Creating or renewing a Trial consumes one quota atomically. Renewal preserves usage history; a paid account cannot be converted to a free Trial. Free Trial quota does not require initial monetary funding, and account/debt/network restrictions still apply.
- Make the desktop sidebar scroll at short viewport heights so logout remains reachable.

Schema additions are additive and idempotent: Form duration/coefficient on Users and fractional usage settlement remainder on Admin settings. They do not rewrite wallets, historical ledger entries, user quotas or existing traffic.

Tests include production Session settings, initial/repeated funding and retry, legacy suspension recovery, scoped alert names, inactive network grants, duration boundaries (1/30/31/45/59/60 days), fractional billing, Trial renewal/exhaustion/replay and migration replay/data retention. Release requires exact-head MySQL 8.0/26.7.0, dashboard parity, installer and Panel/Node mTLS checks. On-server repair of previously lost grants is a separately backed-up, audited operation using observed ledger evidence; it is not an automatic migration.

File disposition: KEEP all runtime/fixture/migration and attribution assets. MERGE/REPLACE only generated dashboard bundles and their index references through the existing Vite build; no unrelated source deletion.

After verified publication and a live recovery snapshot, update using `marzban update --version v1.1.18`.
