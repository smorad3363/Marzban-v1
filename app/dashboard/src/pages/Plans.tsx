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
  ArchiveBoxIcon,
  BoltIcon,
  CalendarDaysIcon,
  CircleStackIcon,
  CpuChipIcon,
  CubeTransparentIcon,
  PencilSquareIcon,
  PlusIcon,
  RocketLaunchIcon,
  SparklesIcon,
  Squares2X2Icon,
  UserPlusIcon,
} from "@heroicons/react/24/outline";
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

type Accent = {
  color: string;
  soft: string;
  border: string;
  glow: string;
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

const categoryAccents: Accent[] = [
  { color: "#72e6a7", soft: "rgba(54, 211, 153, .08)", border: "rgba(72, 224, 161, .22)", glow: "rgba(54, 211, 153, .16)" },
  { color: "#7cc8ff", soft: "rgba(73, 163, 255, .08)", border: "rgba(91, 177, 255, .22)", glow: "rgba(73, 163, 255, .14)" },
  { color: "#e8bd68", soft: "rgba(232, 189, 104, .08)", border: "rgba(232, 189, 104, .24)", glow: "rgba(232, 189, 104, .17)" },
  { color: "#c7a2ff", soft: "rgba(170, 117, 255, .08)", border: "rgba(190, 145, 255, .22)", glow: "rgba(170, 117, 255, .14)" },
];

const trialAccent: Accent = {
  color: "#ff8aa8",
  soft: "rgba(255, 92, 135, .08)",
  border: "rgba(255, 112, 150, .22)",
  glow: "rgba(255, 92, 135, .16)",
};

const resetLabels: Record<PlanDraft["resetStrategy"], string> = {
  no_reset: "بدون ریست",
  day: "روزانه",
  week: "هفتگی",
  month: "ماهانه",
  year: "سالانه",
};

const getCategoryAccent = (index: number) => categoryAccents[index % categoryAccents.length];

const getPlanAccent = (plan: UserPlan, index: number) => {
  if (plan.is_trial) return trialAccent;
  return categoryAccents[(plan.category_id ?? index) % categoryAccents.length];
};

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
      <Stack spacing={{ base: 5, md: 7 }}>
        <Stack
          direction={{ base: "column", md: "row" }}
          justify="space-between"
          align={{ md: "end" }}
          gap={5}
          p={{ base: 5, md: 6 }}
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius={{ base: "18px", md: "22px" }}
          bg="linear-gradient(135deg, var(--panel-surface) 0%, var(--panel-bg) 100%)"
          boxShadow="0 20px 48px rgba(0,0,0,.18)"
          position="relative"
          overflow="hidden"
        >
          <Box position="absolute" insetInlineEnd="-70px" top="-110px" w="240px" h="240px" borderRadius="full" bg="var(--panel-accent-soft)" filter="blur(10px)" pointerEvents="none" />
          <Box position="relative" maxW="760px">
            <HStack spacing={2} mb={3}>
              <Box w="8px" h="8px" borderRadius="full" bg="var(--panel-accent)" boxShadow="0 0 18px var(--panel-accent)" />
              <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800" letterSpacing=".02em">مدیریت اشتراک</Text>
            </HStack>
            <Text as="h1" fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900" color="var(--panel-text)">پلن‌های کاربر</Text>
            <Text color="var(--panel-text-body)" mt={2} lineHeight="1.9">مدیریت و ایجاد پلن‌های اشتراک، دسته‌بندی‌ها و امکانات کاربران</Text>
          </Box>
          <HStack spacing={2.5} flexWrap="wrap" position="relative">
            {account.data?.role === "OWNER" && <Button as="a" href="#access-groups" minH="46px" px={5} variant="outline" borderColor="var(--panel-border)" color="var(--panel-text)" bg="rgba(255,255,255,.015)" _hover={{ borderColor: "var(--panel-accent-border)", bg: "var(--panel-accent-soft)", color: "var(--panel-accent)" }}>گروه‌های دسترسی</Button>}
            {canManage && <Button minH="46px" px={5} bg="var(--panel-accent)" color="var(--panel-accent-contrast)" leftIcon={<Icon as={PlusIcon} boxSize="18px" />} onClick={openCreate} isDisabled={(categories.data || []).length === 0} _hover={{ transform: "translateY(-1px)", filter: "brightness(1.05)", boxShadow: "0 12px 30px var(--panel-accent-soft)" }} _active={{ transform: "translateY(0)" }}>پلن جدید</Button>}
          </HStack>
        </Stack>

        {canManage && (
          <Card p={{ base: 4, md: 6 }} bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius={{ base: "18px", md: "22px" }} boxShadow="0 18px 46px rgba(0,0,0,.16)">
            <Stack spacing={5}>
              <HStack align="start" spacing={3}>
                <Box display="grid" placeItems="center" w="44px" h="44px" borderRadius="14px" bg="var(--panel-accent-soft)" borderWidth="1px" borderColor="var(--panel-accent-border)" flexShrink={0}><Icon as={Squares2X2Icon} boxSize="21px" color="var(--panel-accent)" /></Box>
                <Box><Text fontWeight="900" fontSize={{ base: "lg", md: "xl" }}>دسته‌بندی پلن‌ها</Text><Text color="var(--panel-text-muted)" fontSize="sm" mt={1} lineHeight="1.9">با دسته‌بندی مناسب، مدیریت پلن‌ها را ساده‌تر کنید. هر پلن را در یک دسته قرار دهید.</Text></Box>
              </HStack>
              <Stack direction={{ base: "column", lg: "row" }} align={{ lg: "end" }} gap={3} p={{ base: 4, md: 5 }} borderRadius="16px" borderWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-bg)">
                <FormControl maxW={{ lg: "430px" }}><FormLabel fontSize="sm" fontWeight="700">نام دسته‌بندی جدید</FormLabel><Input minH="46px" value={newCategoryName} placeholder="مثلاً: سازمانی" onChange={(event) => setNewCategoryName(event.target.value)} maxLength={128} borderColor="var(--panel-border)" bg="var(--panel-surface)" _hover={{ borderColor: "var(--panel-accent-border)" }} _focusVisible={{ borderColor: "var(--panel-accent)", boxShadow: "0 0 0 1px var(--panel-accent)" }} /></FormControl>
                <Button minH="46px" px={5} bg="var(--panel-accent)" color="var(--panel-accent-contrast)" leftIcon={<Icon as={PlusIcon} boxSize="17px" />} isDisabled={!newCategoryName.trim()} isLoading={createCategory.isLoading} onClick={() => createCategory.mutate()} _hover={{ filter: "brightness(1.05)" }}>افزودن دسته</Button>
              </Stack>
              <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap={3}>
                {(categories.data || []).map((category, index) => {
                  const accent = getCategoryAccent(index);
                  const isEditingCategory = editingCategoryId === category.id;
                  return (
                    <Box key={category.id} p={4} minH="150px" borderRadius="16px" borderWidth="1px" borderColor={accent.border} bg={`linear-gradient(145deg, ${accent.soft} 0%, var(--panel-bg) 72%)`} transition="transform .2s ease, border-color .2s ease, box-shadow .2s ease" _hover={{ transform: "translateY(-2px)", boxShadow: `0 14px 30px ${accent.glow}` }}>
                      <Stack h="full" spacing={3}>
                        <HStack justify="space-between" align="start"><Box display="grid" placeItems="center" w="36px" h="36px" borderRadius="12px" bg={accent.soft} borderWidth="1px" borderColor={accent.border}><Icon as={CubeTransparentIcon} boxSize="18px" color={accent.color} /></Box><Badge px={2.5} py={1} borderRadius="full" bg={accent.soft} color={accent.color} borderWidth="1px" borderColor={accent.border}>{category.plan_count.toLocaleString("fa-IR")} پلن</Badge></HStack>
                        {isEditingCategory ? <Input value={editingCategoryName} maxLength={128} minH="42px" bg="var(--panel-surface)" borderColor={accent.border} onChange={(event) => setEditingCategoryName(event.target.value)} /> : <Text fontWeight="800" fontSize="md" noOfLines={2}>{category.name}</Text>}
                        <HStack mt="auto" spacing={2} flexWrap="wrap">
                          {isEditingCategory ? <><Button size="sm" variant="outline" borderColor={accent.border} color={accent.color} isDisabled={!editingCategoryName.trim()} isLoading={updateCategory.isLoading} onClick={() => updateCategory.mutate({ category, name: editingCategoryName })}>ذخیره</Button><Button size="sm" variant="ghost" onClick={() => setEditingCategoryId(null)}>انصراف</Button></> : <Button size="sm" variant="ghost" leftIcon={<Icon as={PencilSquareIcon} boxSize="15px" />} onClick={() => { setEditingCategoryId(category.id); setEditingCategoryName(category.name); }}>ویرایش</Button>}
                          <Button size="sm" variant="ghost" colorScheme="red" leftIcon={<Icon as={ArchiveBoxIcon} boxSize="15px" />} isLoading={archiveCategory.isLoading} onClick={() => category.plan_count > 0 ? toast({ title: "این دسته‌بندی پلن فعال دارد", description: "ابتدا پلن‌های فعال را منتقل یا بایگانی کنید.", status: "warning", duration: 5000 }) : archiveCategory.mutate(category)}>بایگانی</Button>
                        </HStack>
                      </Stack>
                    </Box>
                  );
                })}
              </SimpleGrid>
              {!categories.isLoading && (categories.data || []).length === 0 && <Box py={8} textAlign="center" borderWidth="1px" borderStyle="dashed" borderColor="var(--panel-border)" borderRadius="16px"><Text color="var(--panel-text-muted)" fontSize="sm">ابتدا یک دسته‌بندی بسازید.</Text></Box>}
            </Stack>
          </Card>
        )}

        {categories.isError && <Alert status="error" borderRadius="14px"><AlertIcon />دسته‌بندی‌ها دریافت نشدند.</Alert>}
        {plans.isError && <Alert status="error" borderRadius="14px"><AlertIcon />پلن‌ها دریافت نشدند.</Alert>}

        {plans.isLoading ? (
          <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={5}>{[1, 2, 3].map((value) => <Skeleton key={value} h="620px" borderRadius="22px" />)}</SimpleGrid>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap={5} alignItems="stretch">
            {(plans.data || []).map((plan, index) => {
              const accent = getPlanAccent(plan, index);
              const planPrice = plan.is_trial ? 0 : plan.effective_price_toman;
              return (
                <Card key={plan.id} p={0} overflow="hidden" bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius={{ base: "18px", md: "22px" }} boxShadow="0 18px 44px rgba(0,0,0,.18)" transition="transform .22s ease, border-color .22s ease, box-shadow .22s ease" _hover={{ transform: "translateY(-4px)", borderColor: accent.border, boxShadow: `0 24px 56px rgba(0,0,0,.28), 0 0 0 1px ${accent.soft}` }}>
                  <Box h="3px" bg={`linear-gradient(90deg, ${accent.color}, transparent)`} />
                  <Stack p={{ base: 4, md: 5 }} spacing={5} h="full">
                    <HStack justify="space-between" align="start" spacing={3}>
                      <HStack align="start" spacing={3} minW={0}><Box display="grid" placeItems="center" w="44px" h="44px" borderRadius="14px" bg={accent.soft} borderWidth="1px" borderColor={accent.border} flexShrink={0}><Icon as={plan.is_trial ? SparklesIcon : RocketLaunchIcon} boxSize="21px" color={accent.color} /></Box><Box minW={0}><Text as="h2" fontSize="lg" fontWeight="900" overflowWrap="anywhere" noOfLines={2}>{plan.name}</Text><HStack mt={2} spacing={1.5} flexWrap="wrap"><Badge variant="outline" borderColor={accent.border} color={accent.color} bg={accent.soft} borderRadius="full" px={2.5} py={1}>{plan.category_name || "بدون دسته"}</Badge>{plan.is_trial && <Badge color="#ff9bb4" bg="rgba(255, 92, 135, .10)" borderWidth="1px" borderColor="rgba(255, 112, 150, .24)" borderRadius="full" px={2.5} py={1}>تست رایگان</Badge>}</HStack></Box></HStack>
                      <Badge variant="subtle" bg="var(--panel-bg)" color="var(--panel-text-muted)" borderRadius="full" px={2.5} py={1} flexShrink={0}>v{plan.version_number.toLocaleString("fa-IR")}</Badge>
                    </HStack>
                    <Box><Text color="var(--panel-text-muted)" fontSize="xs" fontWeight="700">قیمت پلن</Text><HStack align="baseline" mt={1} spacing={2} flexWrap="wrap"><Text fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900" color={plan.is_trial ? "#ff9bb4" : "var(--panel-accent)"} letterSpacing="-.02em">{planPrice.toLocaleString("fa-IR")}</Text><Text fontSize="sm" color="var(--panel-text-body)" fontWeight="700">تومان</Text></HStack>{plan.description && <Text mt={3} color="var(--panel-text-body)" fontSize="sm" lineHeight="1.9" noOfLines={2} minH={{ md: "53px" }}>{plan.description}</Text>}</Box>
                    <SimpleGrid columns={3} gap={2.5}>
                      <Box p={3} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" minW={0}><Icon as={CircleStackIcon} boxSize="16px" color={accent.color} mb={2} /><Text color="var(--panel-text-muted)" fontSize="xs">حجم</Text><Text mt={1} fontWeight="800" fontSize="sm" noOfLines={1}>{formatBytes(plan.version.data_limit)}</Text></Box>
                      <Box p={3} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" minW={0}><Icon as={CalendarDaysIcon} boxSize="16px" color={accent.color} mb={2} /><Text color="var(--panel-text-muted)" fontSize="xs">مدت</Text><Text mt={1} fontWeight="800" fontSize="sm" noOfLines={1}>{plan.version.duration_days.toLocaleString("fa-IR")} روز</Text></Box>
                      <Box p={3} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" minW={0}><Icon as={CpuChipIcon} boxSize="16px" color={accent.color} mb={2} /><Text color="var(--panel-text-muted)" fontSize="xs">دستگاه</Text><Text mt={1} fontWeight="800" fontSize="sm">{plan.version.concurrent_user_limit === null ? "∞" : plan.version.concurrent_user_limit.toLocaleString("fa-IR")}</Text></Box>
                    </SimpleGrid>
                    <HStack justify="space-between" py={3} px={3.5} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px"><HStack spacing={2}><Icon as={BoltIcon} boxSize="17px" color={accent.color} /><Text color="var(--panel-text-muted)" fontSize="sm">ریست حجم</Text></HStack><Text fontSize="sm" fontWeight="800">{resetLabels[plan.version.reset_strategy]}</Text></HStack>
                    {canManage && <SimpleGrid columns={2} gap={2.5}><Button minH="44px" size="sm" bg="var(--panel-accent)" color="var(--panel-accent-contrast)" leftIcon={<Icon as={PencilSquareIcon} boxSize="16px" />} onClick={() => openEdit(plan)} _hover={{ filter: "brightness(1.05)", transform: "translateY(-1px)" }}>ویرایش پلن</Button><Button minH="44px" size="sm" variant="outline" colorScheme="red" leftIcon={<Icon as={ArchiveBoxIcon} boxSize="16px" />} onClick={() => { setArchiveTarget(plan); archiveDialog.onOpen(); }}>بایگانی</Button></SimpleGrid>}
                    {accountActive && (
                      <Stack mt="auto" pt={5} spacing={3.5} borderTopWidth="1px" borderColor="var(--panel-border)">
                        <HStack spacing={3} align="start"><Box display="grid" placeItems="center" w="36px" h="36px" borderRadius="12px" bg={accent.soft} borderWidth="1px" borderColor={accent.border} flexShrink={0}><Icon as={UserPlusIcon} boxSize="18px" color={accent.color} /></Box><Box><Text fontWeight="800" fontSize="sm">ساخت سریع کاربر</Text><Text color="var(--panel-text-muted)" fontSize="xs" mt={1} lineHeight="1.8">با این پلن یک کاربر جدید سریع ایجاد کنید.</Text></Box></HStack>
                        <FormControl><FormLabel fontSize="xs" color="var(--panel-text-muted)">گروه دسترسی</FormLabel><Select minH="44px" value={accessGroupIds[plan.id] || ""} isDisabled={accessGroups.isLoading || accessGroups.isError} onChange={(event) => setAccessGroupIds((current) => ({ ...current, [plan.id]: event.target.value }))} borderColor="var(--panel-border)" bg="var(--panel-bg)"><option value="">انتخاب دسترسی شبکه</option>{(accessGroups.data || []).map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</Select></FormControl>
                        <FormControl><FormLabel fontSize="xs" color="var(--panel-text-muted)">نام کاربری جدید</FormLabel><Input minH="44px" dir="ltr" value={usernames[plan.id] || ""} placeholder="username" onChange={(event) => setUsernames((current) => ({ ...current, [plan.id]: event.target.value }))} borderColor="var(--panel-border)" bg="var(--panel-bg)" /></FormControl>
                        <Button minH="44px" w="full" bg={accent.soft} color={accent.color} borderWidth="1px" borderColor={accent.border} leftIcon={<Icon as={UserPlusIcon} boxSize="16px" />} isDisabled={!usernames[plan.id]?.trim() || !accessGroupIds[plan.id]} isLoading={createUser.isLoading} onClick={() => createUser.mutate({ plan, username: usernames[plan.id].trim(), accessGroupId: Number(accessGroupIds[plan.id]) })} _hover={{ bg: accent.soft, filter: "brightness(1.12)" }}>ساخت کاربر</Button>
                      </Stack>
                    )}
                  </Stack>
                </Card>
              );
            })}
          </SimpleGrid>
        )}

        {!plans.isLoading && !plans.isError && (plans.data || []).length === 0 && <Card p={10} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="20px" textAlign="center"><Box mx="auto" display="grid" placeItems="center" w="54px" h="54px" borderRadius="16px" bg="var(--panel-accent-soft)" borderWidth="1px" borderColor="var(--panel-accent-border)" mb={4}><Icon as={RocketLaunchIcon} boxSize="24px" color="var(--panel-accent)" /></Box><Text fontWeight="800">پلنی در دسترس نیست.</Text><Text color="var(--panel-text-muted)" mt={2}>مالک پنل یا مدیر مجاز باید نخستین پلن را بسازد.</Text></Card>}

        {account.data?.role === "OWNER" && <Box id="access-groups" pt={3}><Card p={{ base: 4, md: 6 }} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius={{ base: "18px", md: "22px" }}><Stack spacing={1} mb={5}><HStack spacing={2}><Icon as={CubeTransparentIcon} boxSize="17px" color="var(--panel-accent)" /><Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">دسترسی شبکه</Text></HStack><Text as="h2" fontSize="xl" fontWeight="900">گروه‌های دسترسی</Text><Text color="var(--panel-text-muted)" fontSize="sm" lineHeight="1.9">هر گروه مشخص می‌کند یک کاربر از کدام اینباندها، هاست‌ها و نودها استفاده کند و کدام ادمین‌ها اجازه استفاده از آن گروه را داشته باشند. شرایط مالی همچنان در خود پلن مدیریت می‌شود.</Text></Stack><AccessGroupManager /></Card></Box>}
      </Stack>

      <Modal isOpen={modal.isOpen} onClose={modal.onClose} size="2xl" scrollBehavior="inside">
        <ModalOverlay bg="rgba(0,0,0,.78)" backdropFilter="blur(6px)" />
        <ModalContent as="form" onSubmit={submit} mx={3} my={3} maxH="calc(100dvh - 24px)" overflow="hidden" bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius={{ base: "18px", md: "22px" }} boxShadow="0 30px 90px rgba(0,0,0,.5)">
          <ModalHeader ps={14} py={5} borderBottomWidth="1px" borderColor="var(--panel-border)"><HStack spacing={3}><Box display="grid" placeItems="center" w="38px" h="38px" borderRadius="12px" bg="var(--panel-accent-soft)" borderWidth="1px" borderColor="var(--panel-accent-border)"><Icon as={editing ? PencilSquareIcon : PlusIcon} boxSize="18px" color="var(--panel-accent)" /></Box><Box><Text fontSize="lg" fontWeight="900">{editing ? "ویرایش پلن" : "پلن جدید"}</Text><Text color="var(--panel-text-muted)" fontSize="xs" mt={1}>{editing ? "تغییرات به‌صورت نسخه جدید ذخیره می‌شوند." : "مشخصات پلن اشتراک جدید را تکمیل کنید."}</Text></Box></HStack></ModalHeader>
          <ModalCloseButton top={4} insetInlineStart={3} insetInlineEnd="auto" />
          <ModalBody overflowY="auto" py={5}><Stack spacing={5}>
            <Box p={{ base: 4, md: 5 }} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"><Stack spacing={4}>
              <FormControl isRequired><FormLabel>نام پلن</FormLabel><Input minH="46px" value={draft.name} isReadOnly={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>توضیح</FormLabel><Textarea minH="100px" resize="vertical" value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
              <FormControl isRequired><FormLabel>دسته‌بندی</FormLabel><Select minH="46px" value={draft.categoryId} onChange={(event) => setDraft((current) => ({ ...current, categoryId: event.target.value }))}><option value="">انتخاب دسته‌بندی</option>{(categories.data || []).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</Select></FormControl>
              {account.data?.role === "OWNER" && <FormControl p={3.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" bg="var(--panel-surface)"><Checkbox minH="44px" alignItems="center" isChecked={draft.isTrial} isDisabled={Boolean(editing)} onChange={(event) => setDraft((current) => ({ ...current, isTrial: event.target.checked }))}>پلن آزمایشی</Checkbox><FormHelperText mt={1}>مشخصات آزمایشی پس از ساخت تغییر نمی‌کند و هر ساخت موفق یک سهمیه تست مصرف می‌کند.</FormHelperText></FormControl>}
            </Stack></Box>
            <Box p={{ base: 4, md: 5 }} bg="var(--panel-bg)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px"><HStack spacing={2} mb={4}><Icon as={CircleStackIcon} boxSize="17px" color="var(--panel-accent)" /><Text fontWeight="800">مشخصات نسخه</Text></HStack><SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
              <FormControl isRequired><FormLabel>حجم (GiB)</FormLabel><Input minH="46px" type="number" min={0} step={0.01} dir="ltr" value={draft.dataGiB} onChange={(event) => setDraft((current) => ({ ...current, dataGiB: event.target.value }))} /></FormControl>
              <FormControl isRequired={!draft.isTrial}><FormLabel>قیمت پلن (تومان)</FormLabel><Input minH="46px" type="number" min={0} step={1000} dir="ltr" value={draft.isTrial ? "0" : draft.priceToman} isDisabled={draft.isTrial} onChange={(event) => setDraft((current) => ({ ...current, priceToman: event.target.value }))} /></FormControl>
              <FormControl isRequired><FormLabel>مدت (روز)</FormLabel><Input minH="46px" type="number" min={1} max={3650} dir="ltr" value={draft.durationDays} onChange={(event) => setDraft((current) => ({ ...current, durationDays: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>تعداد دستگاه</FormLabel><Input minH="46px" type="number" min={1} dir="ltr" value={draft.deviceLimit} placeholder="نامحدود" onChange={(event) => setDraft((current) => ({ ...current, deviceLimit: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>ریست حجم</FormLabel><Select minH="46px" value={draft.resetStrategy} onChange={(event) => setDraft((current) => ({ ...current, resetStrategy: event.target.value as PlanDraft["resetStrategy"] }))}><option value="no_reset">بدون ریست</option><option value="day">روزانه</option><option value="week">هفتگی</option><option value="month">ماهانه</option><option value="year">سالانه</option></Select></FormControl>
            </SimpleGrid></Box>
            <Alert status="info" variant="left-accent" borderRadius="14px" bg="var(--panel-accent-soft)" borderColor="var(--panel-accent-border)"><AlertIcon color="var(--panel-accent)" />این پلن فقط حجم، مدت، قیمت و محدودیت دستگاه را نسخه‌بندی می‌کند. شبکه از Access Group کاربر می‌آید.</Alert>
          </Stack></ModalBody>
          <ModalFooter flexShrink={0} gap={2} px={{ base: 3, md: 6 }} py={4} borderTopWidth="1px" borderColor="var(--panel-border)" bg="var(--panel-bg)"><Button minH="44px" variant="ghost" onClick={modal.onClose}>انصراف</Button><Button minH="44px" type="submit" bg="var(--panel-accent)" color="var(--panel-accent-contrast)" isLoading={save.isLoading} _hover={{ filter: "brightness(1.05)" }}>ذخیره</Button></ModalFooter>
        </ModalContent>
      </Modal>

      <AlertDialog isOpen={archiveDialog.isOpen} leastDestructiveRef={cancelRef} onClose={archiveDialog.onClose}><AlertDialogOverlay bg="rgba(0,0,0,.75)" backdropFilter="blur(5px)"><AlertDialogContent bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="18px" mx={3}><AlertDialogHeader>بایگانی پلن</AlertDialogHeader><AlertDialogBody color="var(--panel-text-body)">پلن «{archiveTarget?.name}» برای ساخت و تمدید جدید غیرفعال می‌شود.</AlertDialogBody><AlertDialogFooter gap={3} borderTopWidth="1px" borderColor="var(--panel-border)" mt={4} pt={4}><Button ref={cancelRef} onClick={archiveDialog.onClose}>انصراف</Button><Button colorScheme="red" isLoading={archive.isLoading} onClick={() => archiveTarget && archive.mutate(archiveTarget)} leftIcon={<Icon as={ArchiveBoxIcon} boxSize="16px" />}>بایگانی</Button></AlertDialogFooter></AlertDialogContent></AlertDialogOverlay></AlertDialog>
    </AppShell>
  );
};

export default Plans;
