import {
  Alert,
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
  Card,
  Checkbox,
  FormControl,
  FormHelperText,
  FormLabel,
  HStack,
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
import { AccessGroupManager } from "components/AccessGroupManager";
import { AppShell } from "components/AppShell";
import useGetUser from "hooks/useGetUser";
import { FC, FormEvent, useEffect, useRef, useState } from "react";
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

const errorText = localizedApiError;

export const Plans: FC = () => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { getUserIsPending } = useGetUser();
  const modal = useDisclosure();
  const archiveDialog = useDisclosure();
  const cancelRef = useRef<HTMLButtonElement>(null);
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
        allowed_admin_ids: [],
        include_subtree: false,
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

  const openCreate = () => { setEditing(null); modal.onOpen(); };
  const openEdit = (plan: UserPlan) => { setEditing(plan); modal.onOpen(); };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.categoryId) {
      toast({ title: "دسته‌بندی پلن را انتخاب کنید", status: "warning", duration: 3000 });
      return;
    }
    save.mutate();
  };

  return (
    <AppShell>
      <Stack direction={{ base: "column", md: "row" }} justify="space-between" align={{ md: "end" }} gap={4} mb={6}>
        <Box><Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">اشتراک استاندارد</Text><Text as="h1" fontSize={{ base: "2xl", md: "3xl" }} fontWeight="800" mt={1}>پلن‌های کاربر</Text><Text color="var(--panel-text-body)" mt={1}>نسخه‌های تغییرناپذیر، دسترسی شاخه‌ای و ساخت کاربر بدون ورود دستی محدودیت‌ها.</Text></Box>
        {canManage && <Button minH="44px" colorScheme="primary" color="var(--panel-accent-contrast)" onClick={openCreate} isDisabled={(categories.data || []).length === 0}>پلن جدید</Button>}
      </Stack>
      {canManage && (
        <Card p={5} mb={5} bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px">
          <Text fontWeight="800">دسته‌بندی پلن‌ها</Text>
          <Text color="var(--panel-text-muted)" fontSize="sm" mt={1}>پلن و قیمت آن را همین‌جا تنظیم کنید؛ مدیرهای پلنی از فهرست فعال استفاده می‌کنند.</Text>
          <HStack mt={4} align="end" flexWrap="wrap">
            <FormControl maxW={{ base: "full", md: "360px" }}>
              <FormLabel fontSize="sm">نام دسته‌بندی جدید</FormLabel>
              <Input value={newCategoryName} onChange={(event) => setNewCategoryName(event.target.value)} maxLength={128} />
            </FormControl>
            <Button minH="40px" isDisabled={!newCategoryName.trim()} isLoading={createCategory.isLoading} onClick={() => createCategory.mutate()}>افزودن دسته</Button>
          </HStack>
          <Stack mt={4} spacing={2}>
            {(categories.data || []).map((category) => (
              <HStack key={category.id} p={2} borderWidth="1px" borderColor="whiteAlpha.200" borderRadius="md" flexWrap="wrap">
                {editingCategoryId === category.id ? (
                  <Input flex="1" minW="180px" value={editingCategoryName} maxLength={128} onChange={(event) => setEditingCategoryName(event.target.value)} />
                ) : (
                  <Badge variant="outline" color="var(--panel-accent)" borderColor="var(--panel-accent-border)" bg="var(--panel-accent-soft)" px={3} py={1.5}>{category.name} · {category.plan_count}</Badge>
                )}
                <HStack ms="auto" spacing={1}>
                  {editingCategoryId === category.id ? (
                    <>
                      <Button size="xs" isDisabled={!editingCategoryName.trim()} isLoading={updateCategory.isLoading} onClick={() => updateCategory.mutate({ category, name: editingCategoryName })}>ذخیره</Button>
                      <Button size="xs" variant="ghost" onClick={() => setEditingCategoryId(null)}>انصراف</Button>
                    </>
                  ) : (
                    <Button size="xs" variant="ghost" onClick={() => { setEditingCategoryId(category.id); setEditingCategoryName(category.name); }}>ویرایش</Button>
                  )}
                  <Button
                    size="xs"
                    variant="ghost"
                    colorScheme="red"
                    isLoading={archiveCategory.isLoading}
                    onClick={() => category.plan_count > 0
                      ? toast({ title: "این دسته‌بندی پلن فعال دارد", description: "ابتدا پلن‌های فعال را منتقل یا بایگانی کنید.", status: "warning", duration: 5000 })
                      : archiveCategory.mutate(category)}
                  >بایگانی</Button>
                </HStack>
              </HStack>
            ))}
            {!categories.isLoading && (categories.data || []).length === 0 && <Text color="var(--panel-text-muted)" fontSize="sm">ابتدا یک دسته‌بندی بسازید.</Text>}
          </Stack>
        </Card>
      )}
      {categories.isError && <Alert status="error" mb={4}><AlertIcon />دسته‌بندی‌ها دریافت نشدند.</Alert>}
      {plans.isError && <Alert status="error" mb={4}><AlertIcon />پلن‌ها دریافت نشدند.</Alert>}
      {plans.isLoading ? <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4}>{[1, 2, 3].map((value) => <Skeleton key={value} h="245px" borderRadius="18px" />)}</SimpleGrid> : (
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={4}>
          {(plans.data || []).map((plan) => (
            <Card key={plan.id} p={4} bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" boxShadow="panel">
              <HStack justify="space-between" align="start"><Box minW={0}><Text as="h2" fontSize="lg" fontWeight="800" overflowWrap="anywhere">{plan.name}</Text><Text color="var(--panel-text-muted)" fontSize="sm" mt={1}>{plan.description || "بدون توضیح"}</Text></Box><Stack align="end" spacing={1}>{plan.is_trial && <Badge colorScheme="orange">آزمایشی</Badge>}<Badge variant="outline" color="var(--panel-accent)" borderColor="var(--panel-accent-border)" bg="var(--panel-accent-soft)">نسخه {plan.version_number}</Badge><Badge variant="outline" color="var(--panel-text-body)" borderColor="var(--panel-border)" bg="var(--panel-muted-soft)">{plan.category_name || "بدون دسته"}</Badge></Stack></HStack>
              <SimpleGrid columns={2} gap={3} mt={5}><Box><Text color="var(--panel-text-muted)" fontSize="xs">حجم</Text><Text mt={1} fontWeight="700">{formatBytes(plan.version.data_limit)}</Text></Box><Box><Text color="var(--panel-text-muted)" fontSize="xs">مدت</Text><Text mt={1} fontWeight="700">{plan.version.duration_days} روز</Text></Box><Box><Text color="var(--panel-text-muted)" fontSize="xs">قیمت پلن</Text><Text mt={1} fontWeight="700">{plan.effective_price_toman.toLocaleString("fa-IR")} تومان</Text></Box><Box><Text color="var(--panel-text-muted)" fontSize="xs">دستگاه</Text><Text mt={1}>{plan.version.concurrent_user_limit ?? "نامحدود"}</Text></Box><Box><Text color="var(--panel-text-muted)" fontSize="xs">دسته‌بندی</Text><Text mt={1}>{plan.category_name || "بدون دسته"}</Text></Box></SimpleGrid>
              {accountActive && <Stack mt={5} spacing={2}><FormControl><FormLabel fontSize="xs">Access Group</FormLabel><Select minH="44px" value={accessGroupIds[plan.id] || ""} isDisabled={accessGroups.isLoading || accessGroups.isError} onChange={(event) => setAccessGroupIds((current) => ({ ...current, [plan.id]: event.target.value }))}><option value="">انتخاب دسترسی شبکه</option>{(accessGroups.data || []).map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</Select></FormControl><FormControl><FormLabel fontSize="xs">نام کاربری جدید</FormLabel><HStack><Input minH="44px" dir="ltr" value={usernames[plan.id] || ""} onChange={(event) => setUsernames((current) => ({ ...current, [plan.id]: event.target.value }))} /><Button minH="44px" isDisabled={!usernames[plan.id]?.trim() || !accessGroupIds[plan.id]} isLoading={createUser.isLoading} onClick={() => createUser.mutate({ plan, username: usernames[plan.id].trim(), accessGroupId: Number(accessGroupIds[plan.id]) })}>ساخت</Button></HStack></FormControl></Stack>}
              {canManage && <HStack mt={4}><Button minH="44px" size="sm" variant="outline" onClick={() => openEdit(plan)}>نسخه جدید</Button><Button minH="44px" size="sm" variant="ghost" colorScheme="red" onClick={() => { setArchiveTarget(plan); archiveDialog.onOpen(); }}>بایگانی</Button></HStack>}
            </Card>
          ))}
        </SimpleGrid>
      )}
      {account.data?.role === "OWNER" && (
        <Card mt={6} p={{ base: 4, md: 5 }} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px">
          <Stack spacing={1} mb={5}>
            <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">دسترسی شبکه</Text>
            <Text as="h2" fontSize="xl" fontWeight="800">Access Groups</Text>
            <Text color="var(--panel-text-muted)" fontSize="sm">گروه دسترسی، Node / Inbound / Host و ادمین‌های مجاز را مشخص می‌کند و از شرایط تجاری پلن مستقل می‌ماند.</Text>
          </Stack>
          <AccessGroupManager />
        </Card>
      )}

      {!plans.isLoading && !plans.isError && (plans.data || []).length === 0 && <Card p={8} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" textAlign="center"><Text fontWeight="700">پلنی در دسترس نیست.</Text><Text color="var(--panel-text-muted)" mt={2}>Owner یا مدیر مجاز باید نخستین پلن را بسازد.</Text></Card>}

      <Modal isOpen={modal.isOpen} onClose={modal.onClose} size="2xl" scrollBehavior="inside"><ModalOverlay bg="rgba(0,0,0,.72)" /><ModalContent as="form" onSubmit={submit} mx={3} my={3} maxH="calc(100dvh - 24px)" overflow="hidden" bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border-strong)"><ModalHeader ps={14}>{editing ? "ساخت نسخه جدید" : "پلن جدید"}</ModalHeader><ModalCloseButton top={3} insetInlineStart={3} insetInlineEnd="auto" /><ModalBody overflowY="auto"><Stack spacing={4}>
        <FormControl isRequired><FormLabel>نام پلن</FormLabel><Input minH="44px" value={draft.name} isReadOnly={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
        <FormControl><FormLabel>توضیح</FormLabel><Textarea value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
        <FormControl isRequired><FormLabel>دسته‌بندی</FormLabel><Select value={draft.categoryId} onChange={(event) => setDraft((current) => ({ ...current, categoryId: event.target.value }))}><option value="">انتخاب دسته‌بندی</option>{(categories.data || []).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</Select></FormControl>
        {account.data?.role === "OWNER" && <FormControl><Checkbox minH="44px" alignItems="center" isChecked={draft.isTrial} isDisabled={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, isTrial: event.target.checked }))}>پلن آزمایشی</Checkbox><FormHelperText>مشخصات آزمایشی پس از ساخت تغییر نمی‌کند و هر ساخت موفق یک سهمیه تست مصرف می‌کند.</FormHelperText></FormControl>}
        <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}><FormControl isRequired><FormLabel>حجم (GiB)</FormLabel><Input minH="44px" type="number" min={0} step={0.01} dir="ltr" value={draft.dataGiB} onChange={(event) => setDraft((current) => ({ ...current, dataGiB: event.target.value }))} /></FormControl><FormControl isRequired={!draft.isTrial}><FormLabel>قیمت پلن (تومان)</FormLabel><Input minH="44px" type="number" min={0} step={1000} dir="ltr" value={draft.isTrial ? "0" : draft.priceToman} isDisabled={draft.isTrial} onChange={(event) => setDraft((current) => ({ ...current, priceToman: event.target.value }))} /></FormControl><FormControl isRequired><FormLabel>مدت (روز)</FormLabel><Input minH="44px" type="number" min={1} max={3650} dir="ltr" value={draft.durationDays} onChange={(event) => setDraft((current) => ({ ...current, durationDays: event.target.value }))} /></FormControl><FormControl><FormLabel>تعداد دستگاه</FormLabel><Input minH="44px" type="number" min={1} dir="ltr" value={draft.deviceLimit} onChange={(event) => setDraft((current) => ({ ...current, deviceLimit: event.target.value }))} /></FormControl><FormControl><FormLabel>ریست حجم</FormLabel><Select minH="44px" value={draft.resetStrategy} onChange={(event) => setDraft((current) => ({ ...current, resetStrategy: event.target.value as PlanDraft["resetStrategy"] }))}><option value="no_reset">بدون ریست</option><option value="day">روزانه</option><option value="week">هفتگی</option><option value="month">ماهانه</option><option value="year">سالانه</option></Select></FormControl></SimpleGrid>
        <Alert status="info" variant="left-accent"><AlertIcon />این پلن فقط حجم، مدت، قیمت و محدودیت دستگاه را نسخه‌بندی می‌کند. شبکه از Access Group کاربر می‌آید.</Alert>
      </Stack></ModalBody><ModalFooter flexShrink={0} gap={2} px={{ base: 3, md: 6 }} py={3} borderTopWidth="1px" borderColor="var(--panel-border)"><Button minH="42px" variant="ghost" onClick={modal.onClose}>انصراف</Button><Button minH="42px" type="submit" colorScheme="primary" color="var(--panel-accent-contrast)" isLoading={save.isLoading}>ذخیره</Button></ModalFooter></ModalContent></Modal>

      <AlertDialog isOpen={archiveDialog.isOpen} leastDestructiveRef={cancelRef} onClose={archiveDialog.onClose}><AlertDialogOverlay><AlertDialogContent bg="var(--panel-surface)" color="var(--panel-text)"><AlertDialogHeader>بایگانی پلن</AlertDialogHeader><AlertDialogBody>پلن «{archiveTarget?.name}» برای ساخت و تمدید جدید غیرفعال می‌شود.</AlertDialogBody><AlertDialogFooter gap={3}><Button ref={cancelRef} onClick={archiveDialog.onClose}>انصراف</Button><Button colorScheme="red" isLoading={archive.isLoading} onClick={() => archiveTarget && archive.mutate(archiveTarget)}>بایگانی</Button></AlertDialogFooter></AlertDialogContent></AlertDialogOverlay></AlertDialog>
    </AppShell>
  );
};

export default Plans;
