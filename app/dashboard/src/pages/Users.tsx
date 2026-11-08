import { PageHeader } from "design-system/Console";
import { Box, Button, Card, Stack } from "@chakra-ui/react";
import { ChartBarIcon } from "@heroicons/react/24/outline";
import { AppShell } from "components/AppShell";
import { DeleteUserModal } from "components/DeleteUserModal";
import { FiltersCompact } from "components/FiltersCompact";
import { QRCodeDialog } from "components/QRCodeDialog";
import { ResetUserUsageModal } from "components/ResetUserUsageModal";
import { RevokeSubscriptionModal } from "components/RevokeSubscriptionModal";
import { UserDialog } from "components/UserDialog";
import { WorkspaceSummary } from "components/WorkspaceSummary";
import { UsersTablePro } from "components/UsersTablePro";
import { fetchInbounds, useDashboard } from "contexts/DashboardContext";
import { FC, Suspense, lazy, useEffect, useState } from "react";
const Analytics = lazy(() => import("components/DashboardOverview"));

export const Users: FC = () => {
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  useEffect(() => { useDashboard.getState().refetchUsers(); fetchInbounds(); }, []);
  return <AppShell>
    <Stack spacing={3}>
      <PageHeader title="کاربران" actions={<Button size="sm" variant="outline" leftIcon={<ChartBarIcon width={16} />} aria-expanded={analyticsOpen} aria-controls="users-analytics" onClick={() => setAnalyticsOpen(v => !v)}>{analyticsOpen ? "بستن آمار" : "آمار و نمودارها"}</Button>} />
      <WorkspaceSummary />
      <Box id="users-analytics" hidden={!analyticsOpen}>{analyticsOpen && <Suspense fallback={<Box p={4} role="status">در حال دریافت آمار…</Box>}><Analytics embedded /></Suspense>}</Box>
      <Card as="section" aria-label="مدیریت کاربران" bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" boxShadow="var(--shadow-panel)" overflow="hidden">
        <FiltersCompact />
        <Box px={{ base: 2, md: 3 }} pb={3}><UsersTablePro /></Box>
      </Card>
    </Stack>
    <UserDialog /><DeleteUserModal /><QRCodeDialog /><ResetUserUsageModal /><RevokeSubscriptionModal />
  </AppShell>;
};
export default Users;
