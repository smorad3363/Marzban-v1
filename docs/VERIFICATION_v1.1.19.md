# v1.1.19 verification — 2026-10-31

Status: VERIFIED for the scope below. Published tag/source remain immutable.

- Reviewed PR: https://github.com/smorad3363/Marzban-v1/pull/54
- Final PR head: `fcd4d284a81df2d6f9975bb33072af958921e22b`
- Release source: `a4cc71a80030c02d0cc1fb5db6f3d7feb50f122d`
- Release: https://github.com/smorad3363/Marzban-v1/releases/tag/v1.1.19
- Image: `ghcr.io/smorad3363/marzban-v1@sha256:519238948f84af5c50aa3463497ab64e7c68a98728f80eff221b9d351c7c3649`

All five exact-head gates PASS: MySQL 8.0, MySQL 26.7.0, dashboard parity, installer/Panel/Node contracts, dashboard UI contracts/parity. Evidence: https://github.com/smorad3363/Marzban-v1/actions/runs/41197664210 and https://github.com/smorad3363/Marzban-v1/actions/runs/41197664285 . Each MySQL regression suite reported 568 passed / 1 skipped; the six isolated migration/stage checks also passed, together with dump/restore. Skipped is not passed.

Canonical publisher PASS: https://github.com/smorad3363/Marzban-v1/actions/runs/41198037200 .
Independent image verifier PASS: https://github.com/smorad3363/Marzban-v1/actions/runs/41198215625 .
Independent isolated installer verifier PASS: https://github.com/smorad3363/Marzban-v1/actions/runs/41198217154 .

The separately authorized live update completed after a private SQL/state recovery snapshot and checksum verification. CLI/runtime 1.1.19 and exact source/digest match. Panel and MySQL 26.7.0 healthy; Alembic head b6e2c9f4a810. No runtime error/traceback log lines were observed in the post-update check.

Live authenticated API rejects omitted/zero/negative expiration with duration_required, with no new user or ledger rows from those requests. Formula samples at 30, 60, 180, 365, 730 and 10000 days match the new curve/cap. Both expiry columns are BIGINT.

Before/after comparison preserves existing users, expiration, quotas, purchased duration/coefficient snapshots, credentials, Access Group grants, core configuration and closed monetary history. Observed wallet movement reconciles exactly to actual usage accumulating in the existing current-hour settlement bucket; raw traffic counters did not reset. Public subscription returns HTTP 200 with ss and trojan connections.

NOT VERIFIED: visual interaction in a signed-in browser and end-user client connectivity. UI evidence is the required contracts plus canonical source/build parity. HTTP subscription rendering does not prove client connectivity.

File disposition: KEEP all release/runtime assets and historical records; ADD only this evidence document. This documentation commit does not replace or move the release tag.
