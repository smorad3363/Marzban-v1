import {
  Box,
  HStack,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import {
  ChartBarIcon,
  ClockIcon,
  SignalIcon,
  UserGroupIcon,
} from "@heroicons/react/24/outline";
import { FC, ReactElement } from "react";
import { useQuery } from "react-query";
import { fetch } from "service/http";

const UsersIcon = chakra(UserGroupIcon, { baseStyle: { w: 5, h: 5 } });
const OnlineIcon = chakra(SignalIcon, { baseStyle: { w: 5, h: 5 } });
const ExpiringIcon = chakra(ClockIcon, { baseStyle: { w: 5, h: 5 } });
const UsageIcon = chakra(ChartBarIcon, { baseStyle: { w: 5, h: 5 } });

type UsersSummary = {
  total_users: number;
  online_users: number;
  expiring_users: number;
  high_usage_users: number;
  online_window_hours: number;
  expiring_within_days: number;
  high_usage_threshold_percent: number;
};

type Tone = "primary" | "blue" | "warning" | "danger";

const tones: Record<Tone, { color: string; bg: string; border: string }> = {
  primary: {
    color: "var(--panel-accent)",
    bg: "var(--panel-accent-soft)",
    border: "var(--panel-accent-border)",
  },
  blue: {
    color: "var(--panel-info)",
    bg: "var(--panel-info-soft)",
    border: "var(--panel-info-border)",
  },
  warning: {
    color: "var(--panel-warning)",
    bg: "var(--panel-warning-soft)",
    border: "var(--panel-warning-border)",
  },
  danger: {
    color: "var(--panel-danger)",
    bg: "var(--panel-danger-soft)",
    border: "var(--panel-danger-border)",
  },
};

const SummaryCard: FC<{
  title: string;
  value?: number;
  description: string;
  icon: ReactElement;
  tone: Tone;
  loading: boolean;
  failed: boolean;
}> = ({ title, value, description, icon, tone, loading, failed }) => {
  const palette = tones[tone];
  return (
    <Box
      minW={0}
      px={{ base: 3.5, md: 4 }}
      py={{ base: 3.5, md: 4 }}
      bg="linear-gradient(145deg, var(--panel-surface), var(--panel-nested))"
      borderWidth="1px"
      borderColor="var(--panel-border)"
      borderRadius="16px"
      boxShadow="var(--shadow-panel)"
    >
      <HStack align="start" justify="space-between" spacing={3}>
        <Stack spacing={1} minW={0}>
          <Text color="var(--panel-text-muted)" fontSize="10px" fontWeight="800">
            {title}
          </Text>
          {loading ? (
            <Skeleton h="30px" w="82px" borderRadius="8px" />
          ) : (
            <Text
              fontSize={{ base: "xl", md: "2xl" }}
              lineHeight="1.2"
              fontWeight="900"
              letterSpacing="-0.03em"
            >
              {failed ? "—" : (value ?? 0).toLocaleString("fa-IR")}
            </Text>
          )}
          <Text color="var(--panel-text-muted)" fontSize="9px" lineHeight="1.7" noOfLines={2}>
            {description}
          </Text>
        </Stack>
        <Box
          display="grid"
          placeItems="center"
          boxSize="42px"
          flexShrink={0}
          borderRadius="13px"
          color={palette.color}
          bg={palette.bg}
          borderWidth="1px"
          borderColor={palette.border}
        >
          {icon}
        </Box>
      </HStack>
    </Box>
  );
};

export const UserSummaryCards: FC = () => {
  const summary = useQuery<UsersSummary, Error>(
    ["users-summary"],
    () => fetch("/users/summary"),
    {
      staleTime: 15_000,
      refetchInterval: 30_000,
      refetchOnWindowFocus: true,
    }
  );

  const data = summary.data;
  const loading = summary.isLoading && !data;
  const failed = summary.isError && !data;

  return (
    <SimpleGrid columns={{ base: 1, sm: 2, xl: 4 }} gap={3} aria-live="polite">
      <SummaryCard
        title="کل کاربران"
        value={data?.total_users}
        description="تمام کاربران قابل مشاهده در محدوده دسترسی شما"
        icon={<UsersIcon />}
        tone="primary"
        loading={loading}
        failed={failed}
      />
      <SummaryCard
        title="آنلاین الآن"
        value={data?.online_users}
        description={`طبق تعریف فعلی سیستم در ${data?.online_window_hours ?? 24} ساعت اخیر`}
        icon={<OnlineIcon />}
        tone="blue"
        loading={loading}
        failed={failed}
      />
      <SummaryCard
        title="نزدیک انقضا"
        value={data?.expiring_users}
        description={`انقضا در ${data?.expiring_within_days ?? "—"} روز آینده`}
        icon={<ExpiringIcon />}
        tone="warning"
        loading={loading}
        failed={failed}
      />
      <SummaryCard
        title="حجم رو به اتمام"
        value={data?.high_usage_users}
        description={`مصرف حداقل ${data?.high_usage_threshold_percent ?? "—"}٪ از سقف ترافیک`}
        icon={<UsageIcon />}
        tone="danger"
        loading={loading}
        failed={failed}
      />
    </SimpleGrid>
  );
};

export default UserSummaryCards;
