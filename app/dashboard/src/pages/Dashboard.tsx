import {
  Badge,
  Box,
  Button,
  Card,
  Collapse,
  HStack,
  Stack,
  Text,
  useBreakpointValue,
  useDisclosure,
} from "@chakra-ui/react";
import { AdminFormDrawer } from "components/AdminFormDrawer";
import { AppShell } from "components/AppShell";
import { CoreSettingsModal } from "components/CoreSettingsModal";
import { DashboardOverviewCompact } from "components/DashboardOverviewCompact";
import { DeleteUserModal } from "components/DeleteUserModal";
import { FiltersCompact, UserManagementControls } from "components/FiltersCompact";
import { HostsDialog } from "components/HostsDialog";
import { NodesDialog } from "components/NodesModal";
import { NodesUsage } from "components/NodesUsage";
import { PlanCreateModal } from "components/PlanCreateModal";
import { QRCodeDialog } from "components/QRCodeDialog";
import { ResetAllUsageModal } from "components/ResetAllUsageModal";
import { ResetUserUsageModal } from "components/ResetUserUsageModal";
import { RevokeSubscriptionModal } from "components/RevokeSubscriptionModal";
import { UserDialog } from "components/UserDialog";
import { UsersTablePro } from "components/UsersTablePro";
import { fetchInbounds, useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect, useState } from "react";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities } from "types/Admin";

const shortMessages = [
  "همه‌چیز تحت کنترل است؛ پایدار ادامه بده.",
  "مدیریت خوب یعنی تصمیم سریع با داده درست.",
  "وضعیت روشن، تصمیم بهتر، سرویس پایدارتر.",
  "هر تغییر کوچک، کیفیت سرویس را بهتر می‌کند.",
];

const messageForToday = () => {
  const now = new Date();
  const key = now.getFullYear() * 372 + (now.getMonth() + 1) * 31 + now.getDate();
  return shortMessages[key % shortMessages.length];
};

const calendarParts = (date: Date, calendar: "persian" | "islamic") => {
  const parts = new Intl.DateTimeFormat(`en-US-u-ca-${calendar}`, { month: "numeric", day: "numeric" }).formatToParts(date);
  return {
    month: Number(parts.find((item) => item.type === "month")?.value || 0),
    day: Number(parts.find((item) => item.type === "day")?.value || 0),
  };
};

const iranHoliday = (date: Date) => {
  if (date.getDay() === 5) return "تعطیل هفتگی جمعه";
  const solar = calendarParts(date, "persian");
  const fixed: Record<string, string> = {
    "1/1": "نوروز", "1/2": "نوروز", "1/3": "نوروز", "1/4": "نوروز",
    "1/12": "روز جمهوری اسلامی", "1/13": "روز طبیعت", "3/14": "رحلت امام خمینی",
    "3/15": "قیام پانزده خرداد", "11/22": "پیروزی انقلاب اسلامی", "12/29": "ملی‌شدن صنعت نفت",
  };
  if (fixed[`${solar.month}/${solar.day}`]) return fixed[`${solar.month}/${solar.day}`];
  const lunar = calendarParts(date, "islamic");
  const religious: Record<string, string> = {
    "1/9": "تاسوعا", "1/10": "عاشورا", "2/20": "اربعین", "2/28": "رحلت پیامبر",
    "2/30": "شهادت امام رضا", "3/17": "میلاد پیامبر", "6/3": "شهادت حضرت فاطمه",
    "7/13": "میلاد امام علی", "7/27": "مبعث", "8/15": "نیمه شعبان",
    "9/21": "شهادت امام علی", "10/1": "عید فطر", "10/2": "تعطیل عید فطر",
    "12/10": "عید قربان", "12/18": "عید غدیر",
  };
  return religious[`${lunar.month}/${lunar.day}`] || null;
};

export const Dashboard: FC = () => {
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = userData.role === "OWNER" || userData.is_sudo;
  const adminCreate = useDisclosure();
  const planCreate = useDisclosure();
  const desktopUsersVisible = useBreakpointValue({ base: false, md: true }) ?? false;
  const [mobileUsersOpen, setMobileUsersOpen] = useState(true);
  const today = new Date();
  const holiday = iranHoliday(today);

  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities"),
    { enabled: getUserIsSuccess }
  );
  const account = useQuery<AccountSummary, Error>(
    ["account-summary", userData.username],
    () => fetch("/account/summary"),
    { enabled: getUserIsSuccess }
  );

  const accountActive = account.data?.account_status === "ACTIVE";
  const canCreateAdmin = Boolean(accountActive && capabilities.data?.can_create_admins);
  const canCreatePlan = Boolean(accountActive && (account.data?.role === "OWNER" || account.data?.can_manage_plans));

  useEffect(() => {
    useDashboard.getState().refetchUsers();
    fetchInbounds();
  }, []);

  return (
    <AppShell>
      <Stack spacing={3}>
        <Card
          as="header"
          px={{ base: 3.5, md: 4 }}
          py={3}
          bg="linear-gradient(145deg, var(--panel-surface), var(--panel-nested))"
          color="inherit"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="12px"
        >
          <HStack justify="space-between" align="center" gap={4} flexWrap="wrap">
            <Box minW={0}>
              <Text as="h1" fontSize={{ base: "xl", md: "2xl" }} fontWeight="850" letterSpacing="-0.035em">
                خوش آمدی، <Text as="span" dir="ltr">{userData.username}</Text>
              </Text>
            </Box>
            <HStack spacing={2} flexWrap="wrap" justify="end">
              {canCreateAdmin && (
                <Button size="sm" h="34px" variant="outline" borderColor="var(--panel-border)" onClick={adminCreate.onOpen}>
                  ساخت ادمین
                </Button>
              )}
              {canCreatePlan && (
                <Button size="sm" h="34px" variant="outline" borderColor="var(--panel-border)" onClick={planCreate.onOpen}>
                  ساخت پلن
                </Button>
              )}
              <Badge colorScheme="green" px={2.5} py={1.5} borderRadius="full" fontSize="10px">سیستم در حال اجرا</Badge>
              <Text color="var(--panel-text-muted)" fontSize="11px">{messageForToday()}</Text>
              <Badge colorScheme={holiday ? "orange" : "green"} px={2} py={1} borderRadius="full" fontSize="9px">
                {holiday || "روز کاری"}
              </Badge>
              <Text color="var(--panel-text-body)" fontSize="11px" fontWeight="700">
                {today.toLocaleDateString("fa-IR-u-ca-persian", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
              </Text>
              <Text dir="ltr" color="var(--panel-accent)" fontSize="11px" fontWeight="800">
                {today.toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit", hour12: false })}
              </Text>
            </HStack>
          </HStack>
        </Card>

        <DashboardOverviewCompact />

        <Box as="section" aria-labelledby="user-operations-title">
          <Card
            bg="var(--panel-surface)"
            color="inherit"
            borderWidth="1px"
            borderColor="var(--panel-border)"
            borderRadius="14px"
            boxShadow="var(--shadow-panel)"
            overflow="hidden"
          >
            <Stack px={{ base: 3, md: 4 }} pt={3.5} spacing={2.5}>
              <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
                <Box flex="1" minW={0}>
                  <Text color="var(--panel-accent)" fontSize="10px" fontWeight="800">کاربران</Text>
                  <Text id="user-operations-title" as="h2" mt={0.5} fontSize="lg" fontWeight="850">
                    مدیریت کاربران
                  </Text>
                  <Text mt={1} color="var(--panel-text-muted)" fontSize="11px">
                    اطلاعات مهم، وضعیت، مصرف و عملیات هر کاربر بدون باز کردن پنجره اضافی.
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
      <AdminFormDrawer isOpen={adminCreate.isOpen} admin={null} onClose={adminCreate.onClose} />
      <PlanCreateModal isOpen={planCreate.isOpen} isOwner={isOwner} onClose={planCreate.onClose} />
      <DeleteUserModal />
      <QRCodeDialog />
      <ResetUserUsageModal />
      <RevokeSubscriptionModal />
      {isOwner && (
        <>
          <HostsDialog />
          <NodesDialog />
          <NodesUsage />
          <ResetAllUsageModal />
          <CoreSettingsModal />
        </>
      )}
    </AppShell>
  );
};

export default Dashboard;
