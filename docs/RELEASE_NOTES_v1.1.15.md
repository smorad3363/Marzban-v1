# v1.1.15

Dashboard Admin management includes scoped deletion requests and financial/user
usage alerts. Admins without delegation permissions can read their own requests
and alerts without receiving Admin management privileges. Credit inputs retain
focus across multi-digit edits and paste.

Deletion refunds reverse the last actual paid creation/purchase cycle, including
reseller margin entries, to its original purchaser. Unused OnHold accounts and
usage up to and including 1% refund automatically. Above 1%, deletion remains
pending until the direct parent approves an amount (0 through the purchase
price) or rejects. Decisions lock the user/request and are replay-safe; purchase
and decision snapshots survive deletion. Metered usage is never refunded.
Consumed previous renewal cycles and Form adjustment fees are not counted as a
new refundable creation purchase. Counter resets cannot hide consumed traffic.
Bulk and cleanup deletion cannot bypass a required purchase-refund approval.

Debt controls default to warning at 10% remaining / zero, freeze at -10%, and
user disconnection at -40% of the last positive wallet grant. Refunds and resale
revenue do not change that basis. Freeze/disable percentages are editable per
Admin and persist across restarts. Financial freeze blocks purchases and renewal
while preserving current connections; the disable threshold holds only active
or OnHold users in the scoped subtree. Debt recovery restores only financial
holds, preserving manual blocks, device penalties, expiry and exhausted volume.
Overlapping ancestor holds are handled independently. Revision-based runtime
retry survives process interruption; periodic reconciliation retries within one
minute. Manual account suspension remains independent.

Plan-only USER_CREDIT renewal no longer compares traffic bytes against account
count credit. It charges the selected Plan once, preserves existing network
scope and applies the existing replace-volume / extend-max-time contract.
Plan remains commercial terms; Access Group remains network authority.

Use the permanent installer or `marzban update`. The additive migration preserves
current users and financial records and initializes the debt basis from the
latest positive grant. Existing accounting durability / real-traffic qualification
limits remain; no independent real VPN load certification is claimed.
