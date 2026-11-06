import { EmptyState, Metric, PageHeader, SectionHeader, Surface, useChartPalette } from "design-system/Console";
import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Card,
  HStack,
  Progress,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import {
  ChartBarIcon,
  CheckCircleIcon,
  CircleStackIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  ServerStackIcon,
  SignalIcon,
  UserGroupIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import type { ApexOptions } from "apexcharts";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, ReactElement, useMemo, useState } from "react";
import Chart from "react-apexcharts";
import { useQuery } from "react-query";
import { useNavigate } from "react-router-dom";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities } from "types/Admin";
import {
  DashboardAttentionUser,
  DashboardOverview as DashboardOverviewData,
  DashboardRange,
  DashboardUserSummary,
} from "types/Dashboard";
import { CreateUserFromPlan } from "./CreateUserFromPlan";

const iconStyle = { baseStyle: { w: 5, h: 5 } };
const UsersMetricIcon = chakra(UsersIcon, iconStyle);
const OnlineMetricIcon = chakra(SignalIcon, iconStyle);
const ActiveMetricIcon = chakra(CheckCircleIcon, iconStyle);
const AttentionMetricIcon = chakra(ExclamationTriangleIcon, iconStyle);
const TrafficMetricIcon = chakra(ChartBarIcon, iconStyle);
const CreditMetricIcon = chakra(CircleStackIcon, iconStyle);
const NodeIcon = chakra(ServerStackIcon, iconStyle);
const AdminIcon = chakra(UserGroupIcon, iconStyle);
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });

const fa = (value: number) => Number(value || 0).toLocaleString("fa-IR");
const toman = (value: number | null | undefined) => value == null ? "نامحدود" : `${fa(value)} تومان`;
const credit = (value: number | null | undefined) => value == null ? "نامحدود" : fa(Number(value));
const parseUtcDate = (value: string) => new Date(/(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`);

const formatTraffic = (value?: number | null) => {
  const amount = Number(value || 0);
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  if (amount <= 0) return "۰ B";
  const index = Math.min(Math.floor(Math.log(amount) / Math.log(1024)), units.length - 1);
  const normalized = amount / 1024 ** index;
  return `${normalized.toLocaleString("fa-IR", { maximumFractionDigits: index >= 3 ? 2 : 1 })} ${units[index]}`;
};

const statusLabel = (status: string) => ({
  active: "فعال",
  disabled: "غیرفعال",
  expired: "منقضی",
  limited: "محدود",
  on_hold: "در انتظار",
}[status] || status);

const reasonLabel = (item: DashboardAttentionUser) => {
  if (item.reason_code === "expired") return "منقضی شده";
  if (item.reason_code === "limited") return "سقف مصرف تمام شده";
  if (item.reason_code === "traffic_exhausted") return "حجم تمام شده";
  if (item.reason_code === "device_limit") return "محدودیت دستگاه";
  if (item.reason_code === "traffic_near_limit") return item.usage_percent == null ? "مصرف بالا" : `حجم ${fa(Math.round(item.usage_percent))}٪`;
  if (item.reason_code === "expires_soon" && item.expire) {
    const seconds = Math.max(0, item.expire - Date.now() / 1000);
    const hours = Math.ceil(seconds / 3600);
    return hours < 24 ? `${fa(hours)} ساعت تا انقضا` : `${fa(Math.ceil(hours / 24))} روز تا انقضا`;
  }
  return "نیازمند بررسی";
};

const relativeTime = (value: string) => {
  const timestamp = parseUtcDate(value).getTime();
  if (!Number.isFinite(timestamp)) return "—";
  const seconds = Math.max(0, (Date.now() - timestamp) / 1000);
  if (seconds < 3600) return `${fa(Math.max(1, Math.round(seconds / 60)))} دقیقه پیش`;
  if (seconds < 86400) return `${fa(Math.round(seconds / 3600))} ساعت پیش`;
  return `${fa(Math.round(seconds / 86400))} روز پیش`;
};

const Panel: FC<{ children: React.ReactNode; minH?: string | number }> = ({ children, minH }) => <Surface minH={minH} p={{ base: 4, md: 5 }}>{children}</Surface>;
const MetricCard: FC<{ label: string; value: string; hint: string; icon: ReactElement; tone?: "gold" | "green" | "blue" | "red" }> = ({ tone = "gold", ...props }) => <Metric {...props} tone={tone === "green" ? "var(--panel-success)" : tone === "red" ? "var(--panel-danger)" : tone === "blue" ? "var(--panel-info)" : "var(--panel-accent)"} />;
const SectionTitle = SectionHeader;

const AttentionList: FC<{ items: DashboardAttentionUser[]; onOpen: (username: string) => void }> = ({ items, onOpen }) => (
  <Stack spacing={0}>
    {items.length === 0 ? <EmptyState text="کاربری نیازمند توجه فوری نیست." /> : items.map((item) => (
      <HStack
        key={item.username}
        py={2.5}
        borderBottomWidth="1px"
        borderColor="var(--panel-border)"
        _last={{ borderBottomWidth: 0 }}
        cursor="pointer"
        role="button"
        tabIndex={0}
        onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpen(item.username); } }}
        onClick={() => onOpen(item.username)}
        justify="space-between"
        gap={3}
      >
        <HStack minW={0}>
          <Box boxSize="8px" borderRadius="full" bg={item.priority === "critical" ? "var(--panel-danger)" : item.priority === "high" ? "var(--panel-warning)" : "var(--panel-accent)"} />
          <Box minW={0}>
            <Text dir="ltr" textAlign="start" fontSize="sm" fontWeight="700" noOfLines={1}>{item.username}</Text>
            <Text fontSize="xs" color="var(--panel-text-muted)">{statusLabel(item.status)}</Text>
          </Box>
        </HStack>
        <Text fontSize="xs" fontWeight="700" color={item.priority === "critical" ? "var(--panel-danger)" : item.priority === "high" ? "var(--panel-warning)" : "var(--panel-text-body)"}>
          {reasonLabel(item)}
        </Text>
      </HStack>
    ))}
  </Stack>
);

const TopConsumers: FC<{ items: DashboardUserSummary[]; onOpen: (username: string) => void }> = ({ items, onOpen }) => {
  const max = Math.max(...items.map((item) => item.used_traffic), 1);
  return (
    <Stack spacing={2}>
      {items.length === 0 ? <EmptyState text="هنوز مصرف ثبت‌شده‌ای وجود ندارد." /> : items.map((item, index) => (
        <HStack key={item.username} py={1.5} gap={3} cursor="pointer" role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpen(item.username); } }} onClick={() => onOpen(item.username)}>
          <Text w="18px" fontSize="xs" color="var(--panel-text-muted)">{fa(index + 1)}</Text>
          <Box flex="1" minW={0}>
            <HStack justify="space-between" mb={1.5}>
              <Text dir="ltr" fontSize="sm" fontWeight="700" noOfLines={1}>{item.username}</Text>
              <Text dir="ltr" fontSize="xs" color="var(--panel-text-body)">{formatTraffic(item.used_traffic)}</Text>
            </HStack>
            <Progress value={(item.used_traffic / max) * 100} size="xs" borderRadius="full" colorScheme="blue" bg="var(--panel-nested)" />
          </Box>
        </HStack>
      ))}
    </Stack>
  );
};

export const DashboardOverview: FC = () => {
  const { userData, getUserIsSuccess } = useGetUser();
  const navigate = useNavigate();
  const chartPalette = useChartPalette();
  const timezoneOffset = -new Date().getTimezoneOffset();
  const [range, setRange] = useState<DashboardRange>("24h");
  const [planCreateOpen, setPlanCreateOpen] = useState(false);
  const isOwner = userData.role === "OWNER" || userData.is_sudo;

  const overview = useQuery<DashboardOverviewData, Error>(
    ["dashboard-overview-v2", userData.username, timezoneOffset, range],
    () => fetch(`/dashboard/overview?timezone_offset_minutes=${timezoneOffset}&traffic_range=${range}`),
    { enabled: getUserIsSuccess, refetchInterval: 30000, keepPreviousData: true, staleTime: 10000 },
  );
  const account = useQuery<AccountSummary, Error>(
    ["account-summary", userData.username],
    () => fetch("/account/summary"),
    { enabled: getUserIsSuccess && !isOwner, refetchInterval: 30000, staleTime: 15000 },
  );
  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities"),
    { enabled: getUserIsSuccess && !isOwner, refetchInterval: 30000, staleTime: 15000 },
  );

  const openUsers = () => navigate("/users/");
  const openUser = (username: string) => {
    const current = useDashboard.getState().filters;
    useDashboard.setState({ filters: { ...current, search: username, offset: 0 } });
    navigate("/users/");
  };
  const createUser = () => {
    useDashboard.getState().onCreateUser(true);
    navigate("/users/");
  };

  const data = overview.data;
  const trafficSeries = useMemo(() => [{
    name: "مصرف",
    data: (data?.traffic_history || []).map((point) => ({ x: parseUtcDate(point.timestamp).getTime(), y: point.total_traffic })),
  }], [data?.traffic_history]);
  const trafficOptions = useMemo<ApexOptions>(() => ({
    chart: { toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: false }, background: "transparent", fontFamily: "Vazirmatn" },
    colors: [chartPalette.accent],
    dataLabels: { enabled: false },
    stroke: { curve: "smooth", width: 2.4 },
    fill: { type: "gradient", gradient: { shadeIntensity: 0.25, opacityFrom: 0.24, opacityTo: 0.02, stops: [0, 90, 100] } },
    grid: { borderColor: chartPalette.grid, strokeDashArray: 3 },
    xaxis: { type: "datetime", labels: { style: { colors: chartPalette.text, fontSize: "10px" }, datetimeUTC: false }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { labels: { style: { colors: chartPalette.text, fontSize: "10px" }, formatter: (value) => formatTraffic(value) } },
    tooltip: { theme: chartPalette.mode, x: { format: range === "24h" ? "HH:mm" : "yyyy/MM/dd" }, y: { formatter: (value) => formatTraffic(value) } },
    legend: { show: false },
  }), [range, chartPalette.accent, chartPalette.text, chartPalette.mode]);

  if (!getUserIsSuccess || overview.isLoading) {
    return <Stack spacing={4}><Skeleton height="110px" borderRadius="16px" /><Skeleton height="150px" borderRadius="16px" /><Skeleton height="430px" borderRadius="16px" /></Stack>;
  }
  if (overview.isError || !data) {
    return (
      <Alert status="error" borderRadius="14px" minH="88px">
        <AlertIcon />
        <Text>اطلاعات داشبورد بارگذاری نشد.</Text>
        <Button ms="auto" size="sm" variant="outline" onClick={() => overview.refetch()}>تلاش دوباره</Button>
      </Alert>
    );
  }

  const statusItems = [
    { label: "فعال", value: data.active_users, color: chartPalette.success },
    { label: "منقضی", value: data.expired_users, color: chartPalette.danger },
    { label: "غیرفعال", value: data.disabled_users, color: chartPalette.text },
    { label: "در انتظار", value: data.on_hold_users, color: chartPalette.warning },
    { label: "محدود", value: data.limited_users, color: chartPalette.info },
  ];
  const statusOptions: ApexOptions = {
    chart: { animations: { enabled: false }, background: "transparent", fontFamily: "Vazirmatn" },
    colors: statusItems.map((item) => item.color),
    labels: statusItems.map((item) => item.label),
    legend: { show: false },
    dataLabels: { enabled: false },
    stroke: { width: 2, colors: [chartPalette.surface] },
    plotOptions: { pie: { donut: { size: "72%", labels: { show: true, name: { show: true, color: chartPalette.text }, value: { show: true, color: chartPalette.text, formatter: (value) => fa(Number(value)) }, total: { show: true, label: "کاربر", color: chartPalette.text, formatter: () => fa(data.total_users) } } } } },
    tooltip: { theme: chartPalette.mode },
  };

  const accountData = account.data;
  const quota = capabilities.data?.quota;
  const trialRemaining = accountData ? Math.max(Number(accountData.trial_quota || 0) - Number(accountData.trials_used || 0), 0) : 0;
  const accountActive = accountData?.account_status === "ACTIVE";
  const canFreeForm = Boolean(accountActive && accountData?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(accountData?.user_creation_mode || ""));
  const canPlan = Boolean(accountActive && (accountData?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(accountData?.user_creation_mode || "")));

  return (
    <Stack spacing={4} dir="rtl" aria-live="polite">
      <PageHeader eyebrow={isOwner ? "مرکز مدیریت" : "فضای کاری شما"} title={isOwner ? "داشبورد مدیریتی" : "داشبورد کاربران"} description={isOwner ? "وضعیت کاربران، سلامت سرویس و فعالیت‌های مهم در یک نگاه." : "خلاصهٔ کاربران، اعتبار و فعالیت‌های روزانهٔ شما."} actions={
        <HStack flexWrap="wrap">
          {isOwner ? (
            <>
              <Button size="sm" h="40px" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={createUser}>افزودن کاربر</Button>
              <Button size="sm" h="40px" variant="outline" borderColor="var(--panel-border)" onClick={openUsers}>مشاهده کاربران</Button>
            </>
          ) : (
            <>
              {canFreeForm && <Button size="sm" h="40px" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={createUser}>افزودن کاربر</Button>}
              {canPlan && <Button size="sm" h="40px" variant="outline" borderColor="var(--panel-accent-border)" color="var(--panel-accent)" onClick={() => setPlanCreateOpen(true)}>ساخت از پلن</Button>}
            </>
          )}
        </HStack>
      } />

      {!isOwner && accountData && accountData.account_status !== "ACTIVE" && (
        <Alert status="warning" borderRadius="12px"><AlertIcon />حساب شما در وضعیت {accountData.account_status === "SUSPENDED" ? "فریز" : "غیرفعال"} است؛ عملیات ساخت کاربر در دسترس نیست.</Alert>
      )}

      <SimpleGrid columns={{ base: 1, sm: 2, xl: 5 }} gap={3}>
        <MetricCard label={isOwner ? "کل کاربران" : "کاربران من"} value={fa(data.total_users)} hint={isOwner ? "کل کاربران قابل مشاهده" : "در محدوده مجاز حساب شما"} icon={<UsersMetricIcon />} />
        <MetricCard label="آنلاین الآن" value={fa(data.online_users)} hint={`فعالیت ثبت‌شده در ${fa(data.online_window_seconds)} ثانیه اخیر`} icon={<OnlineMetricIcon />} tone="blue" />
        <MetricCard label="فعال" value={fa(data.active_users)} hint="کاربران با وضعیت فعال" icon={<ActiveMetricIcon />} tone="green" />
        <MetricCard label="نیازمند توجه" value={fa(data.attention_count)} hint="براساس وضعیت، حجم، انقضا و Device Limit" icon={<AttentionMetricIcon />} tone={data.attention_count ? "red" : "green"} />
        {isOwner ? (
          <MetricCard label="مصرف امروز" value={formatTraffic(data.today_traffic)} hint="مصرف ثبت‌شده کاربران از ابتدای روز" icon={<TrafficMetricIcon />} tone="blue" />
        ) : (
          <MetricCard label="اعتبار" value={accountData ? toman(accountData.money_balance_toman) : "—"} hint="مانده مالی قابل استفاده حساب" icon={<CreditMetricIcon />} tone="gold" />
        )}
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, xl: 12 }} gap={4} alignItems="stretch">
        <Box gridColumn={{ xl: "span 6" }}>
          <Panel minH="390px">
            <SectionTitle
              title={isOwner ? "مصرف کل کاربران" : "مصرف کاربران من"}
              description="روند مصرف ترافیک در بازهٔ انتخاب‌شده"
              action={
                <HStack spacing={1} flexWrap="wrap">
                  {(["24h", "7d", "30d"] as DashboardRange[]).map((item) => (
                    <Button key={item} size="xs" h="32px" px={3} variant={range === item ? "solid" : "ghost"} colorScheme={range === item ? "primary" : undefined} color={range === item ? "var(--panel-accent-contrast)" : "var(--panel-text-muted)"} onClick={() => setRange(item)}>
                      {item === "24h" ? "۲۴ ساعت" : item === "7d" ? "۷ روز" : "۳۰ روز"}
                    </Button>
                  ))}
                </HStack>
              }
            />
            {overview.isFetching && <Progress size="xs" isIndeterminate mb={2} colorScheme="yellow" />}
            {!data.traffic_history_available || data.traffic_history.length === 0 ? (
              <EmptyState text="در این بازه هنوز داده تاریخی ترافیک ثبت نشده است." />
            ) : (
              <Chart type="area" height={300} options={trafficOptions} series={trafficSeries} />
            )}
          </Panel>
        </Box>

        <Box gridColumn={{ xl: "span 3" }}>
          <Panel minH="390px">
            <SectionTitle title={isOwner ? "وضعیت کاربران" : "وضعیت کاربران من"} description="توزیع وضعیت‌های واقعی کاربران" />
            <Box maxW="230px" mx="auto"><Chart type="donut" height={220} options={statusOptions} series={statusItems.map((item) => item.value)} /></Box>
            <Stack spacing={1.5} mt={1}>
              {statusItems.map((item) => <HStack key={item.label} justify="space-between"><HStack><Box boxSize="7px" bg={item.color} borderRadius="full" /><Text fontSize="xs" color="var(--panel-text-muted)">{item.label}</Text></HStack><Text fontSize="xs" fontWeight="700">{fa(item.value)}</Text></HStack>)}
            </Stack>
          </Panel>
        </Box>

        <Box gridColumn={{ xl: "span 3" }}>
          <Panel minH="390px">
            <SectionTitle title={isOwner ? "نیازمند توجه" : "نیازمند تمدید / توجه"} description="مهم‌ترین موارد در محدوده مجاز" action={<Button size="xs" variant="ghost" color="var(--panel-accent)" onClick={openUsers}>مشاهده همه</Button>} />
            <AttentionList items={data.attention_users} onOpen={openUser} />
          </Panel>
        </Box>
      </SimpleGrid>

      {isOwner ? (
        <SimpleGrid columns={{ base: 1, lg: 3 }} gap={4}>
          <Panel>
            <SectionTitle title="بیشترین مصرف" description="۵ کاربر با بیشترین مصرف ثبت‌شده" />
            <TopConsumers items={data.top_consumers} onOpen={openUser} />
          </Panel>
          <Panel>
            <SectionTitle title="وضعیت نودها" description="خلاصه اتصال نودهای سیستم" action={<Button size="xs" variant="ghost" color="var(--panel-accent)" onClick={() => useDashboard.getState().onEditingNodes(true)}>مشاهده جزئیات نودها</Button>} />
            {data.node_summary && data.node_summary.total > 0 ? (
              <SimpleGrid columns={2} gap={2}>
                <Box p={3} bg="var(--panel-success-soft)" borderWidth="1px" borderColor="var(--panel-success-border)" borderRadius="12px"><Text fontSize="xl" fontWeight="700">{fa(data.node_summary.healthy)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">سالم</Text></Box>
                <Box p={3} bg="var(--panel-accent-soft)" borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius="12px"><Text fontSize="xl" fontWeight="700">{fa(data.node_summary.reconnecting)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">در حال اتصال</Text></Box>
                <Box p={3} bg="var(--panel-danger-soft)" borderWidth="1px" borderColor="var(--panel-danger-border)" borderRadius="12px"><Text fontSize="xl" fontWeight="700">{fa(data.node_summary.error)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">خطا</Text></Box>
                <Box p={3} bg="var(--panel-nested)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px"><Text fontSize="xl" fontWeight="700">{fa(data.node_summary.disabled)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">غیرفعال</Text></Box>
              </SimpleGrid>
            ) : <EmptyState text="نودی ثبت نشده است." />}
          </Panel>
          <Panel>
            <SectionTitle title="ادمین‌ها" description="خلاصه مدیریت ادمین‌های سیستم" action={<Button size="xs" variant="ghost" color="var(--panel-accent)" onClick={() => navigate("/admins/")}>مدیریت ادمین‌ها</Button>} />
            {data.admin_summary ? (
              <Stack spacing={3}>
                <HStack justify="space-between" p={3} bg="var(--panel-nested)" borderRadius="12px"><Text fontSize="sm" color="var(--panel-text-muted)">کل ادمین‌ها</Text><Text fontSize="xl" fontWeight="700">{fa(data.admin_summary.total)}</Text></HStack>
                <SimpleGrid columns={3} gap={2}>
                  <Box textAlign="center" p={2.5} borderWidth="1px" borderColor="var(--panel-success-border)" borderRadius="10px"><Text fontWeight="700" color="var(--panel-success)">{fa(data.admin_summary.active)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">فعال</Text></Box>
                  <Box textAlign="center" p={2.5} borderWidth="1px" borderColor="var(--panel-warning-border)" borderRadius="10px"><Text fontWeight="700" color="var(--panel-warning)">{fa(data.admin_summary.suspended)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">فریز</Text></Box>
                  <Box textAlign="center" p={2.5} borderWidth="1px" borderColor="var(--panel-danger-border)" borderRadius="10px"><Text fontWeight="700" color="var(--panel-danger)">{fa(data.admin_summary.disabled)}</Text><Text fontSize="xs" color="var(--panel-text-muted)">غیرفعال</Text></Box>
                </SimpleGrid>
              </Stack>
            ) : <EmptyState text="اطلاعات ادمین‌ها در دسترس نیست." />}
          </Panel>
        </SimpleGrid>
      ) : (
        <SimpleGrid columns={{ base: 1, lg: 3 }} gap={4}>
          <Panel>
            <SectionTitle title="اعتبار و ظرفیت" description="وضعیت مالی و سهمیه حساب شما" />
            {account.isError || capabilities.isError ? (
              <Alert status="error" borderRadius="10px"><AlertIcon />اطلاعات حساب بارگذاری نشد.</Alert>
            ) : account.isLoading || capabilities.isLoading || !accountData ? (
              <Skeleton height="180px" borderRadius="12px" />
            ) : (
              <Stack spacing={2.5}>
                {accountData.billing_mode === "USED_TRAFFIC" && <Box p={3} bg="var(--panel-nested)" borderRadius="12px"><Text fontSize="sm" fontWeight="700">نرخ پایه هر گیگ: {accountData.used_traffic_price_per_gib_toman == null ? "تنظیم نشده" : toman(accountData.used_traffic_price_per_gib_toman)}</Text><Text fontSize="xs" color="var(--panel-text-muted)" mt={1}>هر گیگ برابر ۱۰۲۴ مگابایت است. هزینه مصرف هر اکانت با ضریب مدت همان اکانت محاسبه می‌شود.</Text></Box>}
                <HStack justify="space-between"><Text fontSize="xs" color="var(--panel-text-muted)">مانده اعتبار</Text><Text fontSize="sm" fontWeight="700">{toman(accountData.money_balance_toman)}</Text></HStack>
                <HStack justify="space-between"><Text fontSize="xs" color="var(--panel-text-muted)">سقف اعتبار</Text><Text fontSize="sm" fontWeight="700">{credit(quota?.credit_limit)}</Text></HStack>
                <HStack justify="space-between"><Text fontSize="xs" color="var(--panel-text-muted)">اعتبار مصرف‌شده</Text><Text fontSize="sm" fontWeight="700">{quota ? credit(quota.credit_used) : "—"}</Text></HStack>
                <HStack justify="space-between"><Text fontSize="xs" color="var(--panel-text-muted)">مانده اعتبار</Text><Text fontSize="sm" fontWeight="700">{credit(quota?.credit_remaining)}</Text></HStack>
                <HStack justify="space-between"><Text fontSize="xs" color="var(--panel-text-muted)">سهمیه تست باقی‌مانده</Text><Text fontSize="sm" fontWeight="700">{fa(trialRemaining)}</Text></HStack>
                {quota?.credit_usage_percent != null && <Progress value={Math.min(100, quota.credit_usage_percent)} size="sm" borderRadius="full" colorScheme={quota.credit_usage_percent >= 85 ? "red" : "yellow"} />}
              </Stack>
            )}
          </Panel>
          <Panel>
            <SectionTitle title="بیشترین مصرف" description="۵ کاربر شما با بیشترین مصرف" />
            <TopConsumers items={data.top_consumers} onOpen={openUser} />
          </Panel>
          <Panel>
            <SectionTitle title="کاربران اخیر" description="آخرین کاربران ساخته‌شده در محدوده شما" action={<Button size="xs" variant="ghost" color="var(--panel-accent)" onClick={openUsers}>مشاهده همه کاربران</Button>} />
            <Stack spacing={0}>
              {data.recent_users.length === 0 ? <EmptyState text="هنوز کاربری ساخته نشده است." /> : data.recent_users.map((item) => (
                <HStack key={item.username} py={2.5} justify="space-between" borderBottomWidth="1px" borderColor="var(--panel-border)" _last={{ borderBottomWidth: 0 }} cursor="pointer" role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openUser(item.username); } }} onClick={() => openUser(item.username)}>
                  <Box minW={0} flex="1"><Text dir="ltr" fontSize="sm" fontWeight="700" noOfLines={1} title={item.username}>{item.username}</Text><Text fontSize="xs" color="var(--panel-text-muted)">{relativeTime(item.created_at)}</Text></Box>
                  <Badge flexShrink={0} colorScheme={item.status === "active" ? "green" : item.status === "expired" || item.status === "limited" ? "red" : "gray"}>{statusLabel(item.status)}</Badge>
                </HStack>
              ))}
            </Stack>
          </Panel>
        </SimpleGrid>
      )}

      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default DashboardOverview;
