import {
  Box,
  Button,
  Flex,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Spinner,
  Stack,
  Text,
  chakra,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import debounce from "lodash.debounce";
import { ChangeEvent, FC, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities, UserPlan } from "types/Admin";
import { CreateUserFromPlan } from "./CreateUserFromPlan";

const SearchIcon = chakra(MagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });
const ReloadIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });
const FilterIcon = chakra(FunnelIcon, { baseStyle: { w: 4, h: 4 } });
const ClearIcon = chakra(XMarkIcon, { baseStyle: { w: 4, h: 4 } });

type AdminOption = { username: string };
type UsersSummary = {
  expiring_within_days: number;
  high_usage_threshold_percent: number;
};

const control = {
  bg: "var(--panel-nested)",
  color: "var(--panel-text)",
  borderColor: "var(--panel-border)",
  _hover: { borderColor: "var(--panel-border-strong)" },
  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },
} as const;

const statusPalettes = {
  primary: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },
  green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
  red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },
  orange: { color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },
  gray: { color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },
} as const;

const StatusButton: FC<{
  active: boolean;
  label: string;
  onClick: () => void;
  tone?: keyof typeof statusPalettes;
}> = ({ active, label, onClick, tone = "primary" }) => {
  const palette = statusPalettes[tone];
  return (
    <Button
      size="sm"
      h="36px"
      px={3.5}
      borderRadius="12px"
      variant="outline"
      borderColor={active ? palette.border : "var(--panel-border)"}
      bg={active ? palette.bg : "var(--panel-surface)"}
      color={active ? palette.color : "var(--panel-text-body)"}
      fontSize="xs"
      fontWeight="700"
      whiteSpace="nowrap"
      flexShrink={0}
      onClick={onClick}
      aria-pressed={active}
      transition="border-color .14s ease, background-color .14s ease"
      _hover={{ borderColor: palette.border, color: palette.color }}
      _active={{ transform: "translateY(0)" }}
    >
      {label}
    </Button>
  );
};

const FilterChip: FC<{
  active: boolean;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}> = ({ active, label, onClick, disabled }) => (
  <Button
    size="sm"
    h="32px"
    px={3}
    borderRadius="full"
    variant="outline"
    borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}
    bg={active ? "var(--panel-accent-soft)" : "var(--panel-nested)"}
    color={active ? "var(--panel-accent)" : "var(--panel-text-muted)"}
    fontSize="xs"
    fontWeight="700"
    whiteSpace="nowrap"
    flexShrink={0}
    aria-pressed={active}
    isDisabled={disabled}
    onClick={onClick}
    _hover={{ borderColor: "var(--panel-accent-border)", color: "var(--panel-accent)" }}
  >
    {label}
  </Button>
);

const sortOptions = [
  { value: "-created_at", label: "جدیدترین‌ها" },
  { value: "created_at", label: "قدیمی‌ترین‌ها" },
  { value: "username", label: "نام کاربری A-Z" },
  { value: "-username", label: "نام کاربری Z-A" },
  { value: "-used_traffic", label: "مصرف بیشتر" },
  { value: "used_traffic", label: "مصرف کمتر" },
  { value: "expire", label: "انقضای نزدیک" },
  { value: "-expire", label: "انقضای دور" },
] as const;

export const UserManagementControls: FC = () => {
  const { filters, onFilterChange } = useDashboard();
  const { userData } = useGetUser();
  const { i18n } = useTranslation();
  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities")
  );
  const canManageAdmins = Boolean(capabilities.data?.can_manage_admins);
  const adminOptions = useQuery<AdminOption[], Error>(
    "user-filter-admins",
    () => fetch("/admins", { query: { limit: 1000 } }),
    { enabled: canManageAdmins, staleTime: 30000 }
  );
  const plans = useQuery<UserPlan[], Error>(
    "user-plans",
    () => fetch("/user-plans"),
    { staleTime: 30000 }
  );
  const summary = useQuery<UsersSummary, Error>(
    ["users-summary"],
    () => fetch("/users/summary"),
    { staleTime: 15000 }
  );

  const changeAdmin = (event: ChangeEvent<HTMLSelectElement>) =>
    onFilterChange({ admin: event.target.value || undefined, offset: 0 });

  const changePlan = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    if (value === "without") {
      onFilterChange({ plan_id: undefined, without_plan: true, trial: undefined, offset: 0 });
      return;
    }
    onFilterChange({
      plan_id: value ? Number(value) : undefined,
      without_plan: undefined,
      offset: 0,
    });
  };

  const advancedActive = Boolean(
    filters.attention ||
    filters.expires_within_days ||
    filters.usage_percent_min ||
    filters.has_device_limit ||
    filters.unlimited_traffic ||
    filters.trial ||
    filters.inactive_hours
  );

  const clearAdvanced = () => onFilterChange({
    attention: undefined,
    expires_within_days: undefined,
    usage_percent_min: undefined,
    has_device_limit: undefined,
    unlimited_traffic: undefined,
    trial: undefined,
    inactive_hours: undefined,
    offset: 0,
  });

  return (
    <Stack dir={i18n.dir()} spacing={2.5} w="full" minW={0}>
      <Flex
        w="full"
        minW={0}
        align="center"
        gap={2}
        flexWrap="wrap"
        overflowX="visible"
        pb={{ base: 1, lg: 0 }}
        sx={{ scrollbarWidth: "thin" }}
      >
        {canManageAdmins && (
          <Select
            aria-label="فیلتر ادمین"
            value={filters.admin || ""}
            onChange={changeAdmin}
            size="sm"
            h="36px"
            w="170px"
            flexShrink={0}
            borderRadius="12px"
            fontSize="xs"
            fontWeight="700"
            {...control}
            sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
          >
            <option value="">همه ادمین‌ها</option>
            {adminOptions.data?.map((admin) => <option key={admin.username} value={admin.username}>{admin.username}</option>)}
          </Select>
        )}

        <Select
          aria-label="فیلتر پلن"
          value={filters.without_plan ? "without" : filters.plan_id ? String(filters.plan_id) : ""}
          onChange={changePlan}
          size="sm"
          h="36px"
          w="190px"
          flexShrink={0}
          borderRadius="12px"
          fontSize="xs"
          fontWeight="700"
          {...control}
          sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
        >
          <option value="">همه پلن‌ها</option>
          <option value="without">بدون پلن</option>
          {(plans.data || []).map((plan) => (
            <option key={plan.id} value={plan.id}>{plan.name}</option>
          ))}
        </Select>

        <Select
          aria-label="مرتب‌سازی کاربران"
          value={filters.sort}
          onChange={(event) => onFilterChange({ sort: event.target.value, offset: 0 })}
          size="sm"
          h="36px"
          w="175px"
          flexShrink={0}
          borderRadius="12px"
          fontSize="xs"
          fontWeight="700"
          {...control}
          sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </Select>
      </Flex>

      <HStack
        spacing={1.5}
        w="full"
        minW={0}
        overflowX="visible"
        flexWrap="wrap"
        pb={{ base: 1, xl: 0 }}
        sx={{ scrollbarWidth: "thin" }}
      >
        <HStack spacing={1} color="var(--panel-text-muted)" flexShrink={0}>
          <FilterIcon />
          <Text fontSize="xs" fontWeight="700" whiteSpace="nowrap">فیلتر هوشمند</Text>
        </HStack>
        <FilterChip
          active={Boolean(filters.attention)}
          label="نیازمند توجه"
          onClick={() => onFilterChange({ attention: filters.attention ? undefined : true, offset: 0 })}
        />
        <FilterChip
          active={Boolean(filters.expires_within_days)}
          label={summary.data ? `انقضا ≤ ${summary.data.expiring_within_days.toLocaleString("fa-IR")} روز` : "نزدیک انقضا"}
          disabled={!summary.data}
          onClick={() => onFilterChange({
            expires_within_days: filters.expires_within_days ? undefined : summary.data?.expiring_within_days,
            offset: 0,
          })}
        />
        <FilterChip
          active={Boolean(filters.usage_percent_min)}
          label={summary.data ? `مصرف ≥ ${summary.data.high_usage_threshold_percent.toLocaleString("fa-IR")}٪` : "مصرف بالا"}
          disabled={!summary.data}
          onClick={() => onFilterChange({
            usage_percent_min: filters.usage_percent_min ? undefined : summary.data?.high_usage_threshold_percent,
            offset: 0,
          })}
        />
        <FilterChip
          active={Boolean(filters.has_device_limit)}
          label="محدودیت دستگاه"
          onClick={() => onFilterChange({ has_device_limit: filters.has_device_limit ? undefined : true, offset: 0 })}
        />
        <FilterChip
          active={Boolean(filters.unlimited_traffic)}
          label="ترافیک نامحدود"
          onClick={() => onFilterChange({ unlimited_traffic: filters.unlimited_traffic ? undefined : true, offset: 0 })}
        />
        <FilterChip
          active={Boolean(filters.trial)}
          label="آزمایشی"
          onClick={() => onFilterChange({
            trial: filters.trial ? undefined : true,
            without_plan: filters.trial ? filters.without_plan : undefined,
            offset: 0,
          })}
        />
        <FilterChip
          active={Boolean(filters.inactive_hours)}
          label="بدون فعالیت ۷ روز"
          onClick={() => onFilterChange({ inactive_hours: filters.inactive_hours ? undefined : 24 * 7, offset: 0 })}
        />
        {advancedActive && (
          <Button
            size="xs"
            h="30px"
            px={2.5}
            flexShrink={0}
            variant="ghost"
            color="var(--panel-text-muted)"
            leftIcon={<ClearIcon />}
            onClick={clearAdvanced}
            fontSize="xs"
          >
            پاک کردن
          </Button>
        )}
      </HStack>
    </Stack>
  );
};

export const FiltersCompact: FC = () => {
  const { loading, filters, onFilterChange, refetchUsers, onCreateUser } = useDashboard();
  const { i18n } = useTranslation();
  const [search, setSearch] = useState(filters.search || "");
  const [planCreateOpen, setPlanCreateOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const { userData } = useGetUser();
  const isOwner = userData.is_sudo || userData.role === "OWNER";
  const advancedCount = [filters.admin, filters.plan_id, filters.without_plan, filters.attention, filters.expires_within_days, filters.usage_percent_min, filters.has_device_limit, filters.unlimited_traffic, filters.trial, filters.inactive_hours, filters.sort !== "-created_at"].filter(Boolean).length;
  useEffect(() => setSearch(filters.search || ""), [filters.search]);

  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"));
  const accountActive = account.data?.account_status === "ACTIVE";

  const updateSearch = useMemo(
    () => debounce((value: string) => onFilterChange({ search: value || undefined, offset: 0 }), 280),
    [onFilterChange]
  );
  useEffect(() => () => updateSearch.cancel(), [updateSearch]);

  const setStatus = (value?: typeof filters.status) =>
    onFilterChange({ status: value, offset: 0 });

  return (
    <Stack dir={i18n.dir()} spacing={2.5} px={{ base: 3, md: 3 }} pt={3} pb={3} minW={0}>
      <Flex align="center" gap={2} wrap="wrap" w="full" minW={0}>
        <InputGroup
          flex="1 1 300px"
          minW={{ base: "full", md: "260px" }}
          maxW={{ base: "full", xl: "430px" }}
          ms={{ base: 0, xl: "auto" }}
        >
          <InputLeftElement pointerEvents="none" h="38px" color="var(--panel-text-muted)"><SearchIcon /></InputLeftElement>
          <Input
            h="38px"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              updateSearch(event.target.value.trim());
            }}
            aria-label="جستجوی کاربران"
            placeholder="جستجو در نام کاربری یا توضیحات..."
            fontSize="xs"
            borderRadius="12px"
            {...control}
          />
        </InputGroup>
        <HStack
          spacing={1.5}
          w={{ base: "full", md: "auto" }}
          minW={0}
          overflowX={{ base: "auto", md: "visible" }}
          flexWrap="nowrap"
          flexShrink={0}
          pb={{ base: 1, md: 0 }}
          sx={{ scrollbarWidth: "thin" }}
        >
          {accountActive && (isOwner || account.data?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "")) && <Button size="sm" h="38px" colorScheme="primary" leftIcon={<AddIcon />} onClick={() => setPlanCreateOpen(true)}>ساخت سریع از پلن</Button>}
          {accountActive && account.data?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "") && <Button size="sm" h="38px" variant="outline" leftIcon={<AddIcon />} onClick={() => onCreateUser(true)}>ساخت سفارشی</Button>}
          <Button size="sm" h="38px" variant="outline" leftIcon={<FilterIcon />} aria-expanded={filtersOpen} aria-controls="user-advanced-filters" onClick={() => setFiltersOpen(v => !v)}>فیلترها{advancedCount ? ` (${advancedCount.toLocaleString("fa-IR")})` : ""}</Button>
          <IconButton
            aria-label="به‌روزرسانی کاربران"
            icon={loading ? <Spinner size="xs" /> : <ReloadIcon />}
            size="sm"
            minW="38px"
            w="38px"
            h="38px"
            flexShrink={0}
            variant="outline"
            borderColor="var(--panel-border)"
            onClick={refetchUsers}
            isDisabled={loading}
            borderRadius="12px"
          />
        </HStack>

        <HStack
          spacing={1.5}
          w={{ base: "full", lg: "auto" }}
          minW={0}
          overflowX="visible"
          flexWrap="wrap"
          flex="0 1 auto"
          pb={{ base: 1, lg: 0 }}
          sx={{ scrollbarWidth: "thin" }}
        >
          <StatusButton active={!filters.status} label="همه" onClick={() => setStatus(undefined)} />
          <StatusButton active={filters.status === "active"} label="فعال" tone="green" onClick={() => setStatus("active")} />
          <StatusButton active={filters.status === "disabled"} label="غیرفعال" tone="gray" onClick={() => setStatus("disabled")} />
          <StatusButton active={filters.status === "limited"} label="محدود" tone="orange" onClick={() => setStatus("limited")} />
          <StatusButton active={filters.status === "expired"} label="منقضی" tone="red" onClick={() => setStatus("expired")} />
          <StatusButton active={filters.status === "on_hold"} label="در انتظار" tone="orange" onClick={() => setStatus("on_hold")} />
        </HStack>


      </Flex>

      <Box id="user-advanced-filters" hidden={!filtersOpen} pt={filtersOpen ? 2 : 0} borderTopWidth={filtersOpen ? "1px" : 0} borderColor="var(--panel-border)">{filtersOpen && <UserManagementControls />}</Box>
      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default FiltersCompact;
