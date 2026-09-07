import {
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
  chakra,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  MagnifyingGlassIcon,
  PlusIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import debounce from "lodash.debounce";
import { ChangeEvent, FC, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AccountSummary, AdminCapabilities } from "types/Admin";
import { CreateUserFromPlan } from "./CreateUserFromPlan";

const SearchIcon = chakra(MagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });
const ReloadIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });

type AdminOption = { username: string };

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
      fontSize="11px"
      fontWeight="750"
      whiteSpace="nowrap"
      onClick={onClick}
      transition="transform .14s ease, border-color .14s ease, background .14s ease"
      _hover={{ transform: "translateY(-1px)", borderColor: palette.border, color: palette.color }}
      _active={{ transform: "translateY(0)" }}
    >
      {label}
    </Button>
  );
};

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

const SortButton: FC<{ active: boolean; label: string; onClick: () => void }> = ({ active, label, onClick }) => (
  <Button
    size="sm"
    h="34px"
    px={3}
    borderRadius="12px"
    variant="outline"
    aria-pressed={active}
    borderColor={active ? "var(--panel-accent-border)" : "var(--panel-border)"}
    bg={active ? "var(--panel-accent-soft)" : "var(--panel-nested)"}
    color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}
    fontSize="10px"
    fontWeight="800"
    whiteSpace="nowrap"
    onClick={onClick}
    transition="transform .14s ease, border-color .14s ease, background .14s ease"
    _hover={{ transform: "translateY(-1px)", borderColor: "var(--panel-accent-border)", color: "var(--panel-accent)" }}
    _active={{ transform: "translateY(0)" }}
  >
    {label}
  </Button>
);

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

  const changeAdmin = (event: ChangeEvent<HTMLSelectElement>) =>
    onFilterChange({ admin: event.target.value || undefined, offset: 0 });

  return (
    <Flex
      dir={i18n.dir()}
      w="full"
      minW={0}
      align="center"
      gap={1.5}
      wrap="wrap"
      justify="flex-start"
    >
      {canManageAdmins && (
        <Select
          aria-label="فیلتر ادمین"
          value={filters.admin || ""}
          onChange={changeAdmin}
          size="sm"
          h="34px"
          w={{ base: "full", sm: "180px" }}
          flexShrink={0}
          borderRadius="12px"
          fontSize="11px"
          fontWeight="700"
          {...control}
          sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
        >
          <option value="">همه ادمین‌ها</option>
          {adminOptions.data?.map((admin) => <option key={admin.username} value={admin.username}>{admin.username}</option>)}
        </Select>
      )}

      {sortOptions.map((option) => (
        <SortButton
          key={option.value}
          active={filters.sort === option.value}
          label={option.label}
          onClick={() => onFilterChange({ sort: option.value, offset: 0 })}
        />
      ))}
    </Flex>
  );
};

export const FiltersCompact: FC = () => {
  const { loading, filters, onFilterChange, refetchUsers, onCreateUser } = useDashboard();
  const { i18n } = useTranslation();
  const [search, setSearch] = useState(filters.search || "");
  const [planCreateOpen, setPlanCreateOpen] = useState(false);

  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"));
  const accountActive = account.data?.account_status === "ACTIVE";

  const updateSearch = useMemo(
    () => debounce((value: string) => onFilterChange({ search: value, offset: 0 }), 280),
    [onFilterChange]
  );

  const setStatus = (value?: typeof filters.status) =>
    onFilterChange({ status: value, offset: 0 });

  return (
    <Stack dir={i18n.dir()} spacing={2.5} px={{ base: 3, md: 4 }} pt={2.5} pb={3}>
      <Flex
        align="center"
        gap={2}
        wrap="wrap"
        w="full"
        minW={0}
      >
        <HStack spacing={1.5} flexWrap="wrap" flexShrink={0}>
          {accountActive && account.data?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "") && (
            <Button
              size="sm"
              h="38px"
              px={4}
              colorScheme="primary"
              color="var(--panel-accent-contrast)"
              leftIcon={<AddIcon />}
              onClick={() => onCreateUser(true)}
              borderRadius="12px"
              fontSize="11px"
            >
              افزودن کاربر
            </Button>
          )}
          {accountActive && (account.data?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "")) && (
            <Button
              size="sm"
              h="38px"
              px={4}
              colorScheme="primary"
              color="var(--panel-accent-contrast)"
              leftIcon={<AddIcon />}
              onClick={() => setPlanCreateOpen(true)}
              borderRadius="12px"
              fontSize="11px"
            >
              ساخت از پلن
            </Button>
          )}
          <IconButton
            aria-label="به‌روزرسانی کاربران"
            icon={loading ? <Spinner size="xs" /> : <ReloadIcon />}
            size="sm"
            minW="38px"
            w="38px"
            h="38px"
            variant="outline"
            borderColor="var(--panel-border)"
            onClick={refetchUsers}
            isDisabled={loading}
            borderRadius="12px"
          />
        </HStack>

        <HStack spacing={1.5} flexWrap="wrap" flex="0 1 auto">
          <StatusButton active={!filters.status} label="همه کاربران" onClick={() => setStatus(undefined)} />
          <StatusButton active={filters.status === "active"} label="فعال" tone="green" onClick={() => setStatus("active")} />
          <StatusButton active={filters.status === "disabled"} label="غیرفعال" tone="gray" onClick={() => setStatus("disabled")} />
          <StatusButton active={filters.status === "expired"} label="منقضی" tone="red" onClick={() => setStatus("expired")} />
          <StatusButton active={filters.status === "on_hold"} label="در انتظار" tone="orange" onClick={() => setStatus("on_hold")} />
        </HStack>

        <InputGroup
          flex="0 1 380px"
          minW={{ base: "full", md: "280px" }}
          maxW={{ base: "full", xl: "380px" }}
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
            placeholder="جستجو در نام کاربری یا توضیحات..."
            fontSize="11px"
            borderRadius="12px"
            {...control}
          />
        </InputGroup>
      </Flex>

      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default FiltersCompact;
