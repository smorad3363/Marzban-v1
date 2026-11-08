import { Alert, AlertIcon, Box, Button, HStack, Icon, Popover, PopoverBody, PopoverCloseButton, PopoverContent, PopoverHeader, PopoverTrigger, SimpleGrid, Skeleton, Stack, Text, Tooltip } from "@chakra-ui/react";
import { ServerStackIcon } from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { useState } from "react";
import { useQuery } from "react-query";
import { useNavigate } from "react-router-dom";
import { fetch } from "service/http";
import { AccountSummary } from "types/Admin";
import { DashboardOverview } from "types/Dashboard";
import { formatBytes } from "utils/formatByte";

const fa = (value?: number) => value == null ? "—" : value.toLocaleString("fa-IR");
function useOverview(enabled = true) {
  const { userData, getUserIsSuccess } = useGetUser();
  const offset = -new Date().getTimezoneOffset();
  return useQuery<DashboardOverview, Error>(["dashboard-overview-v2", userData.username, offset, "24h"], () => fetch(`/dashboard/overview?timezone_offset_minutes=${offset}&traffic_range=24h`), { enabled: enabled && getUserIsSuccess, staleTime: 15000, refetchInterval: enabled ? 60000 : false, refetchIntervalInBackground: false });
}

export function WorkspaceSummary() {
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = userData.is_sudo || userData.role === "OWNER";
  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"), { enabled: getUserIsSuccess && !isOwner, staleTime: 15000, refetchInterval: 60000, refetchIntervalInBackground: false });
  const query = useOverview();
  const { filters, onFilterChange } = useDashboard();
  const data = query.data;
  const items = [
    { label: "کل کاربران", value: fa(data?.total_users), active: !filters.status && !filters.attention, onClick: () => onFilterChange({ status: undefined, attention: undefined, offset: 0 }) },
    { label: "آنلاین الآن", value: fa(data?.online_users), hint: `فعالیت در ${fa(data?.online_window_seconds)} ثانیهٔ اخیر` },
    { label: "فعال", value: fa(data?.active_users), active: filters.status === "active", onClick: () => onFilterChange({ status: "active", attention: undefined, offset: 0 }) },
    { label: "نیازمند توجه", value: fa(data?.attention_count), active: filters.attention, onClick: () => onFilterChange({ attention: filters.attention ? undefined : true, status: undefined, offset: 0 }) },
    { label: isOwner ? "مصرف امروز" : "مانده اعتبار", value: isOwner ? data ? String(formatBytes(data.today_traffic)) : "—" : account.data ? `${fa(account.data.money_balance_toman)} تومان` : "—" },
  ];
  return <Box as="section" aria-label="خلاصه کاربران" className="workspace-summary">
    <SimpleGrid columns={{ base: 2, sm: 3, lg: 5 }} gap={0}>
      {items.map(item => <Tooltip key={item.label} label={item.hint} isDisabled={!item.hint} hasArrow><Box as={item.onClick ? "button" : "div"} onClick={item.onClick} aria-pressed={item.onClick ? Boolean(item.active) : undefined} className="workspace-stat" textAlign="start" bg={item.active ? "var(--panel-accent-soft)" : undefined}>
        <Text fontSize="xs" color="var(--panel-text-muted)">{item.label}</Text>
        <Skeleton isLoaded={!query.isLoading} mt={1} minH="28px"><Text dir="auto" fontSize="xl" fontWeight="700" sx={{ fontVariantNumeric: "tabular-nums" }}>{item.value}</Text></Skeleton>
      </Box></Tooltip>)}
    </SimpleGrid>
    {!isOwner && account.data && account.data.account_status !== "ACTIVE" && <Alert status="warning" fontSize="sm"><AlertIcon />حساب شما {account.data.account_status === "SUSPENDED" ? "فریز" : "غیرفعال"} است؛ عملیات حساب محدود شده است.</Alert>}
    {(query.isError || (!isOwner && account.isError)) && <HStack p={2} justify="space-between"><Text fontSize="xs" color="var(--panel-danger)">آمار تازه نشد؛ مقادیر قبلی ممکن است قدیمی باشند.</Text><Button size="xs" onClick={() => { query.refetch(); if (!isOwner) account.refetch(); }}>تلاش مجدد</Button></HStack>}
  </Box>;
}

export function WorkspaceStatus() {
  const [open, setOpen] = useState(false);
  const query = useOverview(open);
  const navigate = useNavigate();
  const nodes = query.data?.node_summary;
  const admins = query.data?.admin_summary;
  return <Popover isOpen={open} onOpen={() => setOpen(true)} onClose={() => setOpen(false)} placement="bottom-end" isLazy>
    <PopoverTrigger><Button size="sm" variant="ghost" h="44px" px={2} leftIcon={<Icon as={ServerStackIcon} boxSize={4} aria-hidden="true" />} aria-label="خلاصه وضعیت سرویس"><Text display={{ base: "none", sm: "block" }}>وضعیت سرویس</Text></Button></PopoverTrigger>
    <PopoverContent maxW="calc(100vw - 24px)" w="320px" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)"><PopoverCloseButton aria-label="بستن وضعیت سرویس" /><PopoverHeader fontWeight="700">وضعیت سرویس</PopoverHeader><PopoverBody>
      {query.isLoading && <Text role="status">در حال دریافت…</Text>}
      {query.isError && <Alert status="error"><AlertIcon /><Button size="sm" onClick={() => query.refetch()}>دریافت دوباره</Button></Alert>}
      {query.data && <Stack spacing={3} fontSize="sm">
        <HStack justify="space-between"><Text>کاربران آنلاین</Text><Text fontWeight="700">{fa(query.data.online_users)}</Text></HStack>
        {nodes && <><Text fontWeight="600">نودها</Text><SimpleGrid columns={2} gap={2}><Text>سالم: {fa(nodes.healthy)}</Text><Text>در اتصال: {fa(nodes.reconnecting)}</Text><Text color={nodes.error ? "var(--panel-danger)" : undefined}>خطا: {fa(nodes.error)}</Text><Text>غیرفعال: {fa(nodes.disabled)}</Text></SimpleGrid></>}
        {admins && <HStack justify="space-between"><Text>ادمین‌ها</Text><Text>{fa(admins.active)} فعال · {fa(admins.suspended)} فریز</Text></HStack>}
        <Button size="sm" variant="outline" onClick={() => { setOpen(false); navigate("/users/"); }}>بازکردن کاربران</Button>
      </Stack>}
    </PopoverBody></PopoverContent>
  </Popover>;
}
