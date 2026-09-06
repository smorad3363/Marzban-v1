import {
  Alert, AlertDialog, AlertDialogBody, AlertDialogContent, AlertDialogFooter,
  AlertDialogHeader, AlertDialogOverlay, AlertIcon, Badge, Box, Button, Card,
  Checkbox, Collapse, Divider, FormControl, FormHelperText, FormLabel, HStack,
  IconButton, Input, InputGroup, InputLeftElement, Menu, MenuButton, MenuItem,
  MenuList, Select, SimpleGrid, Skeleton, Stack, Table, TableContainer, Tbody,
  Td, Text, Textarea, Th, Thead, Tr, VStack, chakra, useDisclosure, useToast,
} from "@chakra-ui/react";
import {
  ChevronDownIcon, EllipsisVerticalIcon, MagnifyingGlassIcon, PlusIcon, UserGroupIcon,
} from "@heroicons/react/24/outline";
import { AdminFormDrawer } from "components/AdminFormDrawer";
import { AppShell } from "components/AppShell";
import useGetUser from "hooks/useGetUser";
import { FC, Fragment, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { Navigate, useSearchParams } from "react-router-dom";
import { fetch } from "service/http";
import { AdminCapabilities, ManagedAdmin, ManagedAdminList } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { formatBytes } from "utils/formatByte";

const SearchIcon = chakra(MagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });
const MoreIcon = chakra(EllipsisVerticalIcon, { baseStyle: { w: 5, h: 5 } });
const AdminsIcon = chakra(UserGroupIcon, { baseStyle: { w: 5, h: 5 } });
const ChevronIcon = chakra(ChevronDownIcon, { baseStyle: { w: 4, h: 4 } });

const PAGE_SIZE = 20;

const billingModeLabels: Record<string, string> = {
  LEGACY_COMPAT: "قدیمی",
  SEAT_CREDIT: "ظرفیت دستگاه",
  USED_TRAFFIC: "مصرف واقعی",
  ALLOCATED_TRAFFIC: "حجم ساخته‌شده",
  USER_CREDIT: "سقف اکانت",
};

const statusMeta = {
  ACTIVE: { label: "فعال", dot: "#4ade80", text: "green.300", bg: "rgba(34,197,94,.08)" },
  SUSPENDED: { label: "فریز", dot: "#f59e0b", text: "orange.300", bg: "rgba(245,158,11,.08)" },
  DISABLED: { label: "غیرفعال", dot: "#94a3b8", text: "gray.300", bg: "rgba(148,163,184,.08)" },
} as const;

const panel = {
  bg: "rgba(10, 17, 29, .76)",
  borderColor: "rgba(148, 163, 184, .14)",
  boxShadow: "0 16px 44px rgba(0,0,0,.18)",
};

const control = {
  bg: "rgba(2, 8, 23, .38)",
  borderColor: "rgba(148,163,184,.18)",
  _hover: { borderColor: "rgba(148,163,184,.30)" },
  _focusVisible: {
    borderColor: "primary.400",
    boxShadow: "0 0 0 2px rgba(74,222,128,.12)",
  },
};

const SummaryStat: FC<{ label: string; value: string; hint: string; tone?: string }> = ({
  label, value, hint, tone = "gray.100",
}) => (
  <Card
    p={{ base: 3, md: 4 }}
    minH="104px"
    bg={panel.bg}
    borderWidth="1px"
    borderColor={panel.borderColor}
    borderRadius="14px"
    boxShadow="none"
  >
    <Text color="gray.500" fontSize="xs" fontWeight="700">{label}</Text>
    <Text mt={2} color={tone} fontSize={{ base: "xl", md: "2xl" }} fontWeight="800" sx={{ fontVariantNumeric: "tabular-nums" }}>
      {value}
    </Text>
    <Text mt={1.5} color="gray.600" fontSize="11px">{hint}</Text>
  </Card>
);

const CapacityRing: FC<{ current: number; maximum: number | null | undefined }> = ({ current, maximum }) => {
  if (maximum == null) {
    return (
      <HStack spacing={2}>
        <Box
          w="38px"
          h="38px"
          borderRadius="full"
          borderWidth="1px"
          borderColor="rgba(148,163,184,.18)"
          display="grid"
          placeItems="center"
          color="gray.400"
          fontWeight="800"
          transition="transform .18s ease, border-color .18s ease"
          _groupHover={{ transform: "scale(1.04)", borderColor: "rgba(74,222,128,.35)" }}
        >
          ∞
        </Box>
        <Box>
          <Text fontWeight="800" lineHeight="1">{current.toLocaleString("fa-IR")}</Text>
          <Text mt={1} color="gray.500" fontSize="10px">بدون سقف</Text>
        </Box>
      </HStack>
    );
  }

  const safeMax = Math.max(maximum, 1);
  const percent = Math.min(100, Math.max(0, (current / safeMax) * 100));
  const radius = 15;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (circumference * percent) / 100;

  return (
    <HStack spacing={2}>
      <Box
        w="40px"
        h="40px"
        transition="transform .18s ease"
        _groupHover={{ transform: "scale(1.04)" }}
      >
        <svg viewBox="0 0 40 40" width="40" height="40" aria-label={`${Math.round(percent)} درصد ظرفیت کاربر`}>
          <circle cx="20" cy="20" r={radius} fill="none" stroke="rgba(148,163,184,.14)" strokeWidth="4" />
          <circle
            cx="20"
            cy="20"
            r={radius}
            fill="none"
            stroke={percent >= 90 ? "#f87171" : percent >= 70 ? "#f59e0b" : "#4ade80"}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 20 20)"
            style={{ transition: "stroke-dashoffset 420ms cubic-bezier(.22,1,.36,1), stroke 180ms ease" }}
          />
        </svg>
      </Box>
      <Box>
        <Text fontWeight="800" lineHeight="1">
          {current.toLocaleString("fa-IR")} / {maximum.toLocaleString("fa-IR")}
        </Text>
        <Text mt={1} color="gray.500" fontSize="10px">{Math.round(percent).toLocaleString("fa-IR")}٪ ظرفیت</Text>
      </Box>
    </HStack>
  );
};

const AdminAvatar: FC<{ username: string; owner: boolean }> = ({ username, owner }) => (
  <Box
    flexShrink={0}
    w="38px"
    h="38px"
    display="grid"
    placeItems="center"
    borderRadius="12px"
    bg={owner ? "rgba(139,92,246,.12)" : "rgba(59,130,246,.10)"}
    borderWidth="1px"
    borderColor={owner ? "rgba(167,139,250,.25)" : "rgba(96,165,250,.20)"}
    color={owner ? "purple.200" : "blue.200"}
    fontWeight="800"
    textTransform="uppercase"
    transition="transform .18s ease, border-color .18s ease, background .18s ease"
    _groupHover={{
      transform: "translateY(-1px)",
      borderColor: owner ? "rgba(167,139,250,.42)" : "rgba(96,165,250,.38)",
    }}
  >
    {username.slice(0, 1)}
  </Box>
);

const StatusPill: FC<{ status: keyof typeof statusMeta }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack
      w="fit-content"
      spacing={1.5}
      px={2}
      py={1}
      bg={meta.bg}
      borderRadius="full"
      transition="background .18s ease"
    >
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.text} fontSize="11px" fontWeight="700">{meta.label}</Text>
    </HStack>
  );
};

export const Admins: FC = () => {
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { userData, getUserIsPending, getUserIsSuccess } = useGetUser();

  const formDisclosure = useDisclosure();
  const openAdminForm = formDisclosure.onOpen;
  const deleteDisclosure = useDisclosure();
  const freezeDisclosure = useDisclosure();
  const creditDisclosure = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const [selected, setSelected] = useState<ManagedAdmin | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [billingFilter, setBillingFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedUsername, setExpandedUsername] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [freezeTarget, setFreezeTarget] = useState<ManagedAdmin | null>(null);
  const [freezeReason, setFreezeReason] = useState("");
  const [creditTarget, setCreditTarget] = useState<ManagedAdmin | null>(null);
  const [creditOperation, setCreditOperation] = useState<"grant" | "reclaim">("grant");
  const [creditAmount, setCreditAmount] = useState("");
  const [creditReason, setCreditReason] = useState("");
  const [deleteStrategy, setDeleteStrategy] = useState<"delete_users" | "disable_users" | "keep_users">("keep_users");

  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities"),
    { enabled: getUserIsSuccess }
  );

  const canManage = Boolean(capabilities.data?.can_manage_admins);
  const isOwner = Boolean(userData.is_sudo || userData.role === "OWNER");
  const hierarchyReady = capabilities.data?.hierarchy_enabled !== false;
  const canCreate = Boolean(capabilities.data?.can_create_admins) && hierarchyReady;

  useEffect(() => {
    if (canCreate && searchParams.get("create") === "1") {
      setSelected(null);
      openAdminForm();
      setSearchParams({}, { replace: true });
    }
  }, [canCreate, openAdminForm, searchParams, setSearchParams]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(0);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const query = useQuery<ManagedAdminList, Error>(
    ["admin-management", page, search, billingFilter, statusFilter],
    () => {
      const params = new URLSearchParams({
        offset: String(page * PAGE_SIZE),
        limit: String(PAGE_SIZE),
        username: search,
      });
      if (billingFilter) params.set("billing_mode", billingFilter);
      if (statusFilter) params.set("account_status", statusFilter);
      return fetch(`/admin-management?${params.toString()}`);
    },
    { keepPreviousData: true, enabled: canManage, refetchInterval: 15000 }
  );

  const refreshAdminData = () => {
    queryClient.invalidateQueries("admin-management");
    queryClient.invalidateQueries("admin-hierarchy-tree");
    queryClient.invalidateQueries("account-summary");
  };

  const removeMutation = useMutation(
    ({ username, strategy }: { username: string; strategy: typeof deleteStrategy }) =>
      fetch(`/admin/${username}`, { method: "DELETE", body: { strategy } }),
    {
      onSuccess: () => {
        refreshAdminData();
        toast({ title: t("admins.deleted"), status: "success", duration: 3000 });
        deleteDisclosure.onClose();
      },
      onError: (error) => {
        toast({ title: t("admins.deleteFailed"), description: localizedApiError(error), status: "error", duration: 5000 });
      },
    }
  );

  const quickAction = useMutation(
    ({ item, operation, reason }: {
      item: ManagedAdmin;
      operation: "activate" | "freeze" | "unfreeze" | "resume" | "trial-reset";
      reason?: string;
    }) => {
      if (operation === "trial-reset") {
        return fetch(`/admin-management/${item.username}/trial-quota/reset`, {
          method: "POST",
          body: {
            idempotency_key: `trial-reset-${item.id}-${crypto.randomUUID()}`,
            note: "بازنشانی سهمیه تست توسط ادمین بالاسری",
          },
        });
      }
      if (operation === "resume") {
        return fetch(`/admin-management/${item.username}/resume`, { method: "POST" });
      }
      if (operation === "activate") {
        return fetch(`/admin-management/${encodeURIComponent(item.username)}/activate`, { method: "POST" });
      }
      return fetch(`/admin-management/${item.username}/${operation}`, {
        method: "POST",
        body: operation === "freeze"
          ? { reason_id: 1, idempotency_key: `freeze-${item.id}-${crypto.randomUUID()}`, note: reason }
          : { idempotency_key: `unfreeze-${item.id}-${crypto.randomUUID()}` },
      });
    },
    {
      onSuccess: () => {
        refreshAdminData();
        freezeDisclosure.onClose();
        setFreezeReason("");
        setFreezeTarget(null);
        toast({ title: "عملیات انجام شد", status: "success", duration: 2500 });
      },
      onError: (error) => {
        toast({ title: "عملیات انجام نشد", description: localizedApiError(error), status: "error", duration: 5000 });
      },
    }
  );

  const creditMutation = useMutation(
    ({ item, operation, amount, reason }: {
      item: ManagedAdmin;
      operation: "grant" | "reclaim";
      amount: number;
      reason?: string;
    }) =>
      fetch(`/admin-management/${encodeURIComponent(item.username)}/money/${operation}`, {
        method: "POST",
        body: {
          amount_toman: Math.round(amount),
          idempotency_key: `admin-money-${crypto.randomUUID()}`,
          note: reason || undefined,
        },
      }),
    {
      onSuccess: () => {
        refreshAdminData();
        creditDisclosure.onClose();
        setCreditTarget(null);
        setCreditAmount("");
        setCreditReason("");
        toast({ title: "اعتبار به‌روزرسانی شد", status: "success", duration: 2500 });
      },
      onError: (error) => {
        toast({ title: "تغییر اعتبار انجام نشد", description: localizedApiError(error), status: "error", duration: 5000 });
      },
    }
  );

  if (!getUserIsPending && !capabilities.isLoading && !canManage) {
    return <Navigate to="/" replace />;
  }

  const admins = query.data?.admins || [];
  const total = query.data?.total || 0;
  const activeOnPage = admins.filter((item) => item.account_status === "ACTIVE").length;
  const frozenOnPage = admins.filter((item) => item.account_status === "SUSPENDED").length;
  const walletOnPage = admins.reduce((sum, item) => (
    item.role === "OWNER" ? sum : sum + Number(item.policy.money_balance_toman || 0)
  ), 0);
  const selectedAdmins = admins.filter((item) => selectedIds.includes(item.id));

  const canEdit = (item: ManagedAdmin) =>
    hierarchyReady && (item.role !== "OWNER" || item.username === userData.username);
  const canAct = (item: ManagedAdmin) =>
    hierarchyReady && item.role !== "OWNER" && item.username !== userData.username;

  const openCreate = () => {
    setSelected(null);
    openAdminForm();
  };
  const openEdit = (item: ManagedAdmin) => {
    setSelected(item);
    openAdminForm();
  };
  const openDelete = (item: ManagedAdmin) => {
    setSelected(item);
    setDeleteStrategy("keep_users");
    deleteDisclosure.onOpen();
  };
  const openFreeze = (item: ManagedAdmin) => {
    setFreezeTarget(item);
    setFreezeReason("");
    freezeDisclosure.onOpen();
  };
  const openCredit = (item: ManagedAdmin, operation: "grant" | "reclaim") => {
    setCreditTarget(item);
    setCreditOperation(operation);
    setCreditAmount("");
    setCreditReason("");
    creditDisclosure.onOpen();
  };
  const clearFilters = () => {
    setBillingFilter("");
    setStatusFilter("");
    setPage(0);
  };
  const toggleSelection = (item: ManagedAdmin, checked: boolean) =>
    setSelectedIds((current) =>
      checked ? [...new Set([...current, item.id])] : current.filter((id) => id !== item.id)
    );

  const runStatusAction = (item: ManagedAdmin) => {
    if (item.account_status === "SUSPENDED") {
      quickAction.mutate({
        item,
        operation: item.active_owner_freeze_event_id ? "unfreeze" : "resume",
      });
      return;
    }
    if (item.account_status === "DISABLED") {
      if (window.confirm(`ادمین ${item.username} فعال شود؟`)) {
        quickAction.mutate({ item, operation: "activate" });
      }
      return;
    }
    openFreeze(item);
  };

  const statusActionLabel = (item: ManagedAdmin) => {
    if (item.account_status === "SUSPENDED") return "رفع فریز";
    if (item.account_status === "DISABLED") return "فعال‌سازی";
    return "فریز ادمین";
  };

  const renderActions = (item: ManagedAdmin) => (
    <Menu placement="bottom-end" isLazy>
      <MenuButton
        as={IconButton}
        aria-label={`عملیات ${item.username}`}
        icon={<MoreIcon />}
        size="sm"
        minW="34px"
        h="34px"
        variant="ghost"
        color="gray.400"
        borderRadius="9px"
        transition="background .16s ease, color .16s ease, transform .16s ease"
        _hover={{ bg: "whiteAlpha.100", color: "white", transform: "translateY(-1px)" }}
      />
      <MenuList
        minW="210px"
        py={1.5}
        bg="#0c1524"
        borderColor="rgba(148,163,184,.16)"
        boxShadow="0 18px 50px rgba(0,0,0,.38)"
        borderRadius="12px"
        overflow="hidden"
        zIndex={30}
      >
        <MenuItem bg="transparent" _hover={{ bg: "whiteAlpha.100" }} onClick={() => setExpandedUsername((current) => current === item.username ? null : item.username)}>
          {expandedUsername === item.username ? "بستن جزئیات" : "مشاهده جزئیات"}
        </MenuItem>
        <MenuItem bg="transparent" _hover={{ bg: "whiteAlpha.100" }} isDisabled={!canEdit(item)} onClick={() => openEdit(item)}>
          ویرایش
        </MenuItem>
        {canAct(item) && (
          <>
            <Divider my={1} borderColor="whiteAlpha.100" />
            <MenuItem color="green.300" bg="transparent" _hover={{ bg: "rgba(34,197,94,.08)" }} onClick={() => openCredit(item, "grant")}>
              افزایش اعتبار
            </MenuItem>
            <MenuItem color="orange.300" bg="transparent" _hover={{ bg: "rgba(245,158,11,.08)" }} onClick={() => openCredit(item, "reclaim")}>
              کاهش اعتبار
            </MenuItem>
            <MenuItem bg="transparent" _hover={{ bg: "whiteAlpha.100" }} onClick={() => runStatusAction(item)}>
              {statusActionLabel(item)}
            </MenuItem>
            {item.trial_quota_limit > 0 && (
              <MenuItem
                bg="transparent"
                _hover={{ bg: "whiteAlpha.100" }}
                onClick={() =>
                  window.confirm(`تعداد تست قابل ساخت ${item.username} به ${item.trial_quota_limit} برگردد؟`) &&
                  quickAction.mutate({ item, operation: "trial-reset" })
                }
              >
                بازنشانی سهمیه تست
              </MenuItem>
            )}
            <Divider my={1} borderColor="whiteAlpha.100" />
            <MenuItem color="red.300" bg="transparent" _hover={{ bg: "rgba(248,113,113,.08)" }} onClick={() => openDelete(item)}>
              حذف ادمین
            </MenuItem>
          </>
        )}
      </MenuList>
    </Menu>
  );

  return (
    <AppShell>
      <Stack spacing={5}>
        <Stack direction={{ base: "column", md: "row" }} justify="space-between" align={{ md: "center" }} gap={4}>
          <Box>
            <Text as="h1" fontSize={{ base: "2xl", md: "3xl" }} fontWeight="800" letterSpacing="-0.035em">
              {t("admins.title")}
            </Text>
            <Text mt={1} color="gray.500" fontSize="sm" maxW="680px">
              مدیریت ادمین‌ها، اعتبار، وضعیت و دسترسی‌ها در یک نمای خلاصه و عملیاتی.
            </Text>
          </Box>
          {canCreate && (
            <Button
              minH="42px"
              px={5}
              flexShrink={0}
              colorScheme="primary"
              color="#06120d"
              leftIcon={<AddIcon />}
              onClick={openCreate}
              borderRadius="10px"
              transition="transform .16s ease, box-shadow .16s ease"
              _hover={{ transform: "translateY(-1px)", boxShadow: "0 8px 24px rgba(34,197,94,.14)" }}
              _active={{ transform: "translateY(0)" }}
            >
              {t("admins.create")}
            </Button>
          )}
        </Stack>

        {!hierarchyReady && (
          <Alert status="warning" borderRadius="12px" alignItems="flex-start">
            <AlertIcon mt={0.5} />
            <Box>
              <Text fontWeight="800">ساختار ادمین‌ها روی سرور فعال نشده است.</Text>
              <Text mt={1} fontSize="sm">تا فعال‌سازی، مدیریت سلسله‌مراتب و بعضی دسترسی‌ها محدود است.</Text>
            </Box>
          </Alert>
        )}

        <SimpleGrid columns={{ base: 2, xl: 4 }} gap={3}>
          <SummaryStat label="کل ادمین‌ها" value={query.isLoading ? "—" : total.toLocaleString("fa-IR")} hint="در محدوده مدیریتی شما" />
          <SummaryStat label="فعال در این صفحه" value={query.isLoading ? "—" : activeOnPage.toLocaleString("fa-IR")} hint={`از ${admins.length.toLocaleString("fa-IR")} ردیف نمایش‌داده‌شده`} tone="green.300" />
          <SummaryStat label="فریز در این صفحه" value={query.isLoading ? "—" : frozenOnPage.toLocaleString("fa-IR")} hint="برای بررسی سریع وضعیت‌ها" tone="orange.300" />
          <SummaryStat label="کیف پول این صفحه" value={query.isLoading ? "—" : `${walletOnPage.toLocaleString("fa-IR")} تومان`} hint="جمع موجودی ادمین‌های قابل مشاهده" />
        </SimpleGrid>

        <Card
          bg={panel.bg}
          borderWidth="1px"
          borderColor={panel.borderColor}
          borderRadius="14px"
          boxShadow={panel.boxShadow}
          overflow="hidden"
        >
          <Stack
            direction={{ base: "column", xl: "row" }}
            p={{ base: 3, md: 4 }}
            gap={3}
            align={{ xl: "center" }}
            borderBottomWidth="1px"
            borderColor="rgba(148,163,184,.12)"
          >
            <InputGroup flex="1" minW={0}>
              <InputLeftElement pointerEvents="none" color="gray.500">
                <SearchIcon />
              </InputLeftElement>
              <Input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="جستجوی ادمین با نام کاربری..."
                minH="42px"
                borderRadius="10px"
                {...control}
              />
            </InputGroup>

            <Stack direction={{ base: "column", sm: "row" }} spacing={2} w={{ base: "full", xl: "auto" }}>
              <Select
                aria-label="فیلتر نوع اعتبار"
                value={billingFilter}
                minH="42px"
                w={{ base: "full", sm: "190px" }}
                borderRadius="10px"
                onChange={(event) => { setBillingFilter(event.target.value); setPage(0); }}
                {...control}
              >
                <option value="">همه نوع‌های اعتبار</option>
                <option value="USED_TRAFFIC">مصرف واقعی</option>
                <option value="ALLOCATED_TRAFFIC">حجم ساخته‌شده</option>
                <option value="USER_CREDIT">سقف اکانت</option>
              </Select>
              <Select
                aria-label="فیلتر وضعیت"
                value={statusFilter}
                minH="42px"
                w={{ base: "full", sm: "160px" }}
                borderRadius="10px"
                onChange={(event) => { setStatusFilter(event.target.value); setPage(0); }}
                {...control}
              >
                <option value="">همه وضعیت‌ها</option>
                <option value="ACTIVE">فعال</option>
                <option value="SUSPENDED">فریز</option>
                <option value="DISABLED">غیرفعال</option>
              </Select>
              {(billingFilter || statusFilter) && (
                <Button minH="42px" variant="ghost" color="gray.400" onClick={clearFilters}>
                  پاک‌کردن
                </Button>
              )}
            </Stack>
          </Stack>

          {selectedAdmins.length > 0 && (
            <HStack
              px={4}
              py={2.5}
              bg="rgba(59,130,246,.06)"
              borderBottomWidth="1px"
              borderColor="rgba(148,163,184,.12)"
            >
              <Text color="blue.200" fontSize="xs" fontWeight="700">
                {selectedAdmins.length.toLocaleString("fa-IR")} ادمین انتخاب شده
              </Text>
              <Button ms="auto" size="xs" variant="ghost" onClick={() => setSelectedIds([])}>لغو انتخاب</Button>
            </HStack>
          )}

          {query.isError && (
            <Alert status="error" m={4} w="auto" borderRadius="10px">
              <AlertIcon />
              {t("admins.loadFailed")}
              <Button ms="auto" size="sm" onClick={() => query.refetch()}>{t("retry")}</Button>
            </Alert>
          )}

          {query.isLoading ? (
            <Stack p={4}>
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} height="62px" borderRadius="10px" />
              ))}
            </Stack>
          ) : admins.length === 0 ? (
            <VStack py={16} px={5} spacing={3}>
              <Box p={3} color="gray.400" borderRadius="12px" borderWidth="1px" borderColor="whiteAlpha.100">
                <AdminsIcon />
              </Box>
              <Text fontWeight="700">{t("admins.empty")}</Text>
              <Text color="gray.500" fontSize="sm" textAlign="center">
                {t(search ? "admins.emptySearch" : "admins.emptyHelp")}
              </Text>
            </VStack>
          ) : (
            <>
              <TableContainer display={{ base: "none", lg: "block" }}>
                <Table size="sm">
                  <Thead bg="rgba(2,8,23,.34)">
                    <Tr>
                      <Th w="22%">ادمین</Th>
                      <Th w="13%">وضعیت</Th>
                      <Th w="17%">نقش و اعتبار</Th>
                      <Th w="15%">کیف پول</Th>
                      <Th w="18%">کاربران</Th>
                      <Th w="10%">والد</Th>
                      <Th w="5%" textAlign="end">عملیات</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {admins.map((item) => {
                      const expanded = expandedUsername === item.username;
                      const isItemOwner = item.role === "OWNER";
                      return (
                        <Fragment key={item.username}>
                          <Tr
                            role="group"
                            bg={expanded ? "rgba(59,130,246,.055)" : "transparent"}
                            transition="background-color .18s ease, box-shadow .18s ease"
                            _hover={{
                              bg: expanded ? "rgba(59,130,246,.07)" : "rgba(255,255,255,.025)",
                              boxShadow: "inset 3px 0 0 rgba(96,165,250,.45)",
                            }}
                          >
                            <Td py={3.5}>
                              <HStack spacing={3}>
                                {canAct(item) && (
                                  <Checkbox
                                    aria-label={`انتخاب ${item.username}`}
                                    isChecked={selectedIds.includes(item.id)}
                                    onChange={(event) => toggleSelection(item, event.target.checked)}
                                  />
                                )}
                                <AdminAvatar username={item.username} owner={isItemOwner} />
                                <Box minW={0}>
                                  <Text dir="ltr" textAlign="start" fontWeight="800" noOfLines={1}>
                                    {item.username}
                                  </Text>
                                  <Text mt={1} color="gray.600" fontSize="10px" noOfLines={1}>
                                    {item.user_creation_mode === "PLAN_ONLY" ? "ساخت کاربر فقط از پلن" : "ساخت کاربر سفارشی"}
                                  </Text>
                                </Box>
                              </HStack>
                            </Td>
                            <Td><StatusPill status={item.account_status} /></Td>
                            <Td>
                              <HStack spacing={1.5} flexWrap="wrap">
                                <Badge
                                  variant="subtle"
                                  colorScheme={isItemOwner ? "purple" : "blue"}
                                  fontSize="10px"
                                  textTransform="none"
                                >
                                  {t(`admins.role.${item.role}`)}
                                </Badge>
                                <Badge variant="outline" color="gray.400" borderColor="whiteAlpha.200" fontSize="10px" textTransform="none">
                                  {billingModeLabels[item.policy.billing_mode] || item.policy.billing_mode}
                                </Badge>
                              </HStack>
                            </Td>
                            <Td>
                              <Text fontWeight="800" sx={{ fontVariantNumeric: "tabular-nums" }}>
                                {isItemOwner ? "بدون سقف" : item.policy.money_balance_toman.toLocaleString("fa-IR")}
                              </Text>
                              {!isItemOwner && <Text mt={1} color="gray.600" fontSize="10px">تومان</Text>}
                            </Td>
                            <Td>
                              <CapacityRing current={item.quota.current_users} maximum={item.quota.max_users} />
                            </Td>
                            <Td>
                              <HStack spacing={1.5}>
                                {item.parent_username && <Box w="12px" h="1px" bg="whiteAlpha.200" />}
                                <Text dir="ltr" color={item.parent_username ? "gray.300" : "gray.600"} fontSize="xs" noOfLines={1}>
                                  {item.parent_username || "—"}
                                </Text>
                              </HStack>
                            </Td>
                            <Td textAlign="end">
                              <HStack justify="end" spacing={1}>
                                <IconButton
                                  aria-label={expanded ? "بستن جزئیات" : "باز کردن جزئیات"}
                                  icon={
                                    <ChevronIcon
                                      transition="transform .2s cubic-bezier(.22,1,.36,1)"
                                      transform={expanded ? "rotate(180deg)" : "rotate(0deg)"}
                                    />
                                  }
                                  size="sm"
                                  minW="34px"
                                  h="34px"
                                  variant="ghost"
                                  color="gray.500"
                                  onClick={() => setExpandedUsername((current) => current === item.username ? null : item.username)}
                                />
                                {renderActions(item)}
                              </HStack>
                            </Td>
                          </Tr>

                          <Tr bg="rgba(2,8,23,.22)">
                            <Td colSpan={7} p={0} borderBottomWidth={expanded ? "1px" : "0"} borderColor="rgba(148,163,184,.10)">
                              <Collapse in={expanded} animateOpacity>
                                <Box px={5} py={4}>
                                  <SimpleGrid columns={{ base: 2, xl: 6 }} gap={4}>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">مصرف کل</Text>
                                      <Text mt={1} fontSize="sm" fontWeight="700">{formatBytes(item.quota.lifetime_consumed_traffic)}</Text>
                                    </Box>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">ساخت کل</Text>
                                      <Text mt={1} fontSize="sm" fontWeight="700">{formatBytes(item.quota.lifetime_created_traffic)}</Text>
                                    </Box>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">{t("admins.operationRemaining")}</Text>
                                      <Text mt={1} fontSize="sm" fontWeight="700">{item.quota.operation_allowance_remaining ?? t("unlimited")}</Text>
                                    </Box>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">{t("admins.maxDuration")}</Text>
                                      <Text mt={1} fontSize="sm" fontWeight="700">
                                        {item.policy.max_user_duration_days ? `${item.policy.max_user_duration_days} ${t("days")}` : t("unlimited")}
                                      </Text>
                                    </Box>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">{t("admins.expiryDate")}</Text>
                                      <Text mt={1} dir="ltr" fontSize="sm" fontWeight="700">{item.policy.expiry_date || t("unlimited")}</Text>
                                    </Box>
                                    <Box>
                                      <Text color="gray.600" fontSize="10px">{t("admins.telegramId")}</Text>
                                      <Text mt={1} dir="ltr" fontSize="sm" fontWeight="700">{item.telegram_id ?? t("admins.noContact")}</Text>
                                    </Box>
                                  </SimpleGrid>
                                </Box>
                              </Collapse>
                            </Td>
                          </Tr>
                        </Fragment>
                      );
                    })}
                  </Tbody>
                </Table>
              </TableContainer>

              <Stack display={{ base: "flex", lg: "none" }} divider={<Divider borderColor="whiteAlpha.100" />} spacing={0}>
                {admins.map((item) => {
                  const expanded = expandedUsername === item.username;
                  const isItemOwner = item.role === "OWNER";
                  return (
                    <Box key={item.username} role="group" p={3.5} transition="background .18s ease" _hover={{ bg: "whiteAlpha.50" }}>
                      <HStack justify="space-between" align="start" gap={3}>
                        <HStack align="start" spacing={2.5} minW={0}>
                          {canAct(item) && (
                            <Checkbox
                              mt={1}
                              aria-label={`انتخاب ${item.username}`}
                              isChecked={selectedIds.includes(item.id)}
                              onChange={(event) => toggleSelection(item, event.target.checked)}
                            />
                          )}
                          <AdminAvatar username={item.username} owner={isItemOwner} />
                          <Box minW={0}>
                            <HStack spacing={2} flexWrap="wrap">
                              <Text dir="ltr" fontWeight="800">{item.username}</Text>
                              <StatusPill status={item.account_status} />
                            </HStack>
                            <Text mt={1} color="gray.600" fontSize="10px" dir="ltr">
                              {item.parent_username ? `↳ ${item.parent_username}` : "ادمین ریشه"}
                            </Text>
                          </Box>
                        </HStack>
                        {renderActions(item)}
                      </HStack>

                      <SimpleGrid columns={2} gap={3} mt={4}>
                        <Box>
                          <Text color="gray.600" fontSize="10px">نقش / اعتبار</Text>
                          <HStack mt={1.5} spacing={1} flexWrap="wrap">
                            <Badge colorScheme={isItemOwner ? "purple" : "blue"} fontSize="9px">{t(`admins.role.${item.role}`)}</Badge>
                            <Badge variant="outline" borderColor="whiteAlpha.200" color="gray.400" fontSize="9px">
                              {billingModeLabels[item.policy.billing_mode] || item.policy.billing_mode}
                            </Badge>
                          </HStack>
                        </Box>
                        <Box>
                          <Text color="gray.600" fontSize="10px">کیف پول</Text>
                          <Text mt={1.5} fontWeight="800">
                            {isItemOwner ? "بدون سقف" : `${item.policy.money_balance_toman.toLocaleString("fa-IR")} تومان`}
                          </Text>
                        </Box>
                      </SimpleGrid>

                      <HStack mt={4} justify="space-between">
                        <CapacityRing current={item.quota.current_users} maximum={item.quota.max_users} />
                        <Button
                          size="sm"
                          minH="40px"
                          variant="ghost"
                          rightIcon={
                            <ChevronIcon
                              transition="transform .2s cubic-bezier(.22,1,.36,1)"
                              transform={expanded ? "rotate(180deg)" : "rotate(0deg)"}
                            />
                          }
                          onClick={() => setExpandedUsername((current) => current === item.username ? null : item.username)}
                        >
                          جزئیات
                        </Button>
                      </HStack>

                      <Collapse in={expanded} animateOpacity>
                        <SimpleGrid columns={2} gap={3} mt={3} pt={3} borderTopWidth="1px" borderColor="whiteAlpha.100">
                          <Box><Text color="gray.600" fontSize="10px">مصرف کل</Text><Text mt={1} fontSize="sm">{formatBytes(item.quota.lifetime_consumed_traffic)}</Text></Box>
                          <Box><Text color="gray.600" fontSize="10px">ساخت کل</Text><Text mt={1} fontSize="sm">{formatBytes(item.quota.lifetime_created_traffic)}</Text></Box>
                          <Box><Text color="gray.600" fontSize="10px">{t("admins.operationRemaining")}</Text><Text mt={1} fontSize="sm">{item.quota.operation_allowance_remaining ?? t("unlimited")}</Text></Box>
                          <Box><Text color="gray.600" fontSize="10px">{t("admins.telegramId")}</Text><Text mt={1} dir="ltr" fontSize="sm">{item.telegram_id ?? t("admins.noContact")}</Text></Box>
                        </SimpleGrid>
                      </Collapse>
                    </Box>
                  );
                })}
              </Stack>
            </>
          )}

          {total > PAGE_SIZE && (
            <HStack
              justify="space-between"
              px={4}
              py={3}
              borderTopWidth="1px"
              borderColor="rgba(148,163,184,.12)"
            >
              <Text color="gray.600" fontSize="xs">
                {t("admins.page", { current: page + 1, total: Math.ceil(total / PAGE_SIZE) })}
              </Text>
              <HStack>
                <Button
                  size="sm"
                  variant="ghost"
                  minW="40px"
                  isDisabled={page === 0}
                  onClick={() => setPage((value) => value - 1)}
                >
                  {t("previous")}
                </Button>
                <Box
                  minW="34px"
                  h="34px"
                  display="grid"
                  placeItems="center"
                  borderRadius="9px"
                  bg="rgba(59,130,246,.14)"
                  borderWidth="1px"
                  borderColor="rgba(96,165,250,.22)"
                  color="blue.100"
                  fontSize="sm"
                  fontWeight="800"
                >
                  {(page + 1).toLocaleString("fa-IR")}
                </Box>
                <Button
                  size="sm"
                  variant="ghost"
                  minW="40px"
                  isDisabled={(page + 1) * PAGE_SIZE >= total}
                  onClick={() => setPage((value) => value + 1)}
                >
                  {t("next")}
                </Button>
              </HStack>
            </HStack>
          )}
        </Card>
      </Stack>

      <AdminFormDrawer isOpen={formDisclosure.isOpen} admin={selected} onClose={formDisclosure.onClose} />

      <AlertDialog isOpen={deleteDisclosure.isOpen} leastDestructiveRef={cancelRef} onClose={deleteDisclosure.onClose}>
        <AlertDialogOverlay bg="rgba(0,0,0,.72)">
          <AlertDialogContent bg="#0c1524" color="gray.100" borderWidth="1px" borderColor="rgba(148,163,184,.16)" borderRadius="14px">
            <AlertDialogHeader>{t("admins.deleteTitle")}</AlertDialogHeader>
            <AlertDialogBody>
              <Text mb={3}>{t("admins.deleteConfirm", { username: selected?.username })}</Text>
              <FormControl>
                <FormLabel>{t("admins.deleteStrategy")}</FormLabel>
                <Select value={deleteStrategy} onChange={(event) => setDeleteStrategy(event.target.value as typeof deleteStrategy)} {...control}>
                  <option value="keep_users">{t("admins.keepUsers")}</option>
                  <option value="disable_users">{t("admins.disableUsers")}</option>
                  <option value="delete_users">{t("admins.deleteUsers")}</option>
                </Select>
                <FormHelperText>{t(`admins.deleteStrategyHelp.${deleteStrategy}`)}</FormHelperText>
              </FormControl>
            </AlertDialogBody>
            <AlertDialogFooter borderTopWidth="1px" borderColor="whiteAlpha.100" gap={3}>
              <Button ref={cancelRef} variant="ghost" onClick={deleteDisclosure.onClose}>{t("cancel")}</Button>
              <Button
                colorScheme="red"
                isLoading={removeMutation.isLoading}
                onClick={() => selected && removeMutation.mutate({ username: selected.username, strategy: deleteStrategy })}
              >
                {t("delete")}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      <AlertDialog isOpen={freezeDisclosure.isOpen} leastDestructiveRef={cancelRef} onClose={freezeDisclosure.onClose}>
        <AlertDialogOverlay bg="rgba(0,0,0,.76)">
          <AlertDialogContent bg="#0c1524" color="gray.100" borderWidth="1px" borderColor="rgba(148,163,184,.16)" borderRadius="14px">
            <AlertDialogHeader>فریز {freezeTarget?.username}</AlertDialogHeader>
            <AlertDialogBody>
              <FormControl isRequired>
                <FormLabel>دلیل فریز</FormLabel>
                <Textarea
                  autoFocus
                  maxLength={512}
                  value={freezeReason}
                  onChange={(event) => setFreezeReason(event.target.value)}
                  placeholder="دلیل قابل نمایش برای این ادمین را بنویسید"
                  {...control}
                />
                <FormHelperText>این متن در حساب ادمین و گزارش فعالیت ثبت می‌شود.</FormHelperText>
              </FormControl>
            </AlertDialogBody>
            <AlertDialogFooter gap={3} borderTopWidth="1px" borderColor="whiteAlpha.100">
              <Button ref={cancelRef} variant="ghost" onClick={freezeDisclosure.onClose}>انصراف</Button>
              <Button
                colorScheme="orange"
                isLoading={quickAction.isLoading}
                isDisabled={!freezeReason.trim()}
                onClick={() => freezeTarget && quickAction.mutate({ item: freezeTarget, operation: "freeze", reason: freezeReason.trim() })}
              >
                فریز ادمین و زیرشاخه
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      <AlertDialog isOpen={creditDisclosure.isOpen} leastDestructiveRef={cancelRef} onClose={creditDisclosure.onClose}>
        <AlertDialogOverlay bg="rgba(0,0,0,.76)">
          <AlertDialogContent bg="#0c1524" color="gray.100" borderWidth="1px" borderColor="rgba(148,163,184,.16)" borderRadius="14px">
            <AlertDialogHeader>{creditOperation === "grant" ? "افزایش" : "کاهش"} اعتبار {creditTarget?.username}</AlertDialogHeader>
            <AlertDialogBody>
              <Stack spacing={3}>
                <FormControl isRequired>
                  <FormLabel>مقدار (تومان)</FormLabel>
                  <Input
                    autoFocus
                    type="number"
                    min={1}
                    step={1000}
                    dir="ltr"
                    value={creditAmount}
                    onChange={(event) => setCreditAmount(event.target.value)}
                    {...control}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>یادداشت اختیاری</FormLabel>
                  <Input maxLength={512} value={creditReason} onChange={(event) => setCreditReason(event.target.value)} {...control} />
                </FormControl>
              </Stack>
            </AlertDialogBody>
            <AlertDialogFooter gap={3} borderTopWidth="1px" borderColor="whiteAlpha.100">
              <Button ref={cancelRef} variant="ghost" onClick={creditDisclosure.onClose}>انصراف</Button>
              <Button
                colorScheme={creditOperation === "grant" ? "green" : "orange"}
                isLoading={creditMutation.isLoading}
                isDisabled={!creditTarget || !Number.isInteger(Number(creditAmount)) || Number(creditAmount) <= 0}
                onClick={() =>
                  creditTarget &&
                  creditMutation.mutate({
                    item: creditTarget,
                    operation: creditOperation,
                    amount: Number(creditAmount),
                    reason: creditReason.trim(),
                  })
                }
              >
                {creditOperation === "grant" ? "افزایش اعتبار" : "کاهش اعتبار"}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </AppShell>
  );
};

export default Admins;
