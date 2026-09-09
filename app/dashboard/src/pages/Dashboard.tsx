import { AppShell } from "components/AppShell";
import { DashboardOverview } from "components/DashboardOverview";
import { FC } from "react";

export const Dashboard: FC = () => (
  <AppShell>
    <DashboardOverview />
  </AppShell>
);

export default Dashboard;
