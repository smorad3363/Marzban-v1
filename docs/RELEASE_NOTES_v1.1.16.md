# v1.1.16

Exclude the unlimited Owner wallet from descendant financial spending checks,
connection restrictions and recovery. Setting the Owner monetary-billing flag
must not freeze a funded child or prevent recovery of that child's users.
Non-Owner financial ceilings, direct-parent refund authorization, and all scoped
billing restrictions remain enforced. No balances or existing account statuses
are rewritten by this patch.

This includes the v1.1.15 dashboard Access Group checkbox fix, transactional
purchase refunds, requests/alerts, configurable debt controls, wallet retry
identity, and USER_CREDIT Plan renewal repair. Access Group remains the sole
network authority; core tag removal or rename does not implicitly grant a new
Inbound or rewrite existing groups.

Use the permanent installer or `marzban update`. Regression covers the Owner
flag with zero balance and the Owner exemption during child debt recovery.
Existing real-traffic/accounting qualification limits remain unchanged.
