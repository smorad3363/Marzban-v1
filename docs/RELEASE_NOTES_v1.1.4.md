# Marzban v1.1.4

## Highlights

- Redesign the Plans page as a responsive RTL SaaS dashboard using the existing dark panel tokens with a restrained Black/Gold visual system.
- Rework Plan-category management into clear responsive cards with plan counts, inline editing, archive actions, and subtle per-category accents.
- Present Plans as premium responsive cards with prominent Persian-formatted pricing, category/trial badges, data/duration/device summaries, and localized reset-strategy labels.
- Improve the per-Plan quick-user workflow with a dedicated section while preserving the existing username, Access Group selection, and `/users/from-plan` mutation behavior.
- Reorganize the create/edit Plan modal for clearer hierarchy while retaining every existing field, Trial pricing behavior, payload structure, validation, toast, and archive flow.
- Preserve the existing `/account/summary`, `/user-plans`, `/plan-categories`, `/access-groups`, and `/users/from-plan` APIs, React Query keys, OWNER/plan-management permissions, and backend behavior unchanged.
- No database migration or backend business-logic change is introduced in v1.1.4.

## Upgrade

```bash
marzban update --version v1.1.4
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.4/scripts/marzban.sh)" @ install --version v1.1.4 --database mysql
```

## Node Runtime

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.4/scripts/marzban.sh)" @ install-script v1.1.4
sudo marzban node install --version v1.1.4
```

## Validation

- Dashboard Stage 1 contracts, TypeScript production build, and committed source/build parity with Node.js 20.
- Full backend regression and migration/rollback evidence against MySQL 8.0 and 26.7.0.
- Installer, Panel compose, Node runtime, release-image runtime, and Panel-to-Node mTLS contracts.

This file prepares the immutable v1.1.4 release material. Publication is completed only after the reviewed commit reaches `main`, the immutable tag is created, and the canonical Release workflow verifies and publishes the multi-architecture image and GitHub Release.
