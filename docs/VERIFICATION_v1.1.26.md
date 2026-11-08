# v1.1.26 verification — 2026-11-08

The approved user-card design is published and deployed through the official updater. The release source and tag remain unchanged; this evidence is recorded on a separate documentation branch.

## Immutable identities

| Item | Value |
| --- | --- |
| Reviewed PR | [#64](https://github.com/smorad3363/Marzban-v1/pull/64) |
| Tested final PR head | `9956d9350702c7998152a5666c4d75f8082c7d54` |
| Release source | `deed0fdf71a64d8f7174beffb88619f4586903c0` |
| Identical candidate/merge tree | `3e269e61026f2ec3581dcd8e0e0dd3af8c2ee949` |
| Annotated tag | `v1.1.26` → release source |
| Published image | `ghcr.io/smorad3363/marzban-v1@sha256:43e6354c8066c62636d9cce34b42ce8e556c7cbf71126039f357cff08391a679` |
| Official CLI SHA256 | `c16bbe51237044d47104a3edc6fcdb06b6013719d3bad514850e0202f0a56021` |
| Dashboard index SHA256 | `169eea14a57ebf5c293cfc826fce90f57b991f4bb78462868c35cc8c272ad0fc` |

## Final-head gates

All five required checks passed on the exact PR head before merge.

| Check | Evidence |
| --- | --- |
| Backend checkpoints, MySQL 8.0 | [Successful run](https://github.com/smorad3363/Marzban-v1/actions/runs/42478928113/job/128726388889) |
| Backend checkpoints, MySQL 26.7.0 | [Successful run](https://github.com/smorad3363/Marzban-v1/actions/runs/42478928113/job/128726388777) |
| Dashboard build and parity | [Successful run](https://github.com/smorad3363/Marzban-v1/actions/runs/42478928113/job/128726388646) |
| Installer, Panel compose and Node contracts | [Successful run](https://github.com/smorad3363/Marzban-v1/actions/runs/42478928113/job/128726388856) |
| Dashboard contracts, build and parity | [Successful run](https://github.com/smorad3363/Marzban-v1/actions/runs/42478928163/job/128726388431) |

[Canonical publication](https://github.com/smorad3363/Marzban-v1/actions/runs/42479391553), [independent image verification](https://github.com/smorad3363/Marzban-v1/actions/runs/42480405215), and [independent installer qualification](https://github.com/smorad3363/Marzban-v1/actions/runs/42480406955) all succeeded before deployment. The installer qualification includes fresh installation, Owner creation, version integrity and mature upgrade contracts. Main-push backend/branch skips were not counted as final-head passes.

## User-card review

The compiled candidate was rendered in Chrome against isolated synthetic API fixtures. Desktop showed two clearly separated cards per row, with all ten direct operations in one row. Light and dark themes were inspected. A 375px responsive iframe showed one card per row with two rows of five labeled actions. Long usernames and Persian notes truncated within their cards without displacing status or actions. This was a browser viewport review, not a physical-phone test. The temporary preview listener was stopped and removed afterwards.

Behavioral component tests cover each direct action, plan-renewal request and idempotency, cross-page selection, read-only permissions and the empty state. Existing protected-source/API, Plans/Access Group, alert transport, workspace, autofill and production-build parity checks passed. No Panel/Node API, billing policy or migration source was changed.

## Official upgrade and recovery

The authorized server was upgraded from v1.1.25 with the exact published CLI and `marzban update --version v1.1.26`. The updater exited successfully. CLI, runtime, configured/running image, immutable digest and source revision agree. Both Panel and MySQL containers are healthy; MySQL remains 26.7.0.

Before/after database exports of user identities/limits/expiry/ownership, Admin identities and financial/quota settings, Plan identities, Access Group identities and Alembic revision are byte-identical. No private records or credentials are included here. The official protected recovery snapshot contains SQL, data, compose and environment files; both SQL/data checksums passed. The shipped dashboard has no bind override. Public dashboard and card CSS requests returned HTTP 200, and the public HTML references `index.f1ab1796.js`.

The real v1.1.26 and v1.1.25 images passed the qualified rollback helper against identical migration bytes: SHA256 `277718fec993af60e724cabbb4ae1f982769432a7d48c1ca8101959f22071fa2`. This compatibility probe used an isolated container and did not roll production back. The previous image and recovery files remain available.

```bash
marzban update --version v1.1.26
marzban update --version v1.1.25 --allow-downgrade
```

The return command uses the normal updater, requires the explicitly qualified pair and identical migration sources, and creates a recovery snapshot before changing the running version.
