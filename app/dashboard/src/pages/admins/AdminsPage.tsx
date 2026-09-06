import {
  Alert,
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AlertIcon,
  Box,
  Button,
  Card,
  Divider,
  FormControl,
  FormHelperText,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Textarea,
  VStack,
  chakra,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import { MagnifyingGlassIcon, PlusIcon } from "@heroicons/react/24/outline";
import { AdminFormDrawer } from "components/AdminFormDrawer";
import { AppShell } from "components/AppShell";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { Navigate, useSearchParams } from "react-router-dom";
import { fetch } from "service/http";
import { AdminCapabilities, ManagedAdmin, ManagedAdminList } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { AdminTable, CreditOperation } from "./AdminTable";
import { AdminsIcon, control, FilterButton, panel, SummaryStat } from "./AdminUi";

const SearchIcon = chakra(MagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });
const AddIcon = chakra(PlusIcon, { baseStyle: { w: 4, h: 4 } });
const PAGE_SIZE = 20;

type BillingFilter = "" | "USED_TRAFFIC" | "ALLOCATED_TRAFFIC" | "USER_CREDIT";
type StatusFilter = "" | "ACTIVE" | "SUSPENDED" | "DISABLED";
type DeleteStrategy = "delete_users" | "disable_users" | "keep_users";

export const AdminsPage: FC = () => {
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { userData, getUserIsPending, getUserIsSuccess } = useGetUser();

  const formDisclosure = useDisclosure();
  const openAdminForm = formDisclosure.onOpen;
  const deleteDisclosure = useDisclosure();
  const freezeDisclosure = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const [selected, setSelected] = useState<ManagedAdmin | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [billingFilter, setBillingFilter] = useState<BillingFilter>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [freezeTarget, setFreezeTarget] = useState<ManagedAdmin | null>(null);
  const [freezeReason, setFreezeReason] = useState("");
  const [creditAmounts, setCreditAmounts] = useState<Record<string, string>>({});
  const [deleteStrategy, setDeleteStrategy] = useState<DeleteStrategy>("keep_users");

  const capabilities = useQuery<AdminCapabilities, Error>(
    ["admin-capabilities", userData.username],
    () => fetch("/admin/capabilities"),
    { enabled: getUserIsSuccess }
  );

  const canManage = Boolean(capabilities.data?.can_manage_admins);
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
    }, 280);
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
    ({ username, strategy }: { username: string; strategy: DeleteStrategy }) =>
      fetch(`/admin/${username}`, { method: "DELETE", body: { strategy } }),
    {
      onSuccess: () => {
        refreshAdminData();
        toast({ title: t("admins.deleted"), status: "success", duration: 3000 });
        deleteDisclosure.onClose();
      },
      onError: (error) => {
        toast({
          title: t("admins.deleteFailed"),
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
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
          ? {
              reason_id: 1,
              idempotency_key: `freeze-${item.id}-${crypto.randomUUID()}`,
              note: reason,
            }
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
        toast({
          title: "عملیات انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  const creditMutation = useMutation(
    ({ item, operation, amount }: { item: ManagedAdmin; operation: CreditOperation; amount: number }) =>
      fetch(`/admin-management/${encodeURIComponent(item.username)}/money/${operation}`, {
        method: "POST",
        body: {
          amount_toman: Math.round(amount),
          idempotency_key: `admin-money-${crypto.randomUUID()}`,
        },
      }),
    {
      onSuccess: (_data, variables) => {
        refreshAdminData();
        setCreditAmounts((current) => ({ ...current, [variables.item.username]: "" }));
        toast({
          title: variables.operation === "grant" ? "اعتبار افزایش یافت" : "اعتبار کاهش یافت",
          status: "success",
          duration: 2200,
        });
      },
      onError: (error) => {
        toast({
          title: "تغییر اعتبار انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  if (!getUserIsPending && !capabilities.isLoading && !canManage) {
    return <Navigate to="/" replace />;
  }

  const rawAdmins = query.data?.admins || [];
  const admins = rawAdmins.filter((item) => item.username !== userData.username);
  const selfVisibleInResponse = rawAdmins.some((item) => item.username === userData.username);
  const total = Math.max(0, (query.data?.total || 0) - (selfVisibleInResponse ? 1 : 0));
  const activeOnPage = admins.filter((item) => item.account_status === "ACTIVE").length;
  const frozenOnPage = admins.filter((item) => item.account_status === "SUSPENDED").length;
  const walletOnPage = admins.reduce(
    (sum, item) => item.role === "OWNER" ? sum : sum + Number(item.policy.money_balance_toman || 0),
    0
  );

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

  const submitCredit = (item: ManagedAdmin, operation: CreditOperation) => {
    const amount = Number(creditAmounts[item.username]);
    if (!Number.isInteger(amount) || amount <= 0) {
      toast({ title: "مبلغ معتبر وارد کنید", status: "warning", duration: 2200 });
      return;
    }
    creditMutation.mutate({ item, operation, amount });
  };

  const trialReset = (item: ManagedAdmin) => {
    if (window.confirm(`تعداد تست قابل ساخت ${item.username} به ${item.trial_quota_limit} برگردد؟`)) {
      quickAction.mutate({ item, operation: "trial-reset" });
    }
  };

  const busy = creditMutation.isLoading || quickAction.isLoading || removeMutation.isLoading;

  return (
    <AppShell>
      <Stack spacing={5}>
        <Stack direction={{ base: "column", md: "row" }} justify="space-between" align={{ md: "center" }} gap={4}>
          <Box>
            <Text as="h1" fontSize={{ base: "2xl", md: "3xl" }} fontWeight="800" letterSpacing="-0.035em">
              {t("admins.title")}
            </Text>
            <Text mt={1} color="gray.400" fontSize="sm" maxW="680px">
              مدیریت ادمین‌ها، اعتبار، وضعیت و دسترسی‌ها در یک نمای سریع و عملیاتی.
            </Text>
          </Box>
          {canCreate && (
            <Button
              minH="42px"
              px={5}
              flexShrink={0}
              colorScheme="blue"
              leftIcon={<AddIcon />}
              onClick={openCreate}
              borderRadius="10px"
              transition="transform .16s ease, box-shadow .16s ease"
              _hover={{ transform: "translateY(-1px)", boxShadow: "0 8px 24px rgba(37,99,235,.20)" }}
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
              <Text mt={2} fontSize="sm">Use command-line administration to promote an Owner.</Text>
            </Box>
          </Alert>
        )}

        <SimpleGrid columns={{ base: 2, xl: 4 }} gap={3}>
          <SummaryStat label="کل ادمین‌ها" value={query.isLoading ? "—" : total.toLocaleString("fa-IR")} hint="در محدوده مدیریتی شما" />
          <SummaryStat label="فعال در این صفحه" value={query.isLoading ? "—" : activeOnPage.toLocaleString("fa-IR")} hint={`از ${admins.length.toLocaleString("fa-IR")} ردیف`} tone="green.300" />
          <SummaryStat label="فریز در این صفحه" value={query.isLoading ? "—" : frozenOnPage.toLocaleString("fa-IR")} hint="برای بررسی سریع وضعیت‌ها" tone="orange.300" />
          <SummaryStat label="کیف پول این صفحه" value={query.isLoading ? "—" : `${walletOnPage.toLocaleString("fa-IR")} تومان`} hint="جمع موجودی ادمین‌های قابل مشاهده" />
        </SimpleGrid>

        <Card
          bg={panel.bg}
          borderWidth="1px"
          borderColor={panel.borderColor}
          borderRadius="14px"
          boxShadow="0 16px 44px rgba(0,0,0,.18)"
          overflow="hidden"
        >
          <Stack
            direction={{ base: "column", xl: "row" }}
            p={{ base: 3, md: 3.5 }}
            gap={3}
            align={{ xl: "center" }}
            justify="space-between"
            borderBottomWidth="1px"
            borderColor="rgba(148,163,184,.12)"
          >
            <Stack direction={{ base: "column", md: "row" }} spacing={3} align={{ md: "center" }} flex="1" minW={0}>
              <HStack spacing={1.5} flexWrap="wrap">
                <Text color="gray.400" fontSize="11px" fontWeight="800">وضعیت:</Text>
                <FilterButton active={statusFilter === ""} onClick={() => { setStatusFilter(""); setPage(0); }}>همه</FilterButton>
                <FilterButton active={statusFilter === "ACTIVE"} onClick={() => { setStatusFilter("ACTIVE"); setPage(0); }}>فعال</FilterButton>
                <FilterButton active={statusFilter === "SUSPENDED"} onClick={() => { setStatusFilter("SUSPENDED"); setPage(0); }}>فریز</FilterButton>
                <FilterButton active={statusFilter === "DISABLED"} onClick={() => { setStatusFilter("DISABLED"); setPage(0); }}>غیرفعال</FilterButton>
              </HStack>

              <Divider display={{ base: "none", md: "block" }} orientation="vertical" h="28px" borderColor="whiteAlpha.200" />

              <HStack spacing={1.5} flexWrap="wrap">
                <Text color="gray.400" fontSize="11px" fontWeight="800">نوع اعتبار:</Text>
                <FilterButton active={billingFilter === ""} onClick={() => { setBillingFilter(""); setPage(0); }}>همه</FilterButton>
                <FilterButton active={billingFilter === "ALLOCATED_TRAFFIC"} onClick={() => { setBillingFilter("ALLOCATED_TRAFFIC"); setPage(0); }}>حجم ساخته‌شده</FilterButton>
                <FilterButton active={billingFilter === "USED_TRAFFIC"} onClick={() => { setBillingFilter("USED_TRAFFIC"); setPage(0); }}>مصرف واقعی</FilterButton>
                <FilterButton active={billingFilter === "USER_CREDIT"} onClick={() => { setBillingFilter("USER_CREDIT"); setPage(0); }}>سقف اکانت</FilterButton>
              </HStack>
            </Stack>

            <InputGroup w={{ base: "full", xl: "300px" }} flexShrink={0}>
              <InputLeftElement pointerEvents="none" color="gray.500" h="36px"><SearchIcon /></InputLeftElement>
              <Input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="جستجوی ادمین..."
                h="36px"
                borderRadius="8px"
                fontSize="12px"
                {...control}
              />
            </InputGroup>
          </Stack>

          {query.isError && (
            <Alert status="error" m={4} w="auto" borderRadius="10px">
              <AlertIcon />
              {t("admins.loadFailed")}
              <Button ms="auto" size="sm" onClick={() => query.refetch()}>{t("retry")}</Button>
            </Alert>
          )}

          {query.isLoading ? (
            <Stack p={4}>
              {Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} height="72px" borderRadius="10px" />)}
            </Stack>
          ) : admins.length === 0 ? (
            <VStack py={16} px={5} spacing={3}>
              <Box p={3} color="gray.400" borderRadius="12px" borderWidth="1px" borderColor="whiteAlpha.100"><AdminsIcon /></Box>
              <Text fontWeight="700">{t("admins.empty")}</Text>
              <Text color="gray.500" fontSize="sm" textAlign="center">{t(search ? "admins.emptySearch" : "admins.emptyHelp")}</Text>
            </VStack>
          ) : (
            <AdminTable
              admins={admins}
              currentUsername={userData.username}
              hierarchyReady={hierarchyReady}
              creditAmounts={creditAmounts}
              busy={busy}
              onCreditAmountChange={(username, value) => setCreditAmounts((current) => ({ ...current, [username]: value }))}
              onCredit={submitCredit}
              onEdit={openEdit}
              onDelete={openDelete}
              onStatus={runStatusAction}
              onTrialReset={trialReset}
            />
          )}

          {total > PAGE_SIZE && (
            <HStack justify="space-between" px={4} py={3} borderTopWidth="1px" borderColor="rgba(148,163,184,.12)">
              <Text color="gray.500" fontSize="xs">{t("admins.page", { current: page + 1, total: Math.ceil(total / PAGE_SIZE) })}</Text>
              <HStack>
                <Button size="sm" variant="ghost" minW="40px" isDisabled={page === 0} onClick={() => setPage((value) => value - 1)}>{t("previous")}</Button>
                <Box minW="34px" h="34px" display="grid" placeItems="center" borderRadius="9px" bg="rgba(37,99,235,.18)" borderWidth="1px" borderColor="rgba(96,165,250,.25)" color="blue.100" fontSize="sm" fontWeight="800">{(page + 1).toLocaleString("fa-IR")}</Box>
                <Button size="sm" variant="ghost" minW="40px" isDisabled={(page + 1) * PAGE_SIZE >= total} onClick={() => setPage((value) => value + 1)}>{t("next")}</Button>
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
                <Select value={deleteStrategy} onChange={(event) => setDeleteStrategy(event.target.value as DeleteStrategy)} {...control}>
                  <option value="keep_users">{t("admins.keepUsers")}</option>
                  <option value="disable_users">{t("admins.disableUsers")}</option>
                  <option value="delete_users">{t("admins.deleteUsers")}</option>
                </Select>
                <FormHelperText>{t(`admins.deleteStrategyHelp.${deleteStrategy}`)}</FormHelperText>
              </FormControl>
            </AlertDialogBody>
            <AlertDialogFooter borderTopWidth="1px" borderColor="whiteAlpha.100" gap={3}>
              <Button ref={cancelRef} variant="ghost" onClick={deleteDisclosure.onClose}>{t("cancel")}</Button>
              <Button colorScheme="red" isLoading={removeMutation.isLoading} onClick={() => selected && removeMutation.mutate({ username: selected.username, strategy: deleteStrategy })}>{t("delete")}</Button>
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
    </AppShell>
  );
};