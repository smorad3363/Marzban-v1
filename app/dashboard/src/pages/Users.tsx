import { PageHeader } from "design-system/Console";
import {
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
import { UserSummaryCards } from "components/UserSummaryCards";
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
        <PageHeader eyebrow="مدیریت سرویس" title="مدیریت کاربران" description="وضعیت، مصرف و دسترسی کاربران؛ همه در یک فضای منظم." />

        <UserSummaryCards />

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
                  <Text id="user-operations-title" as="h2" fontSize="lg" fontWeight="700">عملیات کاربران</Text>
                  <Text mt={1} color="var(--panel-text-muted)" fontSize="xs">
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
