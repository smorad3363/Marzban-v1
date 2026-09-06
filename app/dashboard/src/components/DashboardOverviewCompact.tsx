import { Badge, Box, Card, HStack, Progress, SimpleGrid, Skeleton, Stack, Text, chakra } from "@chakra-ui/react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CpuChipIcon,
  ServerStackIcon,
  SignalIcon,
  UserGroupIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, ReactElement } from "react";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { DashboardOverview } from "types/Dashboard";
import { formatBytes } from "utils/formatByte";

const UsersIconView = chakra(UsersIcon, { baseStyle: { w: 5, h: 5 } });
const ActiveIcon = chakra(UserGroupIcon, { baseStyle: { w: 5, h: 5 } });
const OnlineIcon = chakra(SignalIcon, { baseStyle: { w: 5, h: 5 } });
const ServerIcon = chakra(ServerStackIcon, { baseStyle: { w: 5, h: 5 } });
const CpuIcon = chakra(CpuChipIcon, { baseStyle: { w: 4, h: 4 } });
const UpIcon = chakra(ArrowUpIcon, { baseStyle: { w: 3.5, h: 3.5 } });
const DownIcon = chakra(ArrowDownIcon, { baseStyle: { w: 3.5, h: 3.5 } });

const fa = (value: number) => value.toLocaleString("fa-IR");

type SystemStats = {
  version: string;
  mem_total: number;
  mem_used: number;
  cpu_usage: number;
  incoming_bandwidth_speed: number;
  outgoing_bandwidth_speed: number;
};

const Kpi: FC<{
  label: string;
  value: string;
  hint: string;
  icon: ReactElement;
  tone?: string;
}> = ({ label, value, hint, icon, tone = "var(--panel-text)" }) => (
  <Card
    p={3.5}
    minH="96px"
    bg="var(--panel-surface)"
    color="inherit"
    borderWidth="1px"
    borderColor="var(--panel-border)"
    borderRadius="12px"
    boxShadow="none"
  >
    <HStack justify="space-between" align="start" gap={3}>
      <Box minW={0}>
        <Text color="var(--panel-text-muted)" fontSize="11px" fontWeight="700">{label}</Text>
        <Text mt={1} color={tone} fontSize={{ base: "xl", md: "2xl" }} fontWeight="850" sx={{ fontVariantNumeric: "tabular-nums" }}>
          {value}
        </Text>
        <Text mt={1} color="var(--panel-text-muted)" fontSize="10px" noOfLines={1}>{hint}</Text>
      </Box>
      <Box
        flexShrink={0}
        p={2}
        color="var(--panel-accent)"
        bg="var(--panel-nested)"
        borderWidth="1px"
        borderColor="var(--panel-border)"
        borderRadius="9px"
      >
        {icon}
      </Box>
    </HStack>
  </Card>
);

export const DashboardOverviewCompact: FC = () => {
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = userData.role === "OWNER" || userData.is_sudo;
  const timezoneOffset = -new Date().getTimezoneOffset();
  const { version } = useDashboard();

  const overview = useQuery<DashboardOverview, Error>(
    ["dashboard-overview-compact", timezoneOffset],
    () => fetch(`/dashboard/overview?timezone_offset_minutes=${timezoneOffset}`),
    { enabled: getUserIsSuccess, refetchInterval: 30000 }
  );

  const system = useQuery<SystemStats, Error>(
    "statistics-query-key",
    () => fetch("/system"),
    {
      enabled: getUserIsSuccess && isOwner,
      refetchInterval: 10000,
      onSuccess: ({ version: currentVersion }) => {
        if (version !== currentVersion) useDashboard.setState({ version: currentVersion });
      },
    }
  );

  if (overview.isLoading || !overview.data) {
    return <Skeleton height="205px" borderRadius="14px" mb={3} />;
  }

  const data = overview.data;
  const traffic = data.current_used_traffic ?? 0;
  const cpu = Math.max(0, Math.min(100, system.data?.cpu_usage ?? 0));
  const memPercent = system.data?.mem_total
    ? Math.max(0, Math.min(100, (system.data.mem_used / system.data.mem_total) * 100))
    : 0;

  return (
    <Stack spacing={3} mb={3}>
      <SimpleGrid columns={{ base: 2, lg: isOwner ? 5 : 4 }} gap={3}>
        {isOwner && (
          <Kpi
            label="وضعیت سرور"
            value={system.isError ? "نامشخص" : "سالم"}
            hint={system.data?.version ? `Marzban v${system.data.version}` : "سرویس اصلی در دسترس است"}
            icon={<ServerIcon />}
            tone={system.isError ? "var(--panel-warning)" : "var(--panel-success)"}
          />
        )}
        <Kpi label="کل کاربران" value={fa(data.total_users)} hint="کاربران قابل مشاهده" icon={<UsersIconView />} />
        <Kpi label="کاربران فعال" value={fa(data.active_users)} hint={`از ${fa(data.total_users)} کاربر`} icon={<ActiveIcon />} tone="var(--panel-success)" />
        <Kpi label="کاربران آنلاین" value={fa(data.online_users)} hint="اتصال در ۲۴ ساعت اخیر" icon={<OnlineIcon />} tone="var(--panel-accent)" />
        <Kpi label="ترافیک مصرفی" value={String(formatBytes(traffic))} hint="مصرف ثبت‌شده در محدوده شما" icon={<UpIcon />} />
      </SimpleGrid>

      {isOwner && system.data && (
        <Card
          px={3.5}
          py={2.5}
          bg="var(--panel-surface)"
          color="inherit"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="12px"
        >
          <SimpleGrid columns={{ base: 1, md: 4 }} gap={3} alignItems="center">
            <Box>
              <HStack spacing={2}>
                <ServerIcon />
                <Text fontSize="12px" fontWeight="800">وضعیت سیستم</Text>
                <Badge colorScheme="green" fontSize="9px">فعال</Badge>
              </HStack>
            </Box>
            <Box>
              <HStack justify="space-between"><HStack spacing={1.5}><CpuIcon /><Text fontSize="11px" color="var(--panel-text-muted)">CPU</Text></HStack><Text fontSize="11px" fontWeight="800">{fa(Math.round(cpu))}٪</Text></HStack>
              <Progress mt={1.5} value={cpu} size="xs" borderRadius="full" colorScheme={cpu > 85 ? "red" : cpu > 70 ? "orange" : "green"} />
            </Box>
            <Box>
              <HStack justify="space-between"><Text fontSize="11px" color="var(--panel-text-muted)">حافظه</Text><Text fontSize="11px" fontWeight="800">{String(formatBytes(system.data.mem_used))}</Text></HStack>
              <Progress mt={1.5} value={memPercent} size="xs" borderRadius="full" colorScheme={memPercent > 85 ? "red" : memPercent > 70 ? "orange" : "green"} />
            </Box>
            <HStack justify={{ base: "start", md: "end" }} spacing={4}>
              <HStack spacing={1}><DownIcon color="var(--panel-accent)" /><Text dir="ltr" fontSize="11px" fontWeight="800">{String(formatBytes(system.data.incoming_bandwidth_speed))}/s</Text></HStack>
              <HStack spacing={1}><UpIcon color="var(--panel-accent)" /><Text dir="ltr" fontSize="11px" fontWeight="800">{String(formatBytes(system.data.outgoing_bandwidth_speed))}/s</Text></HStack>
            </HStack>
          </SimpleGrid>
        </Card>
      )}
    </Stack>
  );
};

export default DashboardOverviewCompact;
