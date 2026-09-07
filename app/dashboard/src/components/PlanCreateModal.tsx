import {
  Alert, AlertIcon, Button, Checkbox, FormControl, FormHelperText, FormLabel,
  Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter,
  ModalHeader, ModalOverlay, Select, SimpleGrid, Stack, Textarea, useToast,
} from "@chakra-ui/react";
import { FC, FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { PlanCategory } from "types/Admin";
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

type Props = {
  isOpen: boolean;
  isOwner: boolean;
  onClose: () => void;
};

export const PlanCreateModal: FC<Props> = ({ isOpen, isOwner, onClose }) => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<PlanDraft>(emptyDraft());
  const categories = useQuery<PlanCategory[], Error>(
    "plan-categories",
    () => fetch("/plan-categories"),
    { enabled: isOpen }
  );

  useEffect(() => {
    if (isOpen) setDraft(emptyDraft());
  }, [isOpen]);

  const save = useMutation(
    () => fetch("/user-plans", {
      method: "POST",
      body: {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        category_id: Number(draft.categoryId),
        is_trial: draft.isTrial,
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
      },
    }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("user-plans");
        onClose();
        toast({ title: "پلن ذخیره شد", status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({
          title: "ذخیره پلن انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.categoryId) {
      toast({ title: "دسته‌بندی پلن را انتخاب کنید", status: "warning", duration: 3000 });
      return;
    }
    save.mutate();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl" scrollBehavior="inside">
      <ModalOverlay bg="rgba(0,0,0,.72)" />
      <ModalContent as="form" onSubmit={submit} mx={3} my={3} maxH="calc(100dvh - 24px)" overflow="hidden" bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border-strong)">
        <ModalHeader ps={14}>ساخت پلن</ModalHeader>
        <ModalCloseButton top={3} insetInlineStart={3} insetInlineEnd="auto" />
        <ModalBody overflowY="auto">
          <Stack spacing={4}>
            {categories.isError && <Alert status="error"><AlertIcon />دسته‌بندی‌ها دریافت نشدند.</Alert>}
            {!categories.isLoading && !categories.isError && (categories.data || []).length === 0 && <Alert status="warning"><AlertIcon />ابتدا از صفحه پلن‌ها یک دسته‌بندی بسازید.</Alert>}
            <Alert status="info" variant="left-accent"><AlertIcon />این پلن فقط شرایط تجاری را تعیین می‌کند. دسترسی شبکه هنگام ساخت کاربر از Access Group انتخاب می‌شود.</Alert>
            <FormControl isRequired><FormLabel>نام پلن</FormLabel><Input minH="44px" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
            <FormControl><FormLabel>توضیح</FormLabel><Textarea value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
            <FormControl isRequired><FormLabel>دسته‌بندی</FormLabel><Select value={draft.categoryId} onChange={(event) => setDraft((current) => ({ ...current, categoryId: event.target.value }))}><option value="">انتخاب دسته‌بندی</option>{(categories.data || []).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</Select></FormControl>
            {isOwner && <FormControl><Checkbox minH="44px" isChecked={draft.isTrial} onChange={(event) => setDraft((current) => ({ ...current, isTrial: event.target.checked }))}>پلن آزمایشی</Checkbox><FormHelperText>هر ساخت موفق یک سهمیه تست مصرف می‌کند.</FormHelperText></FormControl>}
            <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
              <FormControl isRequired><FormLabel>حجم (GiB)</FormLabel><Input minH="44px" type="number" min={0} step={0.01} dir="ltr" value={draft.dataGiB} onChange={(event) => setDraft((current) => ({ ...current, dataGiB: event.target.value }))} /></FormControl>
              <FormControl isRequired={!draft.isTrial}><FormLabel>قیمت پلن (تومان)</FormLabel><Input minH="44px" type="number" min={0} step={1000} dir="ltr" value={draft.isTrial ? "0" : draft.priceToman} isDisabled={draft.isTrial} onChange={(event) => setDraft((current) => ({ ...current, priceToman: event.target.value }))} /></FormControl>
              <FormControl isRequired><FormLabel>مدت (روز)</FormLabel><Input minH="44px" type="number" min={1} max={3650} dir="ltr" value={draft.durationDays} onChange={(event) => setDraft((current) => ({ ...current, durationDays: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>تعداد دستگاه</FormLabel><Input minH="44px" type="number" min={1} dir="ltr" value={draft.deviceLimit} onChange={(event) => setDraft((current) => ({ ...current, deviceLimit: event.target.value }))} /></FormControl>
              <FormControl><FormLabel>ریست حجم</FormLabel><Select minH="44px" value={draft.resetStrategy} onChange={(event) => setDraft((current) => ({ ...current, resetStrategy: event.target.value as PlanDraft["resetStrategy"] }))}><option value="no_reset">بدون ریست</option><option value="day">روزانه</option><option value="week">هفتگی</option><option value="month">ماهانه</option><option value="year">سالانه</option></Select></FormControl>
            </SimpleGrid>
          </Stack>
        </ModalBody>
        <ModalFooter flexShrink={0} gap={2} px={{ base: 3, md: 6 }} py={3} borderTopWidth="1px" borderColor="var(--panel-border)"><Button minH="44px" variant="ghost" onClick={onClose}>انصراف</Button><Button minH="44px" type="submit" colorScheme="primary" color="var(--panel-accent-contrast)" isLoading={save.isLoading} isDisabled={(categories.data || []).length === 0}>ذخیره</Button></ModalFooter>
      </ModalContent>
    </Modal>
  );
};
