import {
  Box,
  Button,
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

const StatusButton: FC<{
  active: boolean;
  label: string;
  onClick: () => void;
  tone?: "primary" | "green" | "red" | "orange" | "gray";
}> = ({ active, label, onClick, tone = "primary" }) => (
  <Button
    size="sm"
    h="36px"
    px={4}
    borderRadius="8px"
    variant="outline"
    borderColor={active ? `${tone}.400` : "rgba(148,163,184,.18)"}
    bg={active ? `${tone}.900` : "rgba(2,6,23,.28)"}
    color={active ? `${tone}.100` : "gray.300"}
    fontSize="12px"
    fontWeight="800"
    onClick={onClick}
    transition="transform .14s ease, border-color .14s ease, background .14s ease"
    _hover={{ transform: "translateY(-1px)", borderColor: `${tone}.400` }}
    _active={{ transform: "translateY(0)" }}
  >
    {label}
  </Button>
);

export const FiltersCompact: FC = () => {
  const { loading, filters, onFilterChange, refetchUsers, onCreateUser } = useDashboard();
  const { i18n } = useTranslation();
  const { userData } = useGetUser();
  const [search, setSearch] = useState(filters.search || "");
  const [planCreateOpen, setPlanCreateOpen] = useState(false);

  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"));
  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities")
  );
  const canManageAdmins = Boolean(capabilities.data?.can_manage_admins);
  const accountActive = account.data?.account_status === "ACTIVE";
  const adminOptions = useQuery<AdminOption[], Error>(
    "user-filter-admins",
    () => fetch("/admins", { query: { limit: 1000 } }),
    { enabled: canManageAdmins, staleTime: 30000 }
  );

  const updateSearch = useMemo(
    () => debounce((value: string) => onFilterChange({ search: value, offset: 0 }), 280),
    [onFilterChange]
  );

  const setStatus = (value?: typeof filters.status) =>
    onFilterChange({ status: value, offset: 0 });

  const changeSort = (event: ChangeEvent<HTMLSelectElement>) =>
    onFilterChange({ sort: event.target.value, offset: 0 });

  const changeAdmin = (event: ChangeEvent<HTMLSelectElement>) =>
    onFilterChange({ admin: event.target.value || undefined, offset: 0 });

  return (
    <Stack dir={i18n.dir()} spacing={3} px={{ base: 3, md: 4 }} pt={3.5} pb={3}>
      <HStack
        justify="space-between"
        align="center"
        gap={3}
        flexWrap="wrap"
        direction="row"
      >
        <HStack spacing={2} flexWrap="wrap">
          {accountActive && account.data?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "") && (
            <Button
              size="sm"
              minH="38px"
              px={4}
              colorScheme="primary"
              color="var(--panel-accent-contrast)"
              leftIcon={<AddIcon />}
              onClick={() => onCreateUser(true)}
              borderRadius="8px"
            >
              افزودن کاربر
            </Button>
          )}
          {accountActive && (account.data?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "")) && (
            <Button
              size="sm"
              minH="38px"
              px={4}
              colorScheme="primary"
              color="var(--panel-accent-contrast)"
              leftIcon={<AddIcon />}
              onClick={() => setPlanCreateOpen(true)}
              borderRadius="8px"
            >
              ساخت از پلن
            </Button>
          )}
          <IconButton
            aria-label="به‌روزرسانی کاربران"
            icon={loading ? <Spinner size="xs" /> : <ReloadIcon />}
            size="sm"
            minW="38px"
            h="38px"
            variant="outline"
            borderColor="var(--panel-border)"
            onClick={refetchUsers}
            isDisabled={loading}
            borderRadius="8px"
          />
        </HStack>

        <HStack spacing={2} flexWrap="wrap" flex="1" justify="center">
          <StatusButton active={!filters.status} label="همه کاربران" onClick={() => setStatus(undefined)} />
          <StatusButton active={filters.status === "active"} label="فعال" tone="green" onClick={() => setStatus("active")} />
          <StatusButton active={filters.status === "disabled"} label="غیرفعال" tone="gray" onClick={() => setStatus("disabled")} />
          <StatusButton active={filters.status === "expired"} label="منقضی" tone="red" onClick={() => setStatus("expired")} />
          <StatusButton active={filters.status === "on_hold"} label="در انتظار" tone="orange" onClick={() => setStatus("on_hold")} />
        </HStack>

        <InputGroup w={{ base: "full", lg: "330px" }} flexShrink={0}>
          <InputLeftElement pointerEvents="none" h="38px" color="gray.500"><SearchIcon /></InputLeftElement>
          <Input
            h="38px"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              updateSearch(event.target.value.trim());
            }}
            placeholder="جستجو در نام کاربری یا توضیحات..."
            fontSize="12px"
            borderRadius="8px"
            {...control}
          />
        </InputGroup>
      </HStack>

      <HStack
        justify="space-between"
        align="center"
        gap={3}
        flexWrap="wrap"
        pt={2.5}
        borderTopWidth="1px"
        borderColor="var(--panel-border)"
      >
        <Text color="gray.500" fontSize="11px">فیلترهای تکمیلی</Text>
        <HStack spacing={2} flexWrap="wrap">
          {canManageAdmins && (
            <Select
              aria-label="فیلتر ادمین"
              value={filters.admin || ""}
              onChange={changeAdmin}
              size="sm"
              h="34px"
              w={{ base: "160px", md: "180px" }}
              borderRadius="8px"
              {...control}
              sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
            >
              <option value="">همه ادمین‌ها</option>
              {adminOptions.data?.map((admin) => <option key={admin.username} value={admin.username}>{admin.username}</option>)}
            </Select>
          )}
          <Select
            aria-label="مرتب‌سازی کاربران"
            value={filters.sort}
            onChange={changeSort}
            size="sm"
            h="34px"
            w={{ base: "170px", md: "200px" }}
            borderRadius="8px"
            {...control}
            sx={{ option: { background: "var(--panel-surface)", color: "var(--panel-text)" } }}
          >
            <option value="-created_at">جدیدترین‌ها</option>
            <option value="created_at">قدیمی‌ترین‌ها</option>
            <option value="username">نام کاربری A-Z</option>
            <option value="-username">نام کاربری Z-A</option>
            <option value="-used_traffic">مصرف بیشتر</option>
            <option value="used_traffic">مصرف کمتر</option>
            <option value="expire">انقضای نزدیک</option>
            <option value="-expire">انقضای دور</option>
          </Select>
        </HStack>
      </HStack>

      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default FiltersCompact;
