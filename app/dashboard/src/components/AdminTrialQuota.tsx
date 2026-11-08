import { Box, Button, FormControl, FormLabel, HStack, Input, Popover, PopoverBody, PopoverCloseButton, PopoverContent, PopoverHeader, PopoverTrigger, Stack, Text, useToast } from "@chakra-ui/react";
import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { ManagedAdmin } from "types/Admin";
import { localizedApiError } from "utils/apiError";
type Operation = "grant" | "reclaim" | "reset";
export function AdminTrialQuota({ admin, disabled = false }: { admin: ManagedAdmin; disabled?: boolean }) {
  const [amount, setAmount] = useState("");
  const [open, setOpen] = useState(false);
  const request = useRef<{ key: string; id: string } | null>(null);
  const client = useQueryClient(); const toast = useToast();
  const mutation = useMutation((operation: Operation) => {
    const key = JSON.stringify([admin.username, operation, amount]);
    if (request.current?.key !== key) request.current = { key, id: `trial-${crypto.randomUUID()}` };
    return fetch(`/admin-management/${encodeURIComponent(admin.username)}/trial-quota/${operation}`, { method: "POST", body: { idempotency_key: request.current.id, ...(operation === "reset" ? {} : { amount: Number(amount) }) } });
  }, {
    onSuccess: () => { request.current = null; setAmount(""); setOpen(false); ["admin-management", "alert-action-admin", "admin-hierarchy-tree", "admin-capabilities", "account-summary", "alert-center"].forEach(key => client.invalidateQueries(key)); toast({ title: "سهمیه تست به‌روزرسانی شد", status: "success", duration: 2200 }); },
    onError: error => { toast({ title: "تغییر سهمیه تست انجام نشد", description: localizedApiError(error), status: "error" }); },
  });
  const valid = /^\d+$/.test(amount) && Number.isSafeInteger(Number(amount)) && Number(amount) > 0;
  return <Popover isOpen={open} onOpen={() => setOpen(true)} onClose={() => { if (!mutation.isLoading) setOpen(false); }} placement="bottom-start" isLazy>
    <PopoverTrigger><Button size="sm" variant="outline" isDisabled={disabled} aria-label={`مدیریت سهمیه تست ${admin.username}`}>تست: {admin.trial_quota.toLocaleString("fa-IR")}</Button></PopoverTrigger>
    <PopoverContent w="310px" maxW="calc(100vw - 24px)" bg="var(--panel-surface)" borderColor="var(--panel-border)" boxShadow="var(--shadow-elevated)"><PopoverCloseButton aria-label="بستن سهمیه تست" isDisabled={mutation.isLoading} /><PopoverHeader fontWeight="700">سهمیه تست <Box as="bdi">{admin.username}</Box></PopoverHeader><PopoverBody><Stack spacing={3}>
      <Text fontSize="xs" color="var(--panel-text-muted)">مانده: {admin.trial_quota.toLocaleString("fa-IR")} · سقف: {admin.trial_quota_limit.toLocaleString("fa-IR")} · مصرف‌شده: {admin.trials_used.toLocaleString("fa-IR")}</Text>
      <FormControl><FormLabel fontSize="sm">تعداد تست</FormLabel><Input dir="ltr" inputMode="numeric" value={amount} isDisabled={mutation.isLoading} onChange={e => setAmount(e.target.value.replace(/[^0-9]/g, ""))} /></FormControl>
      <HStack><Button size="sm" colorScheme="primary" isDisabled={!valid || mutation.isLoading} onClick={() => mutation.mutate("grant")}>افزایش</Button><Button size="sm" variant="outline" isDisabled={!valid || Number(amount) > admin.trial_quota || mutation.isLoading} onClick={() => { if (window.confirm(`سهمیه تست ${admin.username} به تعداد ${amount} کم شود؟`)) mutation.mutate("reclaim"); }}>کاهش</Button><Button size="sm" variant="ghost" isDisabled={mutation.isLoading} onClick={() => { if (window.confirm(`سهمیه تست ${admin.username} به سقف ${admin.trial_quota_limit} بازگردد؟`)) mutation.mutate("reset"); }}>بازنشانی</Button></HStack>
      {mutation.isLoading && <Text role="status" fontSize="xs">در حال ثبت تغییر…</Text>}
    </Stack></PopoverBody></PopoverContent>
  </Popover>;
}
