import {
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
