from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    if old not in content:
        raise SystemExit(f"expected pattern not found in {path}: {old[:120]!r}")
    write(path, content.replace(old, new, 1))


DASHBOARD = '''import {
  Badge,
  Box,
  Card,
  HStack,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
} from "@chakra-ui/react";
import { AppShell } from "components/AppShell";
import useGetUser from "hooks/useGetUser";
import { FC } from "react";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities, ManagedAdminList } from "types/Admin";

const fa = (value: number) => Number(value || 0).toLocaleString("fa-IR");
const credit = (value: number | null | undefined) => value == null ? "نامحدود" : Number(value).toLocaleString("fa-IR");

const Metric: FC<{ label: string; value: string; hint?: string; tone?: string }> = ({ label, value, hint, tone }) => (
  <Card
    p={{ base: 4, md: 5 }}
    minH="118px"
    bg="var(--panel-surface)"
    color="inherit"
    borderWidth="1px"
    borderColor="var(--panel-border)"
    borderRadius="16px"
    boxShadow="var(--shadow-panel)"
  >
    <Text color="var(--panel-text-muted)" fontSize="12px" fontWeight="700">{label}</Text>
    <Text mt={2} color={tone || "var(--panel-text)"} fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900" sx={{ fontVariantNumeric: "tabular-nums" }}>
      {value}
    </Text>
    {hint && <Text mt={2} color="var(--panel-text-muted)" fontSize="11px">{hint}</Text>}
  </Card>
);

export const Dashboard: FC = () => {
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = userData.role === "OWNER" || userData.is_sudo;

  const account = useQuery<AccountSummary, Error>(
    ["account-summary", userData.username],
    () => fetch("/account/summary"),
    { enabled: getUserIsSuccess && !isOwner, refetchInterval: 30000 }
  );
  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities"),
    { enabled: getUserIsSuccess && !isOwner, refetchInterval: 30000 }
  );
  const managedAdmins = useQuery<ManagedAdminList, Error>(
    ["dashboard-admin-overview", userData.username],
    () => fetch("/admin-management?offset=0&limit=100"),
    { enabled: getUserIsSuccess && isOwner, refetchInterval: 30000 }
  );

  const admins = managedAdmins.data?.admins || [];
  const activeAdmins = admins.filter((item) => item.account_status === "ACTIVE").length;
  const suspendedAdmins = admins.filter((item) => item.account_status === "SUSPENDED").length;
  const disabledAdmins = admins.filter((item) => item.account_status === "DISABLED").length;
  const walletOnPage = admins.reduce((sum, item) => sum + Number(item.policy.money_balance_toman || 0), 0);
  const planManagers = admins.filter((item) => item.can_manage_plans).length;
  const childManagers = admins.filter((item) => item.can_create_admins).length;
  const adminSampleHint = (managedAdmins.data?.total || 0) > admins.length ? "در ۱۰۰ ادمین اخیر" : "در همه ادمین‌ها";

  const accountData = account.data;
  const quota = capabilities.data?.quota;
  const trialRemaining = accountData ? Math.max(Number(accountData.trial_quota || 0) - Number(accountData.trials_used || 0), 0) : 0;

  return (
    <AppShell>
      <Stack spacing={5}>
        <Card
          px={{ base: 4, md: 5 }}
          py={{ base: 4, md: 5 }}
          bg="linear-gradient(145deg, var(--panel-surface), var(--panel-nested))"
          color="inherit"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="18px"
          boxShadow="var(--shadow-panel)"
        >
          <HStack justify="space-between" align="start" gap={4} flexWrap="wrap">
            <Box minW={0}>
              <Text color="var(--panel-accent)" fontSize="11px" fontWeight="900">داشبورد</Text>
              <Text as="h1" mt={1} fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900" letterSpacing="-0.04em">
                خوش آمدی، <Text as="span" dir="ltr">{userData.username}</Text>
              </Text>
              <Text mt={2} color="var(--panel-text-muted)" fontSize="sm">
                {isOwner
                  ? "نمای مدیریتی ادمین‌ها؛ وضعیت، اعتبار و دسترسی‌های عملیاتی در یک نگاه."
                  : "خلاصه وضعیت حساب، اعتبار و ظرفیت‌های قابل استفاده شما."}
              </Text>
            </Box>
            {!isOwner && accountData && (
              <Badge
                colorScheme={accountData.account_status === "ACTIVE" ? "green" : accountData.account_status === "SUSPENDED" ? "orange" : "red"}
                px={3}
                py={1.5}
                borderRadius="full"
                fontSize="11px"
              >
                {accountData.account_status === "ACTIVE" ? "حساب فعال" : accountData.account_status === "SUSPENDED" ? "حساب فریز" : "حساب غیرفعال"}
              </Badge>
            )}
          </HStack>
        </Card>

        {isOwner ? (
          managedAdmins.isLoading ? (
            <Skeleton height="310px" borderRadius="18px" />
          ) : (
            <SimpleGrid columns={{ base: 1, sm: 2, xl: 3 }} gap={4}>
              <Metric label="کل ادمین‌ها" value={fa(managedAdmins.data?.total || 0)} hint="بدون حساب Owner" tone="var(--panel-accent)" />
              <Metric label="ادمین فعال" value={fa(activeAdmins)} hint={adminSampleHint} tone="var(--panel-success)" />
              <Metric label="ادمین فریز" value={fa(suspendedAdmins)} hint={adminSampleHint} tone="var(--panel-warning)" />
              <Metric label="ادمین غیرفعال" value={fa(disabledAdmins)} hint={adminSampleHint} tone="var(--panel-danger)" />
              <Metric label="موجودی ادمین‌ها" value={`${fa(walletOnPage)} تومان`} hint={adminSampleHint} />
              <Metric label="مدیر پلن" value={fa(planManagers)} hint={adminSampleHint} />
              <Metric label="مجاز به ساخت ادمین" value={fa(childManagers)} hint={adminSampleHint} />
            </SimpleGrid>
          )
        ) : account.isLoading || capabilities.isLoading || !accountData ? (
          <Skeleton height="310px" borderRadius="18px" />
        ) : (
          <SimpleGrid columns={{ base: 1, sm: 2, xl: 4 }} gap={4}>
            <Metric label="اعتبار مالی" value={`${fa(accountData.money_balance_toman)} تومان`} hint="موجودی قابل استفاده حساب" tone="var(--panel-accent)" />
            <Metric label="سقف اعتبار" value={credit(quota?.credit_limit)} hint="سقف تخصیص‌یافته به حساب" />
            <Metric label="اعتبار مصرف‌شده" value={credit(quota?.credit_used)} hint="مصرف ثبت‌شده حساب" tone="var(--panel-warning)" />
            <Metric label="مانده اعتبار" value={credit(quota?.credit_remaining)} hint="اعتبار قابل استفاده باقی‌مانده" tone="var(--panel-success)" />
            <Metric label="کاربران من" value={fa(accountData.own_users)} hint="کاربران مستقیم این حساب" />
            <Metric label="کاربران زیرمجموعه" value={fa(accountData.subtree_users)} hint="کل کاربران در محدوده شما" />
            <Metric label="سهمیه تست باقی‌مانده" value={fa(trialRemaining)} hint={`از ${fa(accountData.trial_quota)} سهمیه`} />
            <Metric label="ظرفیت ساخت ادمین" value={credit(accountData.admin_creation_remaining)} hint="ظرفیت باقی‌مانده برای زیرمجموعه" />
          </SimpleGrid>
        )}
      </Stack>
    </AppShell>
  );
};

export default Dashboard;
'''

USERS = '''import {
  Box,
  Button,
  Card,
  Collapse,
  HStack,
  Stack,
  Text,
  useBreakpointValue,
} from "@chakra-ui/react";
import { AppShell } from "components/AppShell";
import { DeleteUserModal } from "components/DeleteUserModal";
import { FiltersCompact, UserManagementControls } from "components/FiltersCompact";
import { QRCodeDialog } from "components/QRCodeDialog";
import { ResetUserUsageModal } from "components/ResetUserUsageModal";
import { RevokeSubscriptionModal } from "components/RevokeSubscriptionModal";
import { UserDialog } from "components/UserDialog";
import { UsersTablePro } from "components/UsersTablePro";
import { fetchInbounds, useDashboard } from "contexts/DashboardContext";
import { FC, useEffect, useState } from "react";

export const Users: FC = () => {
  const desktopUsersVisible = useBreakpointValue({ base: false, md: true }) ?? false;
  const [mobileUsersOpen, setMobileUsersOpen] = useState(true);

  useEffect(() => {
    useDashboard.getState().refetchUsers();
    fetchInbounds();
  }, []);

  return (
    <AppShell>
      <Stack spacing={5}>
        <Card
          px={{ base: 4, md: 5 }}
          py={{ base: 4, md: 5 }}
          bg="linear-gradient(145deg, var(--panel-surface), var(--panel-nested))"
          color="inherit"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="18px"
          boxShadow="var(--shadow-panel)"
        >
          <Text color="var(--panel-accent)" fontSize="11px" fontWeight="900">کاربران</Text>
          <Text as="h1" mt={1} fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900" letterSpacing="-0.04em">
            مدیریت کاربران
          </Text>
          <Text mt={2} color="var(--panel-text-muted)" fontSize="sm">
            ساخت، جست‌وجو، فیلتر و عملیات کاربران در فضای مستقل از داشبورد.
          </Text>
        </Card>

        <Box as="section" aria-labelledby="user-operations-title">
          <Card
            bg="var(--panel-surface)"
            color="inherit"
            borderWidth="1px"
            borderColor="var(--panel-border)"
            borderRadius="16px"
            boxShadow="var(--shadow-panel)"
            overflow="hidden"
          >
            <Stack px={{ base: 3, md: 4 }} pt={3.5} spacing={2.5}>
              <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
                <Box flex="1" minW={0}>
                  <Text id="user-operations-title" as="h2" fontSize="lg" fontWeight="850">عملیات کاربران</Text>
                  <Text mt={1} color="var(--panel-text-muted)" fontSize="11px">
                    اطلاعات، وضعیت، مصرف و عملیات هر کاربر بدون شلوغ‌کردن داشبورد اصلی.
                  </Text>
                </Box>
                <Button
                  display={{ base: "inline-flex", md: "none" }}
                  size="sm"
                  variant="ghost"
                  aria-expanded={mobileUsersOpen}
                  onClick={() => setMobileUsersOpen((value) => !value)}
                >
                  {mobileUsersOpen ? "بستن کاربران" : "نمایش کاربران"}
                </Button>
              </HStack>
              <Box pt={2.5} borderTopWidth="1px" borderColor="var(--panel-border)">
                <UserManagementControls />
              </Box>
            </Stack>

            <Collapse in={desktopUsersVisible || mobileUsersOpen} animateOpacity={false}>
              <FiltersCompact />
              <Box px={{ base: 3, md: 4 }} pb={4}>
                <UsersTablePro />
              </Box>
            </Collapse>
          </Card>
        </Box>
      </Stack>

      <UserDialog />
      <DeleteUserModal />
      <QRCodeDialog />
      <ResetUserUsageModal />
      <RevokeSubscriptionModal />
    </AppShell>
  );
};

export default Users;
'''

ROUTER = '''import { Navigate, createHashRouter, useRouteError } from "react-router-dom";
import { Alert, AlertIcon, Button, Center, Stack, Text } from "@chakra-ui/react";
import { ReactNode } from "react";
import { useQuery } from "react-query";
import useGetUser from "hooks/useGetUser";
import { AccountSummary } from "types/Admin";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";
import { Dashboard } from "./Dashboard";
import { Users } from "./Users";
import { Admins } from "./Admins";
import { Login } from "./Login";
import { AuditLogs } from "./AuditLogs";
import { DeviceLimits } from "./DeviceLimits";
import { Plans } from "./Plans";
import { Settings } from "./Settings";

const fetchAdminLoader = () => fetch("/admin", {
  headers: { Authorization: `Bearer ${getAuthToken()}` },
});

const OwnerOnly = ({ children }: { children: ReactNode }) => {
  const { userData, getUserIsPending } = useGetUser();
  if (getUserIsPending) return null;
  return userData.is_sudo || userData.role === "OWNER" ? <>{children}</> : <Navigate to="/" replace />;
};

const PlanManagerOnly = ({ children }: { children: ReactNode }) => {
  const { userData, getUserIsPending, getUserIsSuccess } = useGetUser();
  const account = useQuery<AccountSummary, Error>(
    "account-summary",
    () => fetch("/account/summary"),
    { enabled: getUserIsSuccess }
  );
  if (getUserIsPending || (getUserIsSuccess && account.isLoading)) return null;
  const isOwner = userData.is_sudo || userData.role === "OWNER";
  const canManagePlans = Boolean(
    account.data?.account_status === "ACTIVE" && account.data?.can_manage_plans
  );
  return isOwner || canManagePlans ? <>{children}</> : <Navigate to="/" replace />;
};

type RouteFailure = { status?: number; statusCode?: number; response?: { status?: number } };
const RouteError = () => {
  const error = useRouteError() as RouteFailure;
  const status = error?.statusCode ?? error?.status ?? error?.response?.status;
  if (status === 401 || !getAuthToken()) return <Login />;
  const isServiceFailure = typeof status === "number";
  return <Center minH="100vh" p={6}><Stack maxW="lg" spacing={4}>
    <Alert status="error"><AlertIcon />{isServiceFailure ? "Unable to reach the service" : "Unable to render this page"}</Alert>
    <Text>{isServiceFailure
      ? "The service may be unavailable. Your session has been kept; retry when the connection returns."
      : "The dashboard hit an unexpected interface error. Your session has been kept; retrying the page is safe."}</Text>
    <Button onClick={() => window.location.reload()}>Retry</Button>
  </Stack></Center>;
};

export const router = createHashRouter([
  { path: "/", element: <Dashboard />, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/users/", element: <Users />, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/login/", element: <Login /> },
  { path: "/admins/", element: <Admins />, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/device-limits/", element: <DeviceLimits />, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/plans/", element: <PlanManagerOnly><Plans /></PlanManagerOnly>, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/settings/", element: <OwnerOnly><Settings /></OwnerOnly>, errorElement: <RouteError />, loader: fetchAdminLoader },
  { path: "/audit-logs/", element: <AuditLogs />, errorElement: <RouteError />, loader: fetchAdminLoader },
]);
'''

write("app/dashboard/src/pages/Dashboard.tsx", DASHBOARD)
write("app/dashboard/src/pages/Users.tsx", USERS)
write("app/dashboard/src/pages/Router.tsx", ROUTER)

# Navigation: Dashboard and Users are distinct routes.
replace_once(
    "app/dashboard/src/components/Header.tsx",
    'const UsersNavIcon = chakra(UsersIcon, iconProps);',
    'const DashboardNavIcon = chakra(ChartPieIcon, iconProps);\nconst UsersNavIcon = chakra(UsersIcon, iconProps);',
)
replace_once(
    "app/dashboard/src/components/Header.tsx",
    '  const isAdminsPage = location.pathname.startsWith("/admins");\n  const isAuditPage = location.pathname.startsWith("/audit-logs");\n  const isDeviceLimitPage = location.pathname.startsWith("/device-limits");\n  const isPlansPage = location.pathname.startsWith("/plans");\n  const isSettingsPage = location.pathname.startsWith("/settings");\n  const isUsersPage = !isAdminsPage && !isAuditPage && !isDeviceLimitPage && !isPlansPage && !isSettingsPage;',
    '  const isDashboardPage = location.pathname === "/";\n  const isUsersPage = location.pathname.startsWith("/users");\n  const isAdminsPage = location.pathname.startsWith("/admins");\n  const isAuditPage = location.pathname.startsWith("/audit-logs");\n  const isDeviceLimitPage = location.pathname.startsWith("/device-limits");\n  const isPlansPage = location.pathname.startsWith("/plans");\n  const isSettingsPage = location.pathname.startsWith("/settings");',
)
mobile_users = '''        <Button
          as={Link}
          to="/"
          size="md"
          variant={isUsersPage ? "solid" : "ghost"}
          colorScheme={isUsersPage ? "primary" : "gray"}
          color={isUsersPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"}
          _hover={isUsersPage ? undefined : { bg: "var(--panel-row-hover)", color: "var(--panel-text)" }}
          leftIcon={<UsersNavIcon />}
          justifyContent="flex-start"
          aria-current={isUsersPage ? "page" : undefined}
        >{t("users")}</Button>'''
mobile_split = '''        <Button
          as={Link}
          to="/"
          size="md"
          variant={isDashboardPage ? "solid" : "ghost"}
          colorScheme={isDashboardPage ? "primary" : "gray"}
          color={isDashboardPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"}
          _hover={isDashboardPage ? undefined : { bg: "var(--panel-row-hover)", color: "var(--panel-text)" }}
          leftIcon={<DashboardNavIcon />}
          justifyContent="flex-start"
          aria-current={isDashboardPage ? "page" : undefined}
        >داشبورد</Button>
        <Button
          as={Link}
          to="/users/"
          size="md"
          variant={isUsersPage ? "solid" : "ghost"}
          colorScheme={isUsersPage ? "primary" : "gray"}
          color={isUsersPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"}
          _hover={isUsersPage ? undefined : { bg: "var(--panel-row-hover)", color: "var(--panel-text)" }}
          leftIcon={<UsersNavIcon />}
          justifyContent="flex-start"
          aria-current={isUsersPage ? "page" : undefined}
        >{t("users")}</Button>'''
replace_once("app/dashboard/src/components/Header.tsx", mobile_users, mobile_split)
replace_once(
    "app/dashboard/src/components/Header.tsx",
    '<Button as={Link} to="/" size="md" variant={isUsersPage ? "solid" : "ghost"} colorScheme={isUsersPage ? "primary" : "gray"} color={isUsersPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"} leftIcon={<UsersNavIcon />} justifyContent="flex-start" aria-current={isUsersPage ? "page" : undefined}>{t("users")}</Button>',
    '<Button as={Link} to="/" size="md" variant={isDashboardPage ? "solid" : "ghost"} colorScheme={isDashboardPage ? "primary" : "gray"} color={isDashboardPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"} leftIcon={<DashboardNavIcon />} justifyContent="flex-start" aria-current={isDashboardPage ? "page" : undefined}>داشبورد</Button>\n        <Button as={Link} to="/users/" size="md" variant={isUsersPage ? "solid" : "ghost"} colorScheme={isUsersPage ? "primary" : "gray"} color={isUsersPage ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"} leftIcon={<UsersNavIcon />} justifyContent="flex-start" aria-current={isUsersPage ? "page" : undefined}>{t("users")}</Button>',
)

# Backend pagination/count excludes the authenticated account itself.
replace_once(
    "app/db/crud.py",
    'def get_admins(db: Session,\n               offset: Optional[int] = None,\n               limit: Optional[int] = None,\n               username: Optional[str] = None,\n               scope_admin_id: Optional[int] = None) -> List[Admin]:',
    'def get_admins(db: Session,\n               offset: Optional[int] = None,\n               limit: Optional[int] = None,\n               username: Optional[str] = None,\n               scope_admin_id: Optional[int] = None,\n               exclude_admin_id: Optional[int] = None) -> List[Admin]:',
)
replace_once(
    "app/db/crud.py",
    '    if username:\n        query = query.filter(Admin.username.ilike(f\'%{username}%\'))\n    if offset:',
    '    if exclude_admin_id is not None:\n        query = query.filter(Admin.id != exclude_admin_id)\n    if username:\n        query = query.filter(Admin.username.ilike(f\'%{username}%\'))\n    if offset:',
)
replace_once(
    "app/db/crud.py",
    '    scope_admin_id: Optional[int] = None,\n    role: Optional[str] = None,',
    '    scope_admin_id: Optional[int] = None,\n    exclude_admin_id: Optional[int] = None,\n    role: Optional[str] = None,',
)
replace_once(
    "app/db/crud.py",
    '    if username:\n        query = query.filter(Admin.username.ilike(f"%{username}%"))\n    if role:',
    '    if exclude_admin_id is not None:\n        query = query.filter(Admin.id != exclude_admin_id)\n    if username:\n        query = query.filter(Admin.username.ilike(f"%{username}%"))\n    if role:',
)
replace_once(
    "app/routers/admin.py",
    '    return crud.get_admins(db, offset, limit, username, scope_admin_id=scope_admin_id)',
    '    return crud.get_admins(\n        db, offset, limit, username,\n        scope_admin_id=scope_admin_id,\n        exclude_admin_id=actor.id if actor is not None else None,\n    )',
)
replace_once(
    "app/routers/admin.py",
    '        scope_admin_id=scope_admin_id,\n        role=role,',
    '        scope_admin_id=scope_admin_id,\n        exclude_admin_id=actor.id if actor is not None else None,\n        role=role,',
)

# Regression coverage for pagination/count semantics.
replace_once(
    "tests/test_admin_management.py",
    '    assert total == 3\n    assert [admin.username for admin in admins] == ["middle", "alpha"]\n\n\ndef test_policy_rejects_negative_or_unknown_volume_rules():',
    '''    assert total == 3
    assert [admin.username for admin in admins] == ["middle", "alpha"]


def test_management_list_excludes_current_admin_from_count_and_page(session):
    actor = crud.create_admin(
        session,
        AdminCreate(username="actor", password="secret", is_sudo=False),
    )
    for username in ("child-a", "child-b"):
        crud.create_admin(
            session,
            AdminCreate(username=username, password="secret", is_sudo=False),
        )

    admins, total = crud.get_admins_with_count(
        session,
        offset=0,
        limit=20,
        exclude_admin_id=actor.id,
    )
    legacy_admins = crud.get_admins(
        session,
        exclude_admin_id=actor.id,
    )

    assert total == 2
    assert {admin.username for admin in admins} == {"child-a", "child-b"}
    assert all(admin.id != actor.id for admin in legacy_admins)


def test_policy_rejects_negative_or_unknown_volume_rules():''',
)

# UI contract: Dashboard and Users are separate, and Admin self dashboard does not expose commercial-mode labels.
contracts = read("app/dashboard/scripts/test-stage1-ui-contracts.cjs")
contracts = contracts.replace(
    'const router = read("src/pages/Router.tsx");\nconst header = read("src/components/Header.tsx");',
    'const router = read("src/pages/Router.tsx");\nconst dashboard = read("src/pages/Dashboard.tsx");\nconst usersPage = read("src/pages/Users.tsx");\nconst header = read("src/components/Header.tsx");',
    1,
)
anchor = '// Plans must use the same active-account + can_manage_plans contract across page, route and navigation.\n'
addition = '''// Dashboard and Users must remain distinct surfaces.
assert.ok(router.includes('path: "/users/"'), "Users must have a dedicated route");
assert.ok(header.includes('to="/users/"'), "Navigation must expose the dedicated Users route");
assert.ok(dashboard.includes("مانده اعتبار"), "Admin dashboard must expose remaining credit");
assert.ok(dashboard.includes("اعتبار مالی"), "Admin dashboard must expose account credit");
assert.ok(!dashboard.includes("UserManagementControls"), "Dashboard must not embed user management controls");
assert.ok(usersPage.includes("UserManagementControls"), "Users page must own user management controls");
assert.ok(usersPage.includes("UsersTablePro"), "Users page must own the users table");
for (const hiddenCommercialLabel of ["بر اساس حجم مصرفی", "بر اساس حجم ساخته‌شده", "طبق پلن · سقف اکانت"]) {
  assert.ok(!dashboard.includes(hiddenCommercialLabel), `Admin self dashboard must hide commercial mode label: ${hiddenCommercialLabel}`);
}

'''
if anchor not in contracts:
    raise SystemExit("Stage 1 contract anchor missing")
contracts = contracts.replace(anchor, addition + anchor, 1)
write("app/dashboard/scripts/test-stage1-ui-contracts.cjs", contracts)

print("v1.1.6 workspace patch applied")
