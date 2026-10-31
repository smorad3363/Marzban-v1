# v1.1.20 verification — 2026-10-31

VERIFIED release and authorized live update. Published source/tag remain immutable.

- PR55: https://github.com/smorad3363/Marzban-v1/pull/55
- Final PR head: `502dc2fae7eb036be4341c7c0ed7b26aff2c2d0e`.
- Release source/tag: `034489f42e31989714c6a96fbfe4e1bef9a2fa07` / `v1.1.20`.
- Image: `ghcr.io/smorad3363/marzban-v1@sha256:a3dc8c01bd9a04d9318445545dd3985a6e83d030d4a86fa2d48ef83f492407fa`.

All five exact-head gates PASS:
https://github.com/smorad3363/Marzban-v1/actions/runs/41212108700
https://github.com/smorad3363/Marzban-v1/actions/runs/41212108662
Both MySQL 8.0 and 26.7.0 reported 583 passed / 1 skipped, plus six isolated migration/stage checks and successful logical backup/restore. Skipped is not passed. Installer/Node mTLS and both dashboard build/parity gates pass.

Canonical publication PASS:
https://github.com/smorad3363/Marzban-v1/actions/runs/41212714824
Independent image verifier PASS:
https://github.com/smorad3363/Marzban-v1/actions/runs/41212898139
Independent isolated installer verifier PASS:
https://github.com/smorad3363/Marzban-v1/actions/runs/41212900409

## Authorized live update

The server device was initially offline. It reconnected during this task; the blocker was resolved, and no additional user approval was required.

Verified v1.1.19 before updating. Created a private current SQL/state/Compose/environment recovery snapshot with SHA256 checksums and a business-data manifest. Pre-pulled and checked the exact v1.1.20 image revision/digest. The official versioned update completed successfully.

VERIFIED after update:
- CLI/runtime 1.1.20 and exact source/digest match; Panel and MySQL 26.7.0 healthy.
- Alembic head c7f3a1d9e820.
- Existing local-core mode preserved and the existing active core remains running. No live Master endpoints were silently disabled; management-only is the default for fresh installs.
- User identity/ownership, expiry, quota, purchased factors, credential hashes, Access Group/network permissions, Plan data, core configuration and monetary history preserved. Wallet changes reconcile with actual usage; no raw traffic reset. The observed retention comparison required no extra settlement-row adjustment.
- Real authenticated Owner alert-center and event-stream APIs pass. Four active Admin accounts were checked against allowed self/descendant IDs. Their own per-GiB rate in account-summary matches stored policy.
- Unauthenticated summary and stream requests both return 401.
- Comprehensive alert scan interval is 120 seconds; the derived incident scan was run once to verify initialization.
- Public subscription HTTP 200 and ss/trojan connection entries preserved.
- Post-update runtime error/traceback log count zero.

## Browser evidence and limits

Authenticated browser DOM checks show a real active incident with current configured debt thresholds and a connected change stream. The alert indicator remains present on the Users page after navigation. At a 390x844 responsive viewport, the alert box fits (348px wide) and there is no document horizontal overflow. Collapse/navigation and menu/logout visibility were checked without acknowledging real incidents or editing business data. Temporary viewport override reset using the documented API.

A screenshot attempt timed out; no screenshot artifact was created or published. Browser evidence is DOM/layout inspection, not pixel-image verification. Visual checks for every Admin role and end-user client traffic connectivity remain NOT VERIFIED. No causal production CPU savings are claimed; batching/query bounds and scheduling were directly tested.

## Retention and scope

Additive incident/receipt/scan metadata only. Existing financial and network policy values were not changed. Tests stub external address discovery only in test setup; runtime discovery is unchanged. No credentials were exported.

File disposition: UPDATE this evidence document only; KEEP published release/runtime/history assets. This documentation commit does not move the release tag.
