import { Alert, AlertIcon, Box, Button, FormControl, FormLabel, HStack, Input, Stack, Text, useToast } from "@chakra-ui/react";
import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import useGetUser from "hooks/useGetUser";
import { fetch } from "service/http";
import { AdminCapabilities, ManagedAdminList } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { AdminFormDrawer } from "./AdminFormDrawer";
import { AdminTrialQuota } from "./AdminTrialQuota";
import { Incident } from "./alerts/presentation";

export function AlertAccountActions({ item }: { item: Incident }) {
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = userData.is_sudo || userData.role === "OWNER";
  const capabilities = useQuery<AdminCapabilities>(["admin-capabilities", userData.username], () => fetch("/admin/capabilities"), { enabled: getUserIsSuccess });
  const canManage = Boolean(isOwner || capabilities.data?.can_manage_admins) && item.admin_username !== userData.username;
  const target = useQuery<ManagedAdminList, Error>(["alert-action-admin", item.admin_username], () => fetch(`/admin-management?${new URLSearchParams({ username: item.admin_username, limit: "100" })}`), { enabled: canManage, staleTime: 0 });
  const admin = target.data?.admins.find(a => a.username === item.admin_username);
  const [amount, setAmount] = useState("");
  const [editing, setEditing] = useState(false);
  const request = useRef<{ key: string; id: string } | null>(null);
  const client = useQueryClient(); const toast = useToast();
  const refresh = () => ["admin-management", "alert-action-admin", "account-summary", "alert-center", "admin-capabilities"].forEach(key => client.invalidateQueries(key));
  const credit = useMutation(() => {
    const key = JSON.stringify([item.admin_username, amount]);
    if (request.current?.key !== key) request.current = { key, id: `alert-money-${crypto.randomUUID()}` };
    return fetch(`/admin-management/${encodeURIComponent(item.admin_username)}/money/grant`, { method: "POST", body: { amount_toman: Number(amount), idempotency_key: request.current.id } });
  }, { onSuccess: () => { request.current = null; setAmount(""); refresh(); toast({ title: "اعتبار افزایش یافت", status: "success", duration: 2200 }); }, onError: error => { toast({ title: "افزایش اعتبار انجام نشد", description: localizedApiError(error), status: "error" }); } });
  if (!canManage) return <Text mt={2} fontSize="xs" color="var(--panel-text-muted)">تغییر این حساب با ادمین بالادستی است.</Text>;
  if (target.isLoading) return <Text role="status" fontSize="xs">در حال دریافت اقدام‌های حساب…</Text>;
  if (target.isError) return <Alert status="error"><AlertIcon /><Button size="sm" onClick={() => target.refetch()}>دریافت دوباره حساب</Button></Alert>;
  if (!admin || admin.role === "OWNER") return <Text fontSize="xs">این حساب در محدودهٔ مدیریت شما نیست.</Text>;
  const valid = /^\d+$/.test(amount) && Number.isSafeInteger(Number(amount)) && Number(amount) > 0;
  return <Stack mt={3} spacing={3} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" bg="var(--panel-surface)">
    {item.resource === "financial" && <FormControl><FormLabel fontSize="sm">افزایش اعتبار (تومان)</FormLabel><HStack><Input aria-label={`مبلغ افزایش اعتبار ${item.admin_username}`} inputMode="numeric" dir="ltr" minW={0} value={amount} isDisabled={credit.isLoading} onChange={e => setAmount(e.target.value.replace(/[^0-9]/g, ""))} /><Button size="sm" colorScheme="primary" isDisabled={!valid} isLoading={credit.isLoading} onClick={() => credit.mutate()}>افزایش</Button></HStack></FormControl>}
    <HStack gap={2} flexWrap="wrap">{item.resource === "trials" && <AdminTrialQuota admin={admin} />}<Button size="sm" variant="outline" onClick={() => setEditing(true)}>ویرایش محدودیت‌ها</Button></HStack>
    <Text fontSize="xs" color="var(--panel-text-muted)">هشدار پس از رفع علت به‌روزرسانی می‌شود.</Text>
    {editing && <AdminFormDrawer isOpen={editing} admin={admin} onClose={() => { setEditing(false); refresh(); }} />}
  </Stack>;
}
