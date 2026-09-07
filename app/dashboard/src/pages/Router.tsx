import { Navigate, createHashRouter, useRouteError } from "react-router-dom";
import { Alert, AlertIcon, Button, Center, Stack, Text } from "@chakra-ui/react";
import { ReactNode } from "react";
import { useQuery } from "react-query";
import useGetUser from "hooks/useGetUser";
import { AccountSummary } from "types/Admin";
import { fetch } from "../service/http";
import { getAuthToken } from "../utils/authStorage";
import { Dashboard } from "./Dashboard";
import { Admins } from "./Admins";
import { Login } from "./Login";
import { AuditLogs } from "./AuditLogs";
import { DeviceLimits } from "./DeviceLimits";
import { Plans } from "./Plans";
import { Settings } from "./Settings";
const fetchAdminLoader = () => {
    return fetch("/admin", {
        headers: {
            Authorization: `Bearer ${getAuthToken()}`,
        },
    });
};
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
const RouteError = () => {
    const error = useRouteError() as { status?: number; statusCode?: number; response?: { status?: number } };
    const status = error?.statusCode ?? error?.status ?? error?.response?.status;
    if (status === 401 || !getAuthToken()) return <Login />;
    return <Center minH="100vh" p={6}><Stack maxW="lg" spacing={4}>
        <Alert status="error"><AlertIcon />Unable to load this page</Alert>
        <Text>The service may be unavailable. Your session has been kept; retry when the connection returns.</Text>
        <Button onClick={() => window.location.reload()}>Retry</Button>
    </Stack></Center>;
};
export const router = createHashRouter([
    {
        path: "/",
        element: <Dashboard />,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
    {
        path: "/login/",
        element: <Login />,
    },
    {
        path: "/admins/",
        element: <Admins />,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
    {
        path: "/device-limits/",
        element: <DeviceLimits />,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
    {
        path: "/plans/",
        element: <PlanManagerOnly><Plans /></PlanManagerOnly>,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
    {
        path: "/settings/",
        element: <OwnerOnly><Settings /></OwnerOnly>,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
    {
        path: "/audit-logs/",
        element: <AuditLogs />,
        errorElement: <RouteError />,
        loader: fetchAdminLoader,
    },
]);
