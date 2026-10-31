# v1.1.20 verification — 2026-10-31

Release source/tag are immutable: `034489f42e31989714c6a96fbfe4e1bef9a2fa07` / `v1.1.20`.
Image: `ghcr.io/smorad3363/marzban-v1@sha256:a3dc8c01bd9a04d9318445545dd3985a6e83d030d4a86fa2d48ef83f492407fa`.

VERIFIED:
- PR https://github.com/smorad3363/Marzban-v1/pull/55 final head `502dc2fae7eb036be4341c7c0ed7b26aff2c2d0e` passed all five required gates.
- CI https://github.com/smorad3363/Marzban-v1/actions/runs/41212108700 ; dashboard https://github.com/smorad3363/Marzban-v1/actions/runs/41212108662 .
- Both MySQL 8.0 and 26.7.0 reported 583 passed / 1 skipped in the main regression suite, plus six isolated migration/stage checks and successful backup/restore. Skipped is not passed.
- Installer/Panel/Node mTLS contracts and both dashboard build/parity gates passed.
- Canonical publisher https://github.com/smorad3363/Marzban-v1/actions/runs/41212714824 passed.
- Independent published image verifier https://github.com/smorad3363/Marzban-v1/actions/runs/41212898139 passed for the exact source/digest.
- Independent isolated fresh-install/upgrade verifier https://github.com/smorad3363/Marzban-v1/actions/runs/41212900409 passed.
- Local focused tests verify management-only startup/restart guards and remote checks/sampling, scoped incidents, migration replay, receipts independent from resolution, escalation/dedup, bounded query counts and batched legacy warning dedup.
- The installer-only test environment was separately exercised without application packages; public-IP discovery stubs are optional there and prevent external address-discovery calls in application tests.

BLOCKED / NOT VERIFIED:
- Authorized live update is NOT performed. The registered Desktop Commander server device is offline (last observed approximately two hours ago).
- Last earlier live observation was v1.1.19 with healthy Panel and MySQL 26.7.0. Do not infer its current state solely from that observation.
- Signed-in browser visual interaction, live endpoint preservation after v1.1.20 deployment, end-user client connectivity and measured production hardware effects remain NOT VERIFIED.
- No live database, wallet, user, network endpoint or server file was modified during this implementation/release stage.

Resume from a fresh server/device/version check and private recovery snapshot. Use `marzban update --version v1.1.20` only after that snapshot; preserve the existing local-core setting and active endpoints. Verify current source/digest, migration c7f3a1d9e820, scoped alert API/event behavior, counters, credentials, quotas, grants, subscriptions and accounting. Reconcile legitimate live usage and the existing mutable current-hour ledger bucket, rather than treating normal consumption as data loss.

File disposition: ADD only this verification document; KEEP release/runtime/history assets. This evidence commit does not move the published tag.
