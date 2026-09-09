from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one marker in {path}, found {count}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


# Dashboard: preserve UTC semantics, keep Admin credit generic, and keep status/current-activity labels accurate.
path = "app/dashboard/src/components/DashboardOverview.tsx"
text = read(path)
old = 'const toman = (value: number | null | undefined) => value == null ? "نامحدود" : `${fa(value)} تومان`;\n\nconst formatTraffic'
new = '''const toman = (value: number | null | undefined) => value == null ? "نامحدود" : `${fa(value)} تومان`;
const credit = (value: number | null | undefined) => value == null ? "نامحدود" : fa(Number(value));
const parseUtcDate = (value: string) => new Date(/(?:Z|[+-]\\d\\d:\\d\\d)$/.test(value) ? value : `${value}Z`);

const formatTraffic'''
if text.count(old) != 1:
    raise RuntimeError("Dashboard formatter marker changed")
text = text.replace(old, new, 1)
text = text.replace('const timestamp = new Date(value).getTime();', 'const timestamp = parseUtcDate(value).getTime();', 1)
text = text.replace('x: new Date(point.timestamp).getTime()', 'x: parseUtcDate(point.timestamp).getTime()', 1)
old = '''  const onlinePercent = data.active_users > 0 ? Math.min(100, (data.online_users / data.active_users) * 100) : 0;
  const statusItems = [
    { label: "فعال", value: data.active_users, color: "#2fd788" },
    { label: "منقضی", value: data.expired_users, color: "#ef5d67" },
    { label: "غیرفعال", value: data.disabled_users, color: "#748094" },
    { label: "در انتظار", value: data.on_hold_users + data.limited_users, color: "#d7ad54" },
  ];'''
new = '''  const statusItems = [
    { label: "فعال", value: data.active_users, color: "#2fd788" },
    { label: "منقضی", value: data.expired_users, color: "#ef5d67" },
    { label: "غیرفعال", value: data.disabled_users, color: "#748094" },
    { label: "در انتظار", value: data.on_hold_users, color: "#d7ad54" },
    { label: "محدود", value: data.limited_users, color: "#9b7ad8" },
  ];'''
if old not in text:
    raise RuntimeError("Dashboard status marker changed")
text = text.replace(old, new, 1)
text = text.replace('hint={`${fa(Math.round(onlinePercent))}٪ از کاربران فعال`}', 'hint={`فعالیت ثبت‌شده در ${fa(data.online_window_seconds)} ثانیه اخیر`}', 1)
text = text.replace('quota?.credit_limit == null ? "نامحدود" : formatTraffic(quota.credit_limit)', 'credit(quota?.credit_limit)', 1)
text = text.replace('quota ? formatTraffic(quota.credit_used) : "—"', 'quota ? credit(quota.credit_used) : "—"', 1)
text = text.replace('>مانده ظرفیت</Text><Text fontSize="sm" fontWeight="850">{quota?.credit_remaining == null ? "نامحدود" : formatTraffic(quota.credit_remaining)}</Text>', '>مانده اعتبار</Text><Text fontSize="sm" fontWeight="850">{credit(quota?.credit_remaining)}</Text>', 1)
if "onlinePercent" in text or "new Date(point.timestamp)" in text:
    raise RuntimeError("Dashboard review cleanup incomplete")
write(path, text)


# Backend: Owner Admin summary includes legacy Admins; billing-model distribution is Owner-only.
path = "app/utils/dashboard_metrics.py"
text = read(path)
if "    AdminAccountStatus,\n" not in text:
    raise RuntimeError("AdminAccountStatus import marker changed")
text = text.replace("    AdminAccountStatus,\n", "", 1)
old = '''def _owner_admin_summary(db: Session, actor: Admin) -> DashboardAdminSummary:
    rows = (
        db.query(AdminAccountStatus.code, func.count(Admin.id))
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
        .join(AdminAccountStatus, AdminAccountStatus.id == MarzhelpAdminSettings.account_status_id)
        .filter(Admin.id != actor.id, Admin.deleted_at.is_(None))
        .group_by(AdminAccountStatus.code)
        .all()
    )
    counts = {str(code): int(count) for code, count in rows}
    return DashboardAdminSummary(
        total=sum(counts.values()),
        active=counts.get(admin_hierarchy.ACTIVE, 0),
        suspended=counts.get(admin_hierarchy.SUSPENDED, 0),
        disabled=counts.get(admin_hierarchy.DISABLED, 0),
    )
'''
new = '''def _owner_admin_summary(db: Session, actor: Admin) -> DashboardAdminSummary:
    status_expression = case(
        (
            MarzhelpAdminSettings.account_status_id
            == admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.SUSPENDED],
            admin_hierarchy.SUSPENDED,
        ),
        (
            MarzhelpAdminSettings.account_status_id
            == admin_hierarchy.ACCOUNT_STATUS_IDS[admin_hierarchy.DISABLED],
            admin_hierarchy.DISABLED,
        ),
        else_=admin_hierarchy.ACTIVE,
    )
    rows = (
        db.query(status_expression.label("status"), func.count(Admin.id))
        .outerjoin(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
        .filter(Admin.id != actor.id, Admin.deleted_at.is_(None))
        .group_by(status_expression)
        .all()
    )
    counts = {str(code): int(count) for code, count in rows}
    return DashboardAdminSummary(
        total=sum(counts.values()),
        active=counts.get(admin_hierarchy.ACTIVE, 0),
        suspended=counts.get(admin_hierarchy.SUSPENDED, 0),
        disabled=counts.get(admin_hierarchy.DISABLED, 0),
    )
'''
if old not in text:
    raise RuntimeError("Owner Admin summary marker changed")
text = text.replace(old, new, 1)
old = '''    mode_expression = func.coalesce(MarzhelpAdminSettings.billing_mode, BillingMode.LEGACY_COMPAT.value)
    admin_rows = (
        _visible_admins(db, actor, hierarchy_on=hierarchy_on, actor_is_owner=actor_is_owner)
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
        .with_entities(mode_expression.label("mode"), func.count(Admin.id))
        .group_by(mode_expression)
        .all()
    )
    admin_counts = {str(mode): int(count) for mode, count in admin_rows}

    user_rows = (
        _visible_users(
            db,
            actor,
            hierarchy_on=hierarchy_on,
            actor_is_owner=actor_is_owner,
            allowed_inbounds=allowed_inbounds,
        )
        .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == User.admin_id)
        .with_entities(
            mode_expression.label("mode"),
            func.count(User.id),
            func.coalesce(func.sum(case((User.status == UserStatus.active, 1), else_=0)), 0),
            func.coalesce(func.sum(User.used_traffic), 0),
            func.coalesce(func.sum(User.data_limit), 0),
        )
        .group_by(mode_expression)
        .all()
    )
    user_by_mode = {
        str(mode): (int(count), int(active), int(used), int(allocated))
        for mode, count, active, used, allocated in user_rows
    }
'''
new = '''    admin_counts: dict[str, int] = {}
    user_by_mode: dict[str, tuple[int, int, int, int]] = {}
    if actor_is_owner:
        mode_expression = func.coalesce(
            MarzhelpAdminSettings.billing_mode,
            BillingMode.LEGACY_COMPAT.value,
        )
        admin_rows = (
            _visible_admins(db, actor, hierarchy_on=hierarchy_on, actor_is_owner=True)
            .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == Admin.id)
            .with_entities(mode_expression.label("mode"), func.count(Admin.id))
            .group_by(mode_expression)
            .all()
        )
        admin_counts = {str(mode): int(count) for mode, count in admin_rows}

        user_rows = (
            _visible_users(
                db,
                actor,
                hierarchy_on=hierarchy_on,
                actor_is_owner=True,
                allowed_inbounds=allowed_inbounds,
            )
            .join(MarzhelpAdminSettings, MarzhelpAdminSettings.admin_id == User.admin_id)
            .with_entities(
                mode_expression.label("mode"),
                func.count(User.id),
                func.coalesce(func.sum(case((User.status == UserStatus.active, 1), else_=0)), 0),
                func.coalesce(func.sum(User.used_traffic), 0),
                func.coalesce(func.sum(User.data_limit), 0),
            )
            .group_by(mode_expression)
            .all()
        )
        user_by_mode = {
            str(mode): (int(count), int(active), int(used), int(allocated))
            for mode, count, active, used, allocated in user_rows
        }
'''
if old not in text:
    raise RuntimeError("Billing distribution query marker changed")
text = text.replace(old, new, 1)
old = '''        billing_modes=[
            DashboardBillingModeMetric(
                billing_mode=mode,
                admin_count=admin_counts.get(mode, 0),
                user_count=user_by_mode.get(mode, (0, 0, 0, 0))[0],
                active_users=user_by_mode.get(mode, (0, 0, 0, 0))[1],
                current_used_traffic=(
                    user_by_mode.get(mode, (0, 0, 0, 0))[2] if usage_visible else None
                ),
                allocated_quota=user_by_mode.get(mode, (0, 0, 0, 0))[3],
            )
            for mode in MODES
        ],'''
new = '''        billing_modes=(
            [
                DashboardBillingModeMetric(
                    billing_mode=mode,
                    admin_count=admin_counts.get(mode, 0),
                    user_count=user_by_mode.get(mode, (0, 0, 0, 0))[0],
                    active_users=user_by_mode.get(mode, (0, 0, 0, 0))[1],
                    current_used_traffic=user_by_mode.get(mode, (0, 0, 0, 0))[2],
                    allocated_quota=user_by_mode.get(mode, (0, 0, 0, 0))[3],
                )
                for mode in MODES
            ]
            if actor_is_owner
            else []
        ),'''
if old not in text:
    raise RuntimeError("Billing response marker changed")
text = text.replace(old, new, 1)
write(path, text)


# Scope and legacy-Admin tests.
path = "tests/test_dashboard_owner_admin_v2.py"
text = read(path)
marker = "        assert result.admin_summary is None\n"
if text.count(marker) != 1:
    raise RuntimeError("Admin privacy assertion marker changed")
text = text.replace(marker, marker + "        assert result.billing_modes == []\n", 1)
old = '        suspended_admin = Admin(username="suspended-admin", hashed_password="x")\n        db.add_all([owner, active_admin, suspended_admin])'
new = '        suspended_admin = Admin(username="suspended-admin", hashed_password="x")\n        legacy_admin = Admin(username="legacy-admin", hashed_password="x")\n        db.add_all([owner, active_admin, suspended_admin, legacy_admin])'
if old not in text:
    raise RuntimeError("Owner legacy Admin fixture marker changed")
text = text.replace(old, new, 1)
old = "        assert result.admin_summary.total == 2\n        assert result.admin_summary.active == 1"
new = "        assert result.admin_summary.total == 3\n        assert result.admin_summary.active == 2"
if old not in text:
    raise RuntimeError("Owner Admin summary assertion marker changed")
text = text.replace(old, new, 1)
write(path, text)


# Stable release surfaces.
replace_once("VERSION", "1.1.7\n", "1.1.8\n")
replace_once("app/__init__.py", '__version__ = "1.1.7"', '__version__ = "1.1.8"')
replace_once("scripts/marzban.sh", 'CLI_RELEASE_VERSION="v1.1.7"', 'CLI_RELEASE_VERSION="v1.1.8"')
replace_once("docker-compose.yml", 'image: ghcr.io/smorad3363/marzban-v1:v1.1.7', 'image: ghcr.io/smorad3363/marzban-v1:v1.1.8')


# Canonical Release workflow must enforce the new autofill invariant too.
path = ".github/workflows/build.yml"
text = read(path)
old = '''      - name: Verify canonical dashboard UX contract
        working-directory: app/dashboard
        run: node scripts/test-stage1-ui-contracts.cjs
'''
new = '''      - name: Verify canonical dashboard UX contracts
        working-directory: app/dashboard
        run: |
          node scripts/test-stage1-ui-contracts.cjs
          node scripts/test-autofill-contract.cjs
'''
if old not in text:
    raise RuntimeError("Release dashboard contract marker changed")
write(path, text.replace(old, new, 1))


Path("docs/RELEASE_NOTES_v1.1.8.md").write_text(
    '''# Marzban v1.1.8

## Highlights

- Redesign the Dashboard as separate role-aware Owner and Admin operational views backed only by real scoped backend aggregates; the dedicated Users page remains the full user-management surface.
- Add real 24-hour, 7-day, and 30-day user-traffic history from the existing authoritative usage collector, current-activity counts, status distribution, attention signals, top consumers, and recent-user summaries without adding a second Xray polling path.
- Add Owner-only compact Node and Admin summaries while keeping Admin data restricted to its authorized user scope in the backend.
- Keep Admin credit presentation generic and avoid exposing billing-model basis; Owner remains unrestricted.
- Prevent saved login credentials from autofilling authenticated/non-login inputs, including dynamically mounted Chakra portals, while preserving username/current-password autofill on the Login page.
- Extend Dashboard UI contracts, backend authorization/scope tests, and the canonical Release workflow so the autofill invariant and committed dashboard parity are verified before publication.
- Preserve Node Operations V2, safe Admin retirement, Plan permissions, Access Group semantics, and existing installer/mTLS architecture.

## Upgrade

```bash
marzban update --version v1.1.8
```

## Fresh install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.8/scripts/marzban.sh)" @ install --version v1.1.8 --database mysql
```

## Node Runtime

Use the same immutable release when installing or updating the built-in Node Runtime:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/smorad3363/Marzban-v1/v1.1.8/scripts/marzban.sh)" @ install-script v1.1.8
sudo marzban node install --version v1.1.8
```

For an existing Node installation:

```bash
sudo marzban node update --version v1.1.8
sudo marzban node doctor
```

## Validation

- Dashboard Stage 1 contracts, authenticated-autofill contract, TypeScript production build, output verification, and committed dashboard parity must pass on the final release source.
- Backend regression, authorization/scope coverage, migrations/partial-DDL recovery, Stage 8-11 evidence, backup/restore, and v4.8.0 rollback compatibility must pass against MySQL 8.0 and MySQL 26.7.0.
- Installer syntax/contracts, panel compose, built-in Node compose, MySQL 8.0 logical dump -> 26.7.0 restore, release-image runtime, and Panel-to-Node mTLS contracts must pass before publication.
- The immutable `v1.1.8` tag must resolve to the exact reviewed release commit on `main`; publication must not move or recreate it.
- The canonical Release workflow must publish and anonymously verify multi-architecture `linux/amd64` and `linux/arm64` GHCR images and create the GitHub Release from this file.
''',
    encoding="utf-8",
)


Path("docs/CODEX/STATE.md").write_text(
    '''# V1 Continuation State

## Active Task: v1.1.8 Dashboard Owner/Admin V2 release candidate

- Working branch: `feat/dashboard-owner-admin-v2`
- Pull request: `#39`
- Base/main SHA at task start: `e8f9ce09c7939c15a2fbdeae858ba990d79db846`
- Immutable prior release: `v1.1.7` MUST remain at `c0775a624b7081f794b492e4596bbc484aa6be02`; never move/recreate it.
- Target release: `v1.1.8`.

## Completed Product Work

- Credential autofill is suppressed throughout authenticated UI and Chakra portals; Login retains `username` / `current-password` autofill.
- Owner/Admin Dashboard V2 uses `/api/dashboard/overview` with backend-enforced role/scope.
- Real traffic history comes from existing `NodeUserUsage`; no additional Xray reset-counter poller exists.
- Attention, top consumers, recent users, current activity, status distribution, Owner Node summary, and Owner Admin summary are real database aggregates.
- Admin sees no Owner-only Node/Admin summary and receives no billing-mode distribution from Dashboard overview.
- Admin credit UI remains generic and does not disclose accounting-model basis.
- Users remains the dedicated management surface.
- `host_update_impact` unrelated behavior was restored to the `main` baseline during self-review.
- Version surfaces and release notes are prepared for `v1.1.8`; canonical Release workflow also verifies the authenticated-autofill contract.

## Non-regression Invariants

- Preserve Node Operations V2, one authoritative reset-counter collector, safe Admin retirement, Plan permissions, Access Group semantics, Owner unrestricted behavior, and Panel-to-Node mTLS.
- `v1.1.7` is immutable and must never be moved/recreated.
- `v1.1.8` may be tagged only from the final reviewed merge commit on `main` after all required CI gates are green.

## Last Work File

`app/dashboard/src/components/DashboardOverview.tsx`

## Last Work Section

Final release-candidate self-review: UTC timestamp handling, generic Admin credit presentation, accurate status/current-activity semantics, legacy-safe Owner Admin summary, and Admin billing-mode privacy.

## NEXT EXACT TASK

1. Remove the one-time release-preparation script/workflow from the feature branch.
2. Verify the resulting clean PR #39 HEAD and run both `CI Checkpoints` and `Dashboard UI Contracts` to completion.
3. If any gate fails, inspect the exact failing job/step and fix only its root cause; regenerate committed dashboard build if dashboard source changes.
4. Re-review the final PR diff for scope/security/unrelated changes and verify `main` has not moved.
5. Mark PR #39 ready and squash-merge only the verified head.
6. Verify post-merge `main` CI and all release surfaces (`VERSION`, `app/__init__.py`, `scripts/marzban.sh`, `docker-compose.yml`, `docs/RELEASE_NOTES_v1.1.8.md`).
7. Verify `v1.1.8` does not already exist, then create it at the exact verified release commit on `main` without moving any existing tag.
8. Wait for the canonical `Release` workflow to succeed, including dashboard contracts/parity, multi-arch GHCR publish, anonymous/runtime image verification, and GitHub Release creation.
9. Confirm tag SHA, GitHub Release, `ghcr.io/smorad3363/marzban-v1:v1.1.8`, `latest`, and release workflow source SHA all match.

## Recovery Rule

When work resumes, fetch this file, fetch/review `Last Work File`, verify PR/main/tag/release state, then continue from the first incomplete `NEXT EXACT TASK` item. If `v1.1.8` already exists, never recreate or move it; verify publication instead.
''',
    encoding="utf-8",
)

print("v1.1.8 release-candidate source preparation complete")
