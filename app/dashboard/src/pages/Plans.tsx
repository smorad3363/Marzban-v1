import { EmptyState, PageHeader, Surface } from "design-system/Console";
import { CatalogPager } from "components/plans/CatalogPager";
import { catalogPage, filterPlans } from "components/plans/presentation";
import { useSearchParams } from "react-router-dom";
import {
  Alert,
  Flex, Menu, MenuButton, MenuList, MenuItem, Table, Tbody, Td, Th, Thead, Tr,
  Tabs, TabList, Tab, TabPanels, TabPanel,
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AlertIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormHelperText,
  FormLabel,
  HStack,
  Icon,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Textarea,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import {
  EllipsisHorizontalIcon,
  ArchiveBoxIcon,
  CircleStackIcon,
  PencilSquareIcon,
  PlusIcon,
} from "@heroicons/react/24/outline";
import { AccessGroupManager } from "components/AccessGroupManager";
import { AppShell } from "components/AppShell";
import useGetUser from "hooks/useGetUser";
import { FC, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { AccessGroup, AccountSummary, PlanCategory, UserPlan } from "types/Admin";
import { formatBytes } from "utils/formatByte";
import { localizedApiError } from "utils/apiError";

const GIB = 1024 ** 3;

type PlanDraft = {
  name: string;
  description: string;
  dataGiB: string;
  priceToman: string;
  durationDays: string;
  deviceLimit: string;
  resetStrategy: "no_reset" | "day" | "week" | "month" | "year";
  categoryId: string;
  isTrial: boolean;
};

const emptyDraft = (): PlanDraft => ({
  name: "",
  description: "",
  dataGiB: "10",
  priceToman: "50000",
  durationDays: "30",
  deviceLimit: "",
  resetStrategy: "no_reset",
  categoryId: "",
  isTrial: false,
});

const resetLabels: Record<PlanDraft["resetStrategy"], string> = {
  no_reset: "بدون ریست",
  day: "روزانه",
  week: "هفتگی",
  month: "ماهانه",
  year: "سالانه",
};

const errorText = localizedApiError;

export const Plans: FC = () => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { getUserIsPending } = useGetUser();
  const modal = useDisclosure();
  const categoryModal = useDisclosure();
  const quickCreate = useDisclosure();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(0);
  const [creationPlan, setCreationPlan] = useState<UserPlan | null>(null);
  const [detailsPlan, setDetailsPlan] = useState<UserPlan | null>(null);
  const archiveDialog = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const submitLock = useRef(false);
  const [editing, setEditing] = useState<UserPlan | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<UserPlan | null>(null);
  const [draft, setDraft] = useState<PlanDraft>(emptyDraft());
  const [newCategoryName, setNewCategoryName] = useState("");
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [editingCategoryName, setEditingCategoryName] = useState("");
  const [usernames, setUsernames] = useState<Record<number, string>>({});
  const [accessGroupIds, setAccessGroupIds] = useState<Record<number, string>>({});
  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"), { enabled: !getUserIsPending });
  const plans = useQuery<UserPlan[], Error>("user-plans", () => fetch("/user-plans"), { enabled: !getUserIsPending });
  const categories = useQuery<PlanCategory[], Error>("plan-categories", () => fetch("/plan-categories"), { enabled: !getUserIsPending });
  const accessGroups = useQuery<AccessGroup[], Error>("access-groups", () => fetch("/access-groups"), { enabled: !getUserIsPending });
  const accountActive = account.data?.account_status === "ACTIVE";
  const canManage = accountActive && (account.data?.role === "OWNER" || account.data?.can_manage_plans);

  useEffect(() => {
    if (!modal.isOpen) return;
    setDraft(editing ? {
      name: editing.name,
      description: editing.description || "",
      dataGiB: String(editing.version.data_limit / GIB),
      priceToman: String(editing.version.price_toman),
      durationDays: String(editing.version.duration_days),
      deviceLimit: editing.version.concurrent_user_limit === null ? "" : String(editing.version.concurrent_user_limit),
      resetStrategy: editing.version.reset_strategy,
      categoryId: editing.category_id === null ? "" : String(editing.category_id),
      isTrial: editing.is_trial,
    } : emptyDraft());
  }, [editing, modal.isOpen]);

  const save = useMutation(
    () => {
      const payload = {
        ...(editing ? {} : { name: draft.name.trim(), is_trial: draft.isTrial }),
        description: draft.description.trim() || null,
        category_id: draft.categoryId ? Number(draft.categoryId) : null,
        version: {
          price_toman: draft.isTrial ? 0 : Number(draft.priceToman),
          data_limit: Math.round(Number(draft.dataGiB) * GIB),
          duration_days: Number(draft.durationDays),
          concurrent_user_limit: draft.deviceLimit ? Number(draft.deviceLimit) : null,
          reset_strategy: draft.resetStrategy,
          renewal_volume_strategy: "replace",
          renewal_time_strategy: "extend_max",
        },
        allowed_admin_ids: editing ? editing.allowed_admin_ids : [],
        include_subtree: editing ? editing.include_subtree : false,
      };
      return fetch(editing ? `/user-plans/${editing.id}` : "/user-plans", { method: editing ? "PUT" : "POST", body: payload });
    },
    {
      onSuccess: () => { queryClient.invalidateQueries("user-plans"); modal.onClose(); toast({ title: "پلن ذخیره شد", status: "success", duration: 3000 }); },
      onError: (error) => { toast({ title: "ذخیره پلن انجام نشد", description: errorText(error), status: "error", duration: 5000 }); },
    }
  );

  const createCategory = useMutation(
    () => fetch("/plan-categories", {
      method: "POST",
      body: { name: newCategoryName.trim(), description: null },
    }),
    {
      onSuccess: () => {
        setNewCategoryName("");
        queryClient.invalidateQueries("plan-categories");
        toast({ title: "دسته‌بندی ساخته شد", status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({ title: "ساخت دسته‌بندی انجام نشد", description: errorText(error), status: "error", duration: 5000 });
      },
    }
  );

  const updateCategory = useMutation(
    ({ category, name }: { category: PlanCategory; name: string }) => fetch(`/plan-categories/${category.id}`, {
      method: "PUT",
      body: { name: name.trim(), description: category.description },
    }),
    {
      onSuccess: () => {
        setEditingCategoryId(null);
        setEditingCategoryName("");
        queryClient.invalidateQueries("plan-categories");
        toast({ title: "دسته‌بندی ویرایش شد", status: "success", duration: 3000 });
      },
      onError: (error) => { toast({ title: "ویرایش دسته‌بندی انجام نشد", description: errorText(error), status: "error", duration: 5000 }); },
    }
  );

  const archiveCategory = useMutation(
    (category: PlanCategory) => fetch(`/plan-categories/${category.id}`, { method: "DELETE" }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("plan-categories");
        toast({ title: "دسته‌بندی بایگانی شد", status: "success", duration: 3000 });
      },
      onError: (error) => { toast({ title: "بایگانی دسته‌بندی انجام نشد", description: errorText(error), status: "error", duration: 5000 }); },
    }
  );

  const createUser = useMutation(
    ({ plan, username, accessGroupId }: { plan: UserPlan; username: string; accessGroupId: number }) => fetch("/users/from-plan", {
      method: "POST",
      body: { plan_id: plan.id, access_group_id: accessGroupId, username, status: "active", idempotency_key: `create-${plan.id}-${crypto.randomUUID()}` },
    }),
    {
      onSuccess: (_, values) => { setUsernames((current) => ({ ...current, [values.plan.id]: "" })); setAccessGroupIds((current) => ({ ...current, [values.plan.id]: "" })); queryClient.invalidateQueries("users"); queryClient.invalidateQueries("account-summary"); toast({ title: "کاربر از پلن ساخته شد", status: "success", duration: 3000 }); },
      onError: (error) => { toast({ title: "ساخت کاربر انجام نشد", description: errorText(error), status: "error", duration: 5000 }); },
    }
  );

  const archive = useMutation(
    (plan: UserPlan) => fetch(`/user-plans/${plan.id}`, { method: "DELETE" }),
    {
      onSuccess: () => { queryClient.invalidateQueries("user-plans"); archiveDialog.onClose(); toast({ title: "پلن بایگانی شد", status: "success", duration: 3000 }); },
      onError: (error) => { toast({ title: "بایگانی انجام نشد", description: errorText(error), status: "error", duration: 5000 }); },
    }
  );

  const isOwner = account.data?.role === "OWNER";
  const tabIndex = isOwner && searchParams.get("view") === "access-groups" ? 1 : 0;
  const filteredPlans = useMemo(() => filterPlans(plans.data || [], search, categoryFilter), [plans.data, search, categoryFilter]);
  const currentPage = catalogPage(filteredPlans, page);
  const changeTab = (index: number) => setSearchParams((current) => {
    const next = new URLSearchParams(current);
    if (index === 1 && isOwner) next.set("view", "access-groups");
    else next.delete("view");
    return next;
  }, { preventScrollReset: true });
  const openUserCreate = (plan: UserPlan) => { createUser.reset(); setCreationPlan(plan); quickCreate.onOpen(); };
  useEffect(() => { if (createUser.isSuccess) quickCreate.onClose(); }, [createUser.isSuccess, quickCreate.onClose]);
  useEffect(() => { setPage(0); }, [search, categoryFilter]);

  useEffect(() => { if (!save.isLoading) submitLock.current = false; }, [save.isLoading]);

  const openCreate = () => { save.reset(); setEditing(null); modal.onOpen(); };
  const openEdit = (plan: UserPlan) => { save.reset(); setEditing(plan); modal.onOpen(); };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (save.isLoading || submitLock.current) return;
    if (!draft.categoryId) {
      toast({ title: "دسته‌بندی پلن را انتخاب کنید", status: "warning", duration: 3000 });
      return;
    }
    submitLock.current = true;
    save.mutate();
  };

  const renderActions = (plan: UserPlan) => <HStack spacing={1} justify="flex-end" flexWrap="wrap">
    {accountActive && <Button size="sm" minH="44px" variant="outline" colorScheme="primary" onClick={() => openUserCreate(plan)}>ساخت کاربر</Button>}
    <Menu isLazy placement="bottom-end">
      <MenuButton as={Button} size="sm" minH="44px" minW="44px" p={2} variant="ghost" aria-label={`عملیات پلن ${plan.name}`}><Icon as={EllipsisHorizontalIcon} boxSize={5} /></MenuButton>
      <MenuList><MenuItem onClick={() => setDetailsPlan(plan)}>جزئیات پلن</MenuItem>
        {canManage && <MenuItem onClick={() => openEdit(plan)}>ویرایش پلن</MenuItem>}
        {canManage && <MenuItem color="var(--panel-danger)" onClick={() => { setArchiveTarget(plan); archiveDialog.onOpen(); }}>بایگانی</MenuItem>}
      </MenuList>
    </Menu>
  </HStack>;
  const renderQuickCreate = (plan: UserPlan) => <>
    <ModalOverlay /><ModalContent mx={3} my={3} maxH="calc(100dvh - 24px)">
      <ModalHeader ps={14}>ساخت کاربر از پلن</ModalHeader><ModalCloseButton isDisabled={createUser.isLoading} />
      <ModalBody><Stack spacing={4}>
        <Box p={3} bg="var(--panel-nested)" borderRadius="12px"><Text fontWeight="700">{plan.name}</Text><Text mt={1} fontSize="sm" color="var(--panel-text-muted)">{formatBytes(plan.version.data_limit)} · {plan.version.duration_days.toLocaleString("fa-IR")} روز · {(plan.is_trial ? 0 : plan.effective_price_toman).toLocaleString("fa-IR")} تومان</Text></Box>
        {createUser.isError && <Alert status="error" role="alert"><AlertIcon />{errorText(createUser.error)}</Alert>}
        <FormControl isRequired><FormLabel fontSize="sm">گروه دسترسی</FormLabel><Select minH="44px" value={accessGroupIds[plan.id] || ""} isDisabled={accessGroups.isLoading || accessGroups.isError} onChange={(event) => setAccessGroupIds((current) => ({ ...current, [plan.id]: event.target.value }))}><option value="">انتخاب دسترسی شبکه</option>{(accessGroups.data || []).map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</Select><FormHelperText>پلن مشخصات اشتراک را تعیین می‌کند؛ گروه، مسیر اتصال را.</FormHelperText></FormControl>
        {accessGroups.isError && <Alert status="error"><AlertIcon />گروه‌های دسترسی دریافت نشدند.<Button variant="ghost" size="sm" onClick={() => accessGroups.refetch()}>تلاش دوباره</Button></Alert>}
        {!accessGroups.isLoading && !accessGroups.isError && !accessGroups.data?.length && <Alert status="warning"><AlertIcon /><Box>گروه دسترسی قابل استفاده‌ای وجود ندارد.{isOwner && <Button mt={2} variant="outline" size="sm" onClick={() => { quickCreate.onClose(); changeTab(1); }}>مدیریت گروه‌های دسترسی</Button>}</Box></Alert>}
        <FormControl isRequired><FormLabel fontSize="sm">نام کاربری جدید</FormLabel><Input minH="44px" dir="ltr" value={usernames[plan.id] || ""} placeholder="username" onChange={(event) => setUsernames((current) => ({ ...current, [plan.id]: event.target.value }))} /></FormControl>
      </Stack></ModalBody>
      <ModalFooter gap={2} flexShrink={0}><Button variant="ghost" isDisabled={createUser.isLoading} onClick={quickCreate.onClose}>انصراف</Button><Button colorScheme="primary" isDisabled={!usernames[plan.id]?.trim() || !accessGroupIds[plan.id]} isLoading={createUser.isLoading} loadingText="در حال ساخت" onClick={() => createUser.mutate({ plan, username: usernames[plan.id].trim(), accessGroupId: Number(accessGroupIds[plan.id]) })}>ساخت کاربر</Button></ModalFooter>
    </ModalContent>
  </>;

  return (
    <AppShell>
      <PageHeader title="پلن‌ها و گروه‌های دسترسی" description="پلن برای شرایط اشتراک؛ گروه برای شبکه و مجوز استفاده." />
      <Tabs index={tabIndex} onChange={changeTab} isLazy lazyBehavior="keepMounted" isManual variant="line" colorScheme="primary">
        <TabList gap={2} borderColor="var(--panel-border)" mb={5}>
          <Tab minH="48px" flex={{ base: 1, md: "initial" }} px={{ base: 2, md: 4 }} fontSize={{ base: "sm", md: "md" }} fontWeight="600">پلن‌ها <Badge ms={2} display={{ base: "none", sm: "inline-flex" }}>{(plans.data || []).length.toLocaleString("fa-IR")}</Badge></Tab>
          {account.data?.role === "OWNER" && <Tab minH="48px" flex={{ base: 1, md: "initial" }} px={{ base: 2, md: 4 }} fontSize={{ base: "sm", md: "md" }} fontWeight="600">گروه‌های دسترسی <Badge ms={2} display={{ base: "none", sm: "inline-flex" }}>{(accessGroups.data || []).length.toLocaleString("fa-IR")}</Badge></Tab>}
        </TabList>
        <TabPanels>
          <TabPanel p={0}>
            <Stack spacing={4}>
              <Flex justify="space-between" align="center" gap={3} flexWrap="wrap">
                <Box><Text as="h2" fontSize="lg" fontWeight="700">فهرست پلن‌ها</Text></Box>
                {canManage && <HStack flexWrap="wrap" gap={2} spacing={0}>
                  <Button variant="outline" onClick={categoryModal.onOpen}>مدیریت دسته‌ها</Button>
                  <Button colorScheme="primary" leftIcon={<Icon as={PlusIcon} boxSize={4} />} onClick={openCreate} isDisabled={(categories.data || []).length === 0}>پلن جدید</Button>
                </HStack>}
              </Flex>
              {canManage && !categories.isLoading && !categories.isError && !categories.data?.length && <Alert status="info"><AlertIcon /><Box>برای ساخت اولین پلن، ابتدا یک دسته‌بندی ایجاد کنید.<Button ms={2} variant="outline" size="sm" onClick={categoryModal.onOpen}>ساخت دسته‌بندی</Button></Box></Alert>}
              {categories.isError && <Alert status="error"><AlertIcon />دسته‌بندی‌ها دریافت نشدند.<Button variant="ghost" size="sm" onClick={() => categories.refetch()}>تلاش دوباره</Button></Alert>}
              {plans.isError && <Alert status="error"><AlertIcon />پلن‌ها دریافت نشدند.<Button variant="ghost" size="sm" onClick={() => plans.refetch()}>تلاش دوباره</Button></Alert>}
              <Surface p={{ base: 3, md: 4 }}>
                <Stack direction={{ base: "column", md: "row" }} spacing={3} mb={4}>
                  <Input type="search" aria-label="جستجوی پلن" placeholder="جستجوی نام یا توضیح پلن…" value={search} onChange={(event) => setSearch(event.target.value)} />
                  <Select aria-label="فیلتر دسته‌بندی پلن" maxW={{ md: "240px" }} value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option value="">همه دسته‌بندی‌ها</option>{(categories.data || []).map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</Select>
                  {(search || categoryFilter) && <Button variant="ghost" onClick={() => { setSearch(""); setCategoryFilter(""); }}>پاک‌کردن فیلترها</Button>}
                </Stack>
                {plans.isLoading ? <Stack spacing={3}>{[1, 2, 3, 4].map(value => <Skeleton key={value} h="76px" borderRadius="12px" />)}</Stack> : !plans.isError && <>
                  {!!currentPage.items.length && <>
                    <Box display={{ base: "none", xl: "block" }} overflowX="auto">
                      <Table size="sm" sx={{ th: { whiteSpace: "nowrap", fontSize: "12px" }, td: { py: 3, fontSize: "sm" } }}>
                        <Thead><Tr><Th textAlign="start">پلن</Th><Th textAlign="start">حجم</Th><Th textAlign="start">مدت</Th><Th textAlign="start">دستگاه</Th><Th textAlign="start">قیمت</Th><Th textAlign="end">عملیات</Th></Tr></Thead>
                        <Tbody>{currentPage.items.map(plan => <Tr key={plan.id} _hover={{ bg: "var(--panel-row-hover)" }}>
                          <Td maxW="240px"><Text fontWeight="600" noOfLines={2} title={plan.name}>{plan.name}</Text><HStack mt={1} spacing={2} flexWrap="wrap"><Text fontSize="xs" color="var(--panel-text-muted)">{plan.category_name || "بدون دسته"}</Text>{plan.is_trial && <Badge colorScheme="blue">تست رایگان</Badge>}</HStack></Td>
                          <Td><Text dir="auto" whiteSpace="nowrap">{formatBytes(plan.version.data_limit)}</Text></Td><Td>{plan.version.duration_days.toLocaleString("fa-IR")} روز</Td><Td>{plan.version.concurrent_user_limit === null ? "نامحدود" : plan.version.concurrent_user_limit.toLocaleString("fa-IR")}</Td>
                          <Td><Text fontWeight="600" whiteSpace="nowrap">{(plan.is_trial ? 0 : plan.effective_price_toman).toLocaleString("fa-IR")} <Text as="span" fontSize="xs" color="var(--panel-text-muted)">تومان</Text></Text></Td><Td>{renderActions(plan)}</Td>
                        </Tr>)}</Tbody>
                      </Table>
                    </Box>
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={3} display={{ base: "grid", xl: "none" }} aria-label="کارت‌های پلن">
                      {currentPage.items.map(plan => <Box key={plan.id} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" p={4} minW={0}>
                        <Flex gap={2} align="start" justify="space-between"><Box minW={0}><Text as="h3" fontWeight="700" noOfLines={2} title={plan.name}>{plan.name}</Text><Text fontSize="xs" color="var(--panel-text-muted)" mt={1}>{plan.category_name || "بدون دسته"}</Text></Box>{plan.is_trial && <Badge colorScheme="blue" flexShrink={0}>تست رایگان</Badge>}</Flex>
                        <SimpleGrid columns={3} gap={2} my={4} fontSize="sm"><Box><Text fontSize="xs" color="var(--panel-text-muted)">حجم</Text><Text dir="auto" mt={1}>{formatBytes(plan.version.data_limit)}</Text></Box><Box><Text fontSize="xs" color="var(--panel-text-muted)">مدت</Text><Text mt={1}>{plan.version.duration_days.toLocaleString("fa-IR")} روز</Text></Box><Box><Text fontSize="xs" color="var(--panel-text-muted)">دستگاه</Text><Text mt={1}>{plan.version.concurrent_user_limit === null ? "نامحدود" : plan.version.concurrent_user_limit.toLocaleString("fa-IR")}</Text></Box></SimpleGrid>
                        <Text fontWeight="700" mb={3}>{(plan.is_trial ? 0 : plan.effective_price_toman).toLocaleString("fa-IR")} <Text as="span" fontWeight="400" fontSize="xs" color="var(--panel-text-muted)">تومان</Text></Text>{renderActions(plan)}
                      </Box>)}
                    </SimpleGrid>
                  </>}
                  {!currentPage.items.length && <EmptyState text={search || categoryFilter ? "پلنی با این فیلتر پیدا نشد" : "پلنی در دسترس نیست"} description={search || categoryFilter ? "نام دیگری جستجو کنید یا فیلتر دسته‌بندی را تغییر دهید." : "مالک پنل یا مدیر مجاز می‌تواند نخستین پلن را بسازد."} />}
                  <CatalogPager count={filteredPlans.length} page={currentPage.current} onPageChange={setPage} noun="پلن" />
                </>}
              </Surface>
            </Stack>
          </TabPanel>
          {account.data?.role === "OWNER" && <TabPanel p={0} id="access-groups"><AccessGroupManager /></TabPanel>}
        </TabPanels>
      </Tabs>

      <Modal isOpen={categoryModal.isOpen} onClose={categoryModal.onClose} size="xl" scrollBehavior="inside" closeOnOverlayClick={!createCategory.isLoading && !updateCategory.isLoading && !archiveCategory.isLoading}>
        <ModalOverlay /><ModalContent mx={3} my={3} maxH="calc(100dvh - 24px)"><ModalHeader ps={14}>دسته‌بندی پلن‌ها</ModalHeader><ModalCloseButton />
          <ModalBody><Stack spacing={4}>
            <Text fontSize="sm" color="var(--panel-text-muted)">دسته‌ها برای مرتب‌کردن پلن‌ها هستند. دسته‌بندی هر پلن در فرم همان پلن انتخاب می‌شود.</Text>
            <Stack direction={{ base: "column", sm: "row" }} align={{ sm: "end" }} spacing={2}>
              <FormControl><FormLabel fontSize="sm">نام دسته‌بندی جدید</FormLabel><Input value={newCategoryName} placeholder="مثلاً: سازمانی" onChange={(event) => setNewCategoryName(event.target.value)} maxLength={128} /></FormControl>
              <Button colorScheme="primary" flexShrink={0} isDisabled={!newCategoryName.trim()} isLoading={createCategory.isLoading} onClick={() => createCategory.mutate()}>افزودن دسته</Button>
            </Stack>
            {(categories.data || []).map(category => <Box key={category.id} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
              <Flex gap={3} justify="space-between" align="center" flexWrap="wrap">
                <Box minW={0} flex="1">{editingCategoryId === category.id ? <Input aria-label="نام جدید دسته‌بندی" value={editingCategoryName} maxLength={128} onChange={(event) => setEditingCategoryName(event.target.value)} /> : <Text fontWeight="600" overflowWrap="anywhere">{category.name}</Text>}<Text mt={1} fontSize="xs" color="var(--panel-text-muted)">{category.plan_count.toLocaleString("fa-IR")} پلن</Text></Box>
                <HStack spacing={1} flexWrap="wrap">{editingCategoryId === category.id ? <><Button size="sm" colorScheme="primary" isDisabled={!editingCategoryName.trim()} isLoading={updateCategory.isLoading} onClick={() => updateCategory.mutate({ category, name: editingCategoryName })}>ذخیره</Button><Button size="sm" variant="ghost" onClick={() => setEditingCategoryId(null)}>انصراف</Button></> : <Button size="sm" variant="ghost" onClick={() => { setEditingCategoryId(category.id); setEditingCategoryName(category.name); }}>ویرایش</Button>}
                  <Button size="sm" variant="ghost" colorScheme="red" isLoading={archiveCategory.isLoading} onClick={() => category.plan_count > 0 ? toast({ title: "این دسته‌بندی پلن فعال دارد", description: "ابتدا پلن‌های فعال را منتقل یا بایگانی کنید.", status: "warning", duration: 5000 }) : archiveCategory.mutate(category)}>بایگانی</Button>
                </HStack>
              </Flex>
            </Box>)}
            {!categories.isLoading && !categories.data?.length && <EmptyState text="هنوز دسته‌بندی ساخته نشده است" description="نام نخستین دسته را در همین پنجره وارد کنید." />}
          </Stack></ModalBody><ModalFooter><Button variant="outline" onClick={categoryModal.onClose}>بستن</Button></ModalFooter>
        </ModalContent>
      </Modal>
      <Modal isOpen={quickCreate.isOpen} onClose={quickCreate.onClose} size="md" scrollBehavior="inside" closeOnOverlayClick={!createUser.isLoading} closeOnEsc={!createUser.isLoading}>{creationPlan && renderQuickCreate(creationPlan)}</Modal>
      <Modal isOpen={Boolean(detailsPlan)} onClose={() => setDetailsPlan(null)} size="md" scrollBehavior="inside"><ModalOverlay /><ModalContent mx={3} my={3} maxH="calc(100dvh - 24px)"><ModalHeader ps={14}>جزئیات پلن</ModalHeader><ModalCloseButton /><ModalBody>{detailsPlan && <Stack spacing={4}><Text fontSize="lg" fontWeight="700">{detailsPlan.name}</Text><Text fontSize="sm" whiteSpace="pre-wrap">{detailsPlan.description || "توضیحی ثبت نشده است."}</Text><SimpleGrid columns={2} gap={4}>{[
        ["دسته‌بندی", detailsPlan.category_name || "بدون دسته"], ["نسخه", `v${detailsPlan.version_number.toLocaleString("fa-IR")}`], ["حجم", formatBytes(detailsPlan.version.data_limit)], ["مدت", `${detailsPlan.version.duration_days.toLocaleString("fa-IR")} روز`], ["دستگاه", detailsPlan.version.concurrent_user_limit === null ? "نامحدود" : detailsPlan.version.concurrent_user_limit.toLocaleString("fa-IR")], ["ریست حجم", resetLabels[detailsPlan.version.reset_strategy]], ["قیمت", `${(detailsPlan.is_trial ? 0 : detailsPlan.effective_price_toman).toLocaleString("fa-IR")} تومان`], ["نوع پلن", detailsPlan.is_trial ? "تست رایگان" : "اشتراک"],
      ].map(([label, value]) => <Box key={String(label)} minW={0}><Text fontSize="xs" color="var(--panel-text-muted)">{label}</Text><Text fontSize="sm" mt={1} overflowWrap="anywhere">{value}</Text></Box>)}</SimpleGrid></Stack>}</ModalBody><ModalFooter><Button variant="outline" onClick={() => setDetailsPlan(null)}>بستن</Button></ModalFooter></ModalContent></Modal>

      <Modal isOpen={modal.isOpen} onClose={modal.onClose} size="2xl" scrollBehavior="inside" closeOnOverlayClick={!save.isLoading} closeOnEsc={!save.isLoading}>
        <ModalOverlay bg="var(--panel-overlay)" backdropFilter="blur(6px)" />
        <ModalContent as="form" onSubmit={submit} mx={3} my={3} maxH="calc(100dvh - 24px)" overflow="hidden" bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius={{ base: "18px", md: "22px" }} boxShadow="var(--shadow-elevated)">
          <ModalHeader ps={14} py={5} borderBottomWidth="1px" borderColor="var(--panel-border)"><HStack spacing={3}><Box display="grid" placeItems="center" w="38px" h="38px" borderRadius="12px" bg="var(--panel-accent-soft)" borderWidth="1px" borderColor="var(--panel-accent-border)"><Icon as={editing ? PencilSquareIcon : PlusIcon} boxSize="18px" color="var(--panel-accent)" /></Box><Box><Text fontSize="lg" fontWeight="700">{editing ? "ویرایش پلن" : "پلن جدید"}</Text><Text color="var(--panel-text-muted)" fontSize="xs" mt={1}>{editing ? "تغییرات به‌صورت نسخه جدید ذخیره می‌شوند." : "مشخصات پلن اشتراک جدید را تکمیل کنید."}</Text></Box></HStack></ModalHeader>
          <ModalCloseButton isDisabled={save.isLoading} top={4} insetInlineStart={3} insetInlineEnd="auto" />
          <ModalBody overflowY="auto" py={5}><Stack spacing={5}>
            {save.isError && <Alert status="error" role="alert"><AlertIcon />{errorText(save.error)}</Alert>}
            <Box p={{ base: 4, md: 5 }} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"><Stack spacing={4}>
              <FormControl isRequired><FormLabel>نام پلن</FormLabel><Input minH="46px" value={draft.name} isReadOnly={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>توضیح</FormLabel><Textarea minH="100px" resize="vertical" value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
              <FormControl isRequired><FormLabel>دسته‌بندی</FormLabel><Select minH="46px" value={draft.categoryId} onChange={(event) => setDraft((current) => ({ ...current, categoryId: event.target.value }))}><option value="">انتخاب دسته‌بندی</option>{(categories.data || []).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</Select></FormControl>
              {account.data?.role === "OWNER" && <FormControl p={3.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" bg="var(--panel-surface)"><Checkbox minH="44px" alignItems="center" isChecked={draft.isTrial} isDisabled={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, isTrial: event.target.checked }))}>پلن آزمایشی</Checkbox><FormHelperText mt={1}>مشخصات آزمایشی پس از ساخت تغییر نمی‌کند و هر ساخت موفق یک سهمیه تست مصرف می‌کند.</FormHelperText></FormControl>}
            </Stack></Box>
            <Box p={{ base: 4, md: 5 }} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"><HStack spacing={2} mb={4}><Icon as={CircleStackIcon} boxSize="17px" color="var(--panel-accent)" /><Text fontWeight="700">مشخصات نسخه</Text></HStack><SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
              <FormControl isRequired><FormLabel>حجم (GiB)</FormLabel><Input minH="46px" type="number" min={0} step={0.01} dir="ltr" value={draft.dataGiB} onChange={(event) => setDraft((current) => ({ ...current, dataGiB: event.target.value }))} /></FormControl>
              <FormControl isRequired={!draft.isTrial}><FormLabel>قیمت پلن (تومان)</FormLabel><Input minH="46px" type="number" min={0} step={1000} dir="ltr" value={draft.isTrial ? "0" : draft.priceToman} isDisabled={draft.isTrial} onChange={(event) => setDraft((current) => ({ ...current, priceToman: event.target.value }))} /></FormControl>
              <FormControl isRequired><FormLabel>مدت (روز)</FormLabel><Input minH="46px" type="number" min={1} max={3650} dir="ltr" value={draft.durationDays} onChange={(event) => setDraft((current) => ({ ...current, durationDays: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>تعداد دستگاه</FormLabel><Input minH="46px" type="number" min={1} dir="ltr" value={draft.deviceLimit} placeholder="نامحدود" onChange={(event) => setDraft((current) => ({ ...current, deviceLimit: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>ریست حجم</FormLabel><Select minH="46px" value={draft.resetStrategy} onChange={(event) => setDraft((current) => ({ ...current, resetStrategy: event.target.value as PlanDraft["resetStrategy"] }))}><option value="no_reset">بدون ریست</option><option value="day">روزانه</option><option value="week">هفتگی</option><option value="month">ماهانه</option><option value="year">سالانه</option></Select></FormControl>
            </SimpleGrid></Box>
            <Alert status="info" variant="left-accent" borderRadius="14px" bg="var(--panel-accent-soft)" borderColor="var(--panel-accent-border)"><AlertIcon color="var(--panel-accent)" />این پلن فقط حجم، مدت، قیمت و محدودیت دستگاه را نسخه‌بندی می‌کند. شبکه از Access Group کاربر می‌آید.</Alert>
          </Stack></ModalBody>
          <ModalFooter flexShrink={0} gap={2} px={{ base: 3, md: 6 }} py={4} borderTopWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-bg)"><Button minH="44px" variant="ghost" onClick={modal.onClose} isDisabled={save.isLoading}>انصراف</Button><Button minH="44px" type="submit" bg="var(--panel-accent)" color="var(--panel-accent-contrast)" isLoading={save.isLoading} _hover={{ filter: "brightness(1.05)" }}>ذخیره</Button></ModalFooter>
        </ModalContent>
      </Modal>

      <AlertDialog isOpen={archiveDialog.isOpen} leastDestructiveRef={cancelRef} onClose={archiveDialog.onClose}><AlertDialogOverlay bg="rgba(0,0,0,.75)" backdropFilter="blur(5px)"><AlertDialogContent bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="18px" mx={3}><AlertDialogHeader>بایگانی پلن</AlertDialogHeader><AlertDialogBody color="var(--panel-text-body)">پلن «{archiveTarget?.name}» برای ساخت و تمدید جدید غیرفعال می‌شود.</AlertDialogBody><AlertDialogFooter gap={3} borderTopWidth="1px" borderColor="var(--panel-border)" mt={4} pt={4}><Button ref={cancelRef} onClick={archiveDialog.onClose}>انصراف</Button><Button colorScheme="red" isLoading={archive.isLoading} onClick={() => archiveTarget && archive.mutate(archiveTarget)} leftIcon={<Icon as={ArchiveBoxIcon} boxSize="16px" />}>بایگانی</Button></AlertDialogFooter></AlertDialogContent></AlertDialogOverlay></AlertDialog>
    </AppShell>
  );
};

export default Plans;
