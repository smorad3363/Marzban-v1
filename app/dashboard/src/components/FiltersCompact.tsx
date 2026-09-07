import {
  Box,
  Button,
  Collapse,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Spinner,
  Stack,
  Text,
  Tooltip,
  chakra,
} from "@chakra-ui/react";
import {
  AdjustmentsHorizontalIcon,
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
const AdvancedIcon = chakra(AdjustmentsHorizontalIcon, { baseStyle: { w: 4, h: 4 } });

type AdminOption = { username: string };

const control = {
  bg: "var(--panel-surface)",
  color: "var(--panel-text)",
  borderColor: "var(--panel-border)",
  _hover: { borderColor: "var(--panel-border-strong)" },
  _focusVisible: { borderColor: "var(--panel-accent)", boxShadow: "0 0 0 2px var(--panel-accent-soft)" },
} as const;

const StatusSegment: FC<{ active: boolean; label: string; onClick: () => void }> = ({ active, label, onClick }) => (
  <Button
    size="sm"
    minH="34px"
    px={{ base: 2.5, md: 3.5 }}
    borderRadius="10px"
    variant="ghost"
    bg={active ? "var(--panel-surface)" : "transparent"}
    color={active ? "var(--panel-accent)" : "var(--panel-text-body)"}
    boxShadow={active ? "var(--shadow-row)" : "none"}
    fontSize="12px"
    fontWeight={active ? "750" : "600"}
    onClick={onClick}
    _hover={{ bg: active ? "var(--panel-surface)" : "var(--panel-row-hover)", color: active ? "var(--panel-accent)" : "var(--panel-text)" }}
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
  const [advancedOpen, setAdvancedOpen] = useState(Boolean(filters.admin));

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

  const setStatus = (value?: typeof filters.status) => onFilterChange({ status: value, offset: 0 });
  const changeSort = (event: ChangeEvent<HTMLSelectElement>) => onFilterChange({ sort: event.target.value, offset: 0 });
  const changeAdmin = (event: ChangeEvent<HTMLSelectElement>) => onFilterChange({ admin: event.target.value || undefined, offset: 0 });

  return (
    <Stack dir={i18n.dir()} spacing={3.5} px={{ base: 3, md: 4 }} pt={4} pb={3.5}>
      <HStack justify="space-between" align="center" gap={3} flexWrap="wrap">
        <HStack spacing={2} flexWrap="wrap">
          {accountActive && account.data?.billing_mode !== "USER_CREDIT" && ["FREE_FORM", "FORM_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "") && (
            <Button size="sm" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={() => onCreateUser(true)}>
              افزودن کاربر
            </Button>
          )}
          {accountActive && (account.data?.billing_mode === "USER_CREDIT" || ["PLAN_ONLY", "BOTH"].includes(account.data?.user_creation_mode || "")) && (
            <Button size="sm" colorScheme="primary" color="var(--panel-accent-contrast)" leftIcon={<AddIcon />} onClick={() => setPlanCreateOpen(true)}>
              ساخت از پلن
            </Button>
          )}
          <Tooltip label="به‌روزرسانی کاربران">
            <IconButton aria-label="به‌روزرسانی کاربران" icon={loading ? <Spinner size="xs" /> : <ReloadIcon />} size="sm" variant="outline" borderColor="var(--panel-border)" onClick={refetchUsers} isDisabled={loading} />
          </Tooltip>
        </HStack>

        <HStack
          spacing={1}
          p={1}
          bg="var(--panel-nested)"
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="14px"
          overflowX="auto"
          maxW="full"
        >
          <StatusSegment active={!filters.status} label="همه" onClick={() => setStatus(undefined)} />
          <StatusSegment active={filters.status === "active"} label="فعال" onClick={() => setStatus("active")} />
          <StatusSegment active={filters.status === "disabled"} label="غیرفعال" onClick={() => setStatus("disabled")} />
          <StatusSegment active={filters.status === "expired"} label="منقضی" onClick={() => setStatus("expired")} />
          <StatusSegment active={filters.status === "on_hold"} label="در انتظار" onClick={() => setStatus("on_hold")} />
        </HStack>

        <HStack w={{ base: "full", lg: "360px" }} flexShrink={0} spacing={2}>
          <InputGroup flex="1">
            <InputLeftElement pointerEvents="none" h="42px" color="var(--panel-text-muted)"><SearchIcon /></InputLeftElement>
            <Input
              h="42px"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                updateSearch(event.target.value.trim());
              }}
              placeholder="جستجوی کاربر..."
              fontSize="12px"
              {...control}
            />
          </InputGroup>
          <Tooltip label="فیلتر پیشرفته">
            <IconButton
              aria-label="فیلتر پیشرفته"
              aria-expanded={advancedOpen}
              icon={<AdvancedIcon />}
              h="42px"
              minW="42px"
              variant={advancedOpen ? "solid" : "outline"}
              color={advancedOpen ? "var(--panel-accent-contrast)" : "var(--panel-text-body)"}
              bg={advancedOpen ? "var(--panel-accent)" : "var(--panel-surface)"}
              borderColor={advancedOpen ? "var(--panel-accent)" : "var(--panel-border)"}
              onClick={() => setAdvancedOpen((value) => !value)}
              _hover={{ bg: advancedOpen ? "var(--panel-accent-hover)" : "var(--panel-row-hover)" }}
            />
          </Tooltip>
        </HStack>
      </HStack>

      <Collapse in={advancedOpen} animateOpacity>
        <Box pt={3} borderTopWidth="1px" borderColor="var(--panel-border)">
          <HStack justify="space-between" align="center" gap={3} flexWrap="wrap">
            <Text color="var(--panel-text-muted)" fontSize="11px">فیلترهای تکمیلی</Text>
            <HStack spacing={2} flexWrap="wrap">
              {canManageAdmins && (
                <Select aria-label="فیلتر ادمین" value={filters.admin || ""} onChange={changeAdmin} size="sm" w={{ base: "160px", md: "190px" }} {...control}>
                  <option value="">همه ادمین‌ها</option>
                  {adminOptions.data?.map((admin) => <option key={admin.username} value={admin.username}>{admin.username}</option>)}
                </Select>
              )}
              <Select aria-label="مرتب‌سازی کاربران" value={filters.sort} onChange={changeSort} size="sm" w={{ base: "180px", md: "210px" }} {...control}>
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
        </Box>
      </Collapse>

      <CreateUserFromPlan isOpen={planCreateOpen} onClose={() => setPlanCreateOpen(false)} />
    </Stack>
  );
};

export default FiltersCompact;
