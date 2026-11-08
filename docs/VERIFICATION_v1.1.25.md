# v1.1.25 verification

Release source: `7dc60751eb5488e5e9d4a62228114f6c8516a8e1`.
Final PR head: `39331621c897384e2847b52bd1288c23889ac4a5`.
Published multiarch digest: `sha256:7df8deabc74c805abfaa01b36afe544adb4ccbf5469cd184d48170cdbfdb0e78`.

| Check | Result | Evidence |
| --- | --- | --- |
| Final PR head: MySQL 8.0 and 26.7.0, installer/Node/mTLS, dashboard build/parity | PASS | [CI](https://github.com/smorad3363/Marzban-v1/actions/runs/42429702934) |
| Final PR head: UI interaction, API invariants, forms, 96 contrast checks | PASS | [UI contracts](https://github.com/smorad3363/Marzban-v1/actions/runs/42429703068) |
| Canonical image/release publication | PASS | [Release](https://github.com/smorad3363/Marzban-v1/actions/runs/42430103710) |
| Published image, digest, source revision and architectures | PASS | [Independent verifier](https://github.com/smorad3363/Marzban-v1/actions/runs/42430298386) |
| Published fresh installer and Owner/version contracts | PASS | [Installer lab](https://github.com/smorad3363/Marzban-v1/actions/runs/42430300145) |
| Authorized production update through official CLI | PASS | Runtime, CLI and image report v1.1.25; application and MySQL healthy |
| Production records, user limits/expiry and migration revision | PASS | Stable business records identical before and after update |
| Served dashboard and CLI match the release | PASS | Public HTML references current assets; no dashboard bind override remains |
| Recovery snapshot checksum and real-image rollback compatibility helper | PASS | SQL/archive checksums pass; real v1.1.25 and v1.1.24 migration sources match |
| Production rollback execution | NOT PERFORMED | Update retained; no rollback was requested |
| Direct visual browser review | NOT VERIFIED | Browser access unavailable; automated interaction/contrast tests passed |

The main-push backend matrix and Branch Hygiene can be SKIPPED by their event conditions. They are not represented as passes; final PR-head backend and installer gates above provide that coverage.

## Official commands

```bash
marzban update --version v1.1.25
marzban update --version v1.1.24 --allow-downgrade
```

Only the qualified v1.1.25 to v1.1.24 return is accepted. The helper verifies every migration source byte before the updater stops the application. No database migration or accounting-policy change is part of v1.1.25. Current data is retained; a schema downgrade is never performed. Operational backups and deployment metadata remain on the authorized server and are not published here.
