# Marzban v1.1.5

## Highlights

- Fix Admin deletion for real accounts that already have traffic usage, delegated traffic, wallet balances, users, or immutable accounting history.
- Remove the stale `admin_delete_credit_unsettled` router guard that returned HTTP 409 before the existing safe retirement path could run.
- Keep Admin deletion safe by retiring/tombstoning the identity instead of physically deleting rows referenced by immutable accounting, Audit, Plan, and allocation history.
- Preserve Owner/self deletion protection and the active-child structural blocker.
- Preserve all existing owned-user deletion strategies (`keep_users`, `disable_users`, and `delete_users`).
- Update the Admin dashboard guidance so operators are told that accounting/Audit history is preserved and balances/traffic are not retirement blockers.
- Add route-level regression coverage for deleting an Admin with non-zero total/used/delegated traffic, a non-zero money balance, an owned user, and immutable Admin money-transaction history.

## Upgrade

```bash
marzban update --version v1.1.5
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.5/scripts/marzban.sh)" @ install --version v1.1.5 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.5/scripts/marzban.sh)" @ install-script v1.1.5
sudo marzban node install --version v1.1.5
```

## Validation

- Focused Admin deletion regression suite passes against MySQL 8 with the route-level accounting-history scenario.
- Dashboard Stage 1 contracts, TypeScript production build, and committed source/build parity are required to pass on the final release commit.
- Full backend regression, migrations/partial-DDL recovery, Stage 8-11, backup/restore, and rollback compatibility are required against MySQL 8.0 and 26.7.0.
- Installer, Panel compose, release-image runtime, and Panel-to-Node mTLS contracts are required before publication.
- The immutable `v1.1.5` tag must resolve to the exact reviewed merge commit on `main`; release publication must not move or recreate the tag.

This file prepares the immutable v1.1.5 release material. Publication is complete only after the reviewed release commit reaches `main`, the immutable `v1.1.5` tag is created from that commit, and the canonical Release workflow verifies and publishes the multi-architecture image and GitHub Release.
