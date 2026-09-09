# Marzban v1.1.2

## Highlights

- Fix the Dashboard Admin creation crash when Owner selects `USER_CREDIT` (طبق پلن · سقف اکانت) by removing Chakra `FormHelperText` usage outside a `FormControl`.
- Make the Dashboard route error boundary distinguish frontend render failures from API/service failures while keeping the current session intact.
- Harden logout by clearing authentication-scoped React Query cache and replacing browser history before returning to Login.
- Add regression coverage for `FORM_ONLY`, `PLAN_ONLY`, `BOTH`, and `USER_CREDIT` creation behavior; scoped Plan creation continues through `/available-user-plans`.
- Preserve Admin deletion cleanup-strategy behavior and the existing immutable billing/audit-history safeguards.
- Keep Access Group authorization semantics and Plan authorization scope unchanged; this hotfix does not widen Admin permissions.

## Upgrade

```bash
marzban update --version v1.1.2
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.2/scripts/marzban.sh)" @ install --version v1.1.2 --database mysql
```

## Validation

- Dashboard Admin UX and v1.1.2 regression checks.
- Dashboard source/build parity with Node.js 20.
- Existing Access Group, Admin hierarchy, installer, migration, and Node contracts remain under the repository CI checkpoints.

This file prepares the immutable v1.1.2 release material. Publication is completed only after the reviewed commit reaches `main`, the immutable tag is created, and the tag-triggered Release workflow verifies and publishes the image and GitHub Release.
