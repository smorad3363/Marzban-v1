import { Alert, AlertIcon, Box, Button, FormControl, FormHelperText, FormLabel, HStack, Input, Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay, Select, Stack, Text, useToast } from "@chakra-ui/react";
import { ArrowPathIcon } from "@heroicons/react/24/outline";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "react-query";
import { useDashboard } from "contexts/DashboardContext";
import { fetch } from "service/http";
import { AccessGroup } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { queryClient } from "utils/react-query";
import { formatBytes } from "utils/formatByte";

type AvailableUserPlan = { id: number; name: string; data_limit: number; duration_days: number; price_toman: number; concurrent_user_limit: number | null };
const randomUsername = () => `u_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
export const CreateUserFromPlan = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const [username, setUsername] = useState("");
  const [planId, setPlanId] = useState("");
  const [groupId, setGroupId] = useState("");
  const request = useRef<{ key: string; id: string } | null>(null);
  const toast = useToast();
  const plans = useQuery<AvailableUserPlan[]>("available-user-plans", () => fetch("/available-user-plans"), { enabled: isOpen });
  const groups = useQuery<AccessGroup[]>("access-groups", () => fetch("/access-groups"), { enabled: isOpen });
  useEffect(() => { if (isOpen) { setUsername(randomUsername()); request.current = null; } }, [isOpen]);
  useEffect(() => { if (plans.data) setPlanId(v => plans.data!.some(i => String(i.id) === v) ? v : plans.data!.length === 1 ? String(plans.data![0].id) : ""); }, [plans.data]);
  useEffect(() => { if (groups.data) setGroupId(v => groups.data!.some(i => String(i.id) === v) ? v : groups.data!.length === 1 ? String(groups.data![0].id) : ""); }, [groups.data]);
  const create = useMutation(() => {
    const key = JSON.stringify([username.trim(), planId, groupId]);
    if (request.current?.key !== key) request.current = { key, id: `create-${crypto.randomUUID()}` };
    return fetch("/users/from-plan", { method: "POST", body: { username: username.trim(), plan_id: Number(planId), access_group_id: Number(groupId), status: "active", idempotency_key: request.current.id } });
  }, {
    onSuccess: () => { useDashboard.getState().refetchUsers(); ["account-summary", "users-summary", "dashboard-overview-v2"].forEach(key => queryClient.invalidateQueries(key)); toast({ title: "کاربر ساخته شد", status: "success", duration: 2200 }); onClose(); },
    onError: error => { toast({ title: "ساخت کاربر انجام نشد", description: localizedApiError(error), status: "error" }); },
  });
  const plan = plans.data?.find(i => i.id === Number(planId));
  const group = groups.data?.find(i => i.id === Number(groupId));
  const valid = /^[a-zA-Z0-9_]{3,32}$/.test(username.trim());
  return <Modal isOpen={isOpen} onClose={create.isLoading ? () => undefined : onClose} isCentered scrollBehavior="inside"><ModalOverlay /><ModalContent dir="rtl" mx={3} as="form" onSubmit={event => { event.preventDefault(); if (plan && group && valid && !create.isLoading && !groups.isError && !plans.isError) create.mutate(); }}>
    <ModalHeader>ساخت سریع از پلن</ModalHeader><ModalCloseButton aria-label="بستن ساخت کاربر" isDisabled={create.isLoading} />
    <ModalBody><Stack spacing={3}>
      {(plans.isError || groups.isError) && <Alert status="error"><AlertIcon />دریافت گزینه‌ها انجام نشد.<Button size="sm" onClick={() => { plans.refetch(); groups.refetch(); }}>تلاش مجدد</Button></Alert>}
      <FormControl isRequired><FormLabel>نام کاربری</FormLabel><HStack><Input dir="ltr" autoComplete="off" maxLength={32} value={username} isDisabled={create.isLoading} onChange={e => setUsername(e.target.value)} /><Button type="button" minW="44px" variant="outline" aria-label="ساخت نام تصادفی" isDisabled={create.isLoading} onClick={() => setUsername(randomUsername())}><ArrowPathIcon width={16} /></Button></HStack><FormHelperText>نام آماده است؛ می‌توانید تغییرش دهید. ۳ تا ۳۲ حرف انگلیسی، عدد یا زیرخط.</FormHelperText></FormControl>
      <FormControl isRequired><FormLabel>پلن</FormLabel><Select value={planId} isDisabled={plans.isLoading || create.isLoading} onChange={e => setPlanId(e.target.value)}><option value="">{plans.isLoading ? "در حال دریافت…" : "انتخاب پلن"}</option>{plans.data?.map(i => <option key={i.id} value={i.id}>{i.name} · {i.price_toman.toLocaleString("fa-IR")} تومان</option>)}</Select></FormControl>
      {!plans.isLoading && !plans.isError && !plans.data?.length && <Text role="status">پلنی در دسترس نیست؛ با ادمین بالادستی پیگیری کنید.</Text>}
      <FormControl isRequired><FormLabel>گروه دسترسی</FormLabel><Select value={groupId} isDisabled={groups.isLoading || create.isLoading} onChange={e => setGroupId(e.target.value)}><option value="">{groups.isLoading ? "در حال دریافت…" : "انتخاب مسیر اتصال"}</option>{groups.data?.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}</Select></FormControl>
      {!groups.isLoading && !groups.isError && !groups.data?.length && <Alert status="warning"><AlertIcon />گروه دسترسی موجود نیست؛ ابتدا یک گروه مجاز تعریف کنید.</Alert>}
      {plan && <Box role="status" p={3} bg="var(--panel-nested)" borderRadius="10px"><HStack justify="space-between" flexWrap="wrap"><Text>{plan.duration_days.toLocaleString("fa-IR")} روز · {plan.data_limit ? String(formatBytes(plan.data_limit)) : "حجم نامحدود"}</Text><Text fontWeight="700">{plan.price_toman.toLocaleString("fa-IR")} تومان</Text></HStack><Text mt={1} fontSize="xs" color="var(--panel-text-muted)">هزینه طبق سیاست حساب شما محاسبه می‌شود.</Text></Box>}
    </Stack></ModalBody><ModalFooter gap={2}><Button type="button" minH="44px" onClick={onClose} isDisabled={create.isLoading}>انصراف</Button><Button minH="44px" type="submit" colorScheme="primary" isLoading={create.isLoading} isDisabled={!plan || !group || !valid || plans.isError || groups.isError || groups.isLoading}>ساخت کاربر</Button></ModalFooter>
  </ModalContent></Modal>;
};
