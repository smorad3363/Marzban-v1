import { Badge, Box, Card, HStack, Stack, Text } from "@chakra-ui/react";
import { AppShell } from "components/AppShell";
import { CoreSettingsModal } from "components/CoreSettingsModal";
import { DashboardOverviewCompact } from "components/DashboardOverviewCompact";
import { DeleteUserModal } from "components/DeleteUserModal";
import { FiltersCompact } from "components/FiltersCompact";
import { HostsDialog } from "components/HostsDialog";
import { NodesDialog } from "components/NodesModal";
import { NodesUsage } from "components/NodesUsage";
import { QRCodeDialog } from "components/QRCodeDialog";
import { ResetAllUsageModal } from "components/ResetAllUsageModal";
import { ResetUserUsageModal } from "components/ResetUserUsageModal";
import { RevokeSubscriptionModal } from "components/RevokeSubscriptionModal";
import { UserDialog } from "components/UserDialog";
import { UsersTablePro } from "components/UsersTablePro";
import { fetchInbounds, useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect } from "react";

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

export const Dashboard: FC = () => {
  const { userData } = useGetUser();
  const isOwner = userData.role === "OWNER" || userData.is_sudo;
  const today = new Date();

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
              <Text mt={1} color="gray.400" fontSize="12px">مرکز مدیریت کاربران و سرویس‌های Marzban</Text>
            </Box>
            <HStack spacing={3} flexWrap="wrap">
              <Badge colorScheme="green" px={2.5} py={1.5} borderRadius="full" fontSize="10px">سیستم در حال اجرا</Badge>
              <Text color="gray.400" fontSize="11px">{messageForToday()}</Text>
              <Text color="gray.300" fontSize="11px" fontWeight="700">
                {today.toLocaleDateString("fa-IR-u-ca-persian", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
              </Text>
              <Text dir="ltr" color="blue.300" fontSize="11px" fontWeight="800">
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
            borderColor="rgba(148,163,184,.14)"
            borderRadius="14px"
            boxShadow="0 16px 42px rgba(0,0,0,.22)"
            overflow="hidden"
          >
            <Box px={{ base: 3, md: 4 }} pt={3.5}>
              <Text color="primary.300" fontSize="10px" fontWeight="800">کاربران</Text>
              <Text id="user-operations-title" as="h2" mt={0.5} fontSize="lg" fontWeight="850">مدیریت کاربران</Text>
              <Text mt={1} color="gray.500" fontSize="11px">اطلاعات مهم، وضعیت، مصرف و عملیات هر کاربر بدون باز کردن پنجره اضافی.</Text>
            </Box>
            <FiltersCompact />
            <Box px={{ base: 3, md: 4 }} pb={4}>
              <UsersTablePro />
            </Box>
          </Card>
        </Box>
      </Stack>

      <UserDialog />
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
