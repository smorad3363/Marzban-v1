import { Alert, AlertIcon, Badge, Box, Button, FormControl, FormLabel, HStack, Input, Select, Stack, Text, useToast } from "@chakra-ui/react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { localizedApiError } from "utils/apiError";

type RequestItem = { id: number; username: string; account_admin_id: number; reviewer_admin_id: number; status: string; purchase_toman: number; refund_toman: number | null; used_bytes: number; quota_bytes: number; created_at: string; decision_note: string | null };
type AlertItem = { id: number; admin_id: number; admin_username: string | null; kind: string; details?: { username?: string; percent?: number; balance_toman?: number }; created_at: string };
type Data = { actor_id: number; requests: RequestItem[]; alerts: AlertItem[] };
const labels: Record<string, string> = { incident_open: "هشدار جدید", incident_change: "تغییر وضعیت هشدار", incident_resolved: "رفع هشدار", low: "کمبود موجودی (۱۰٪ آخرین شارژ)", empty: "اتمام موجودی", frozen: "فریز مالی؛ ساخت و تمدید متوقف است", disabled: "قطع کاربران به دلیل بدهی", normal: "رفع محدودیت مالی", user_usage: "رسیدن کاربر به حد مصرف", account_suspended: "تعلیق حساب ادمین", account_disabled: "غیرفعال شدن حساب ادمین" };
const statuses: Record<string, string> = { PENDING: "در انتظار بررسی", APPROVED: "تأیید و حذف شد", REJECTED: "رد شد" };

export const RequestsAlerts = () => {
  const toast = useToast();
  const client = useQueryClient();
  const [filter, setFilter] = useState("");
  const [requestBefore, setRequestBefore] = useState<number | null>(null);
  const [alertBefore, setAlertBefore] = useState<number | null>(null);
  const [amounts, setAmounts] = useState<Record<number, string>>({});
  const [notes, setNotes] = useState<Record<number, string>>({});
  const query = useQuery<Data, Error>(["admin-requests-alerts", requestBefore, alertBefore], () => fetch(`/admin-management/requests-alerts?${new URLSearchParams({ ...(requestBefore ? { request_before_id: String(requestBefore) } : {}), ...(alertBefore ? { alert_before_id: String(alertBefore) } : {}) })}`), { refetchInterval: 60000, refetchIntervalInBackground: false });
  const decide = useMutation(({ item, approve }: { item: RequestItem; approve: boolean }) => fetch(`/admin-management/deletion-requests/${item.id}/decision`, { method: "POST", body: { approve, refund_toman: approve ? Number(amounts[item.id] ?? item.purchase_toman) : 0, note: notes[item.id]?.trim() || null } }), {
    onSuccess: () => { client.invalidateQueries("admin-requests-alerts"); client.invalidateQueries("admin-management"); client.invalidateQueries("account-summary"); client.invalidateQueries("users"); toast({ title: "تصمیم ثبت شد", status: "success" }); },
    onError: (error) => { toast({ title: "ثبت تصمیم انجام نشد", description: localizedApiError(error), status: "error" }); },
  });
  return <Box borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" p={4}>
    <Text as="h2" fontWeight="800">درخواست‌ها و هشدارها</Text>
    <Text fontSize="sm" mt={2}>درخواست‌های بیشتر از ۱٪ مصرف فقط توسط ادمین بالادستی مستقیم بررسی می‌شوند. تا تأیید، کاربر حذف نمی‌شود.</Text>
    {query.isError && <Alert status="error" mt={3}><AlertIcon />{localizedApiError(query.error)}<Button ms={2} onClick={() => query.refetch()}>تلاش مجدد</Button></Alert>}
    <Select aria-label="وضعیت درخواست" my={3} value={filter} onChange={(e) => setFilter(e.target.value)} maxW="240px"><option value="">تاریخچه همه درخواست‌ها</option><option value="PENDING">در انتظار بررسی</option><option value="APPROVED">تأییدشده</option><option value="REJECTED">ردشده</option></Select>
    <Stack spacing={3} maxH="500px" overflowY="auto">
      {query.data?.requests.filter((item) => !filter || item.status === filter).map((item) => <Box key={item.id} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" p={3}>
        <HStack justify="space-between" flexWrap="wrap"><Text dir="ltr">{item.username}</Text><Badge>{statuses[item.status] || item.status}</Badge></HStack>
        <Text fontSize="sm" mt={2}>مبلغ خرید: {item.purchase_toman.toLocaleString("fa-IR")} تومان · مصرف: {item.quota_bytes ? (item.used_bytes * 100 / item.quota_bytes).toFixed(2) + "٪" : `${item.used_bytes} بایت`}</Text>
        {item.status === "PENDING" && item.reviewer_admin_id === query.data?.actor_id ? <Stack mt={3}>
          <FormControl><FormLabel fontSize="sm">مبلغ بازگشت (تومان، حداکثر مبلغ خرید)</FormLabel><Input aria-label={`مبلغ بازگشت ${item.id}`} dir="ltr" inputMode="numeric" value={amounts[item.id] ?? String(item.purchase_toman)} onChange={(e) => setAmounts((old) => ({ ...old, [item.id]: e.target.value }))} /></FormControl>
          <Input aria-label={`توضیح تصمیم ${item.id}`} placeholder="توضیح تصمیم" value={notes[item.id] || ""} onChange={(e) => setNotes((old) => ({ ...old, [item.id]: e.target.value }))} />
          <HStack><Button colorScheme="green" isLoading={decide.isLoading} isDisabled={!/^\d+$/.test(amounts[item.id] ?? String(item.purchase_toman)) || Number(amounts[item.id] ?? item.purchase_toman) > item.purchase_toman} onClick={() => decide.mutate({ item, approve: true })}>تأیید بازگشت و حذف</Button><Button isDisabled={decide.isLoading} onClick={() => decide.mutate({ item, approve: false })}>رد درخواست</Button></HStack>
        </Stack> : <Text mt={2} fontSize="sm">{item.refund_toman !== null ? `بازگشت: ${item.refund_toman.toLocaleString("fa-IR")} تومان` : "منتظر بررسی بالادستی"} {item.decision_note}</Text>}
      </Box>)}
      {query.isSuccess && query.data?.requests.length === 0 && <Text>درخواستی ثبت نشده است.</Text>}
    </Stack>
    <HStack mt={3}><Button size="sm" onClick={() => setRequestBefore(null)} isDisabled={!requestBefore}>جدیدترین درخواست‌ها</Button><Button size="sm" isDisabled={query.data?.requests.length !== 100} onClick={() => setRequestBefore(query.data?.requests[query.data.requests.length - 1]?.id || null)}>درخواست‌های قدیمی‌تر</Button></HStack>
    <Stack mt={4} spacing={2} maxH="260px" overflowY="auto">{query.data?.alerts.map((item) => <Box key={item.id} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" p={3}><Text fontSize="sm">{labels[item.kind] || item.kind} · ادمین {item.admin_username || "حذف‌شده"} {item.details?.username} {item.details?.percent ? `${item.details.percent}٪` : ""}</Text><Text fontSize="xs" color="var(--panel-text-muted)">{new Date(item.created_at + (item.created_at.endsWith("Z") ? "" : "Z")).toLocaleString("fa-IR")}</Text></Box>)}</Stack>
    <HStack mt={3}><Button size="sm" onClick={() => setAlertBefore(null)} isDisabled={!alertBefore}>جدیدترین هشدارها</Button><Button size="sm" isDisabled={query.data?.alerts.length !== 100} onClick={() => setAlertBefore(query.data?.alerts[query.data.alerts.length - 1]?.id || null)}>هشدارهای قدیمی‌تر</Button></HStack>
  </Box>;
};
