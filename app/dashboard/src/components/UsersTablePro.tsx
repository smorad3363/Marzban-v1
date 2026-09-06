import {
  Badge,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  CircularProgressLabel,
  HStack,
  IconButton,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Select,
  Stack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tooltip,
  Tr,
  useDisclosure,
  useToast,
  chakra,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  ClipboardDocumentIcon,
  DocumentMagnifyingGlassIcon,
  LinkIcon,
  PauseIcon,
  PencilSquareIcon,
  PlayIcon,
  QrCodeIcon,
  RectangleStackIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { useDashboard } from "contexts/DashboardContext";
import useGetUser from "hooks/useGetUser";
import { FC, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { useNavigate } from "react-router-dom";
import { fetch } from "service/http";
import { AccountSummary, UserPlan } from "types/Admin";
import { User, UserCreate } from "types/User";
import { localizedApiError } from "utils/apiError";
import { formatBytes } from "utils/formatByte";
import { BulkUserActions } from "./BulkUserActions";
import { Pagination } from "./Pagination";

const CopyIcon = chakra(ClipboardDocumentIcon, { baseStyle: { w: 4, h: 4 } });
const QRIcon = chakra(QrCodeIcon, { baseStyle: { w: 4, h: 4 } });
const EditIcon = chakra(PencilSquareIcon, { baseStyle: { w: 4, h: 4 } });
const PauseActionIcon = chakra(PauseIcon, { baseStyle: { w: 4, h: 4 } });
const PlayActionIcon = chakra(PlayIcon, { baseStyle: { w: 4, h: 4 } });
const RenewIcon = chakra(RectangleStackIcon, { baseStyle: { w: 4, h: 4 } });
const ResetIcon = chakra(ArrowPathIcon, { baseStyle: { w: 4, h: 4 } });
const RevokeIcon = chakra(LinkIcon, { baseStyle: { w: 4, h: 4 } });
const DeleteIcon = chakra(TrashIcon, { baseStyle: { w: 4, h: 4 } });
const AuditIcon = chakra(DocumentMagnifyingGlassIcon, { baseStyle: { w: 4, h: 4 } });

const statusMeta: Record<User["status"], { label: string; color: string; bg: string }> = {
  active: { label: "فعال", color: "green.200", bg: "rgba(34,197,94,.12)" },
  connected: { label: "فعال", color: "green.200", bg: "rgba(34,197,94,.12)" },
  connecting: { label: "در اتصال", color: "cyan.200", bg: "rgba(6,182,212,.12)" },
  on_hold: { label: "در انتظار", color: "yellow.200", bg: "rgba(234,179,8,.12)" },
  disabled: { label: "غیرفعال", color: "red.200", bg: "rgba(239,68,68,.12)" },
  expired: { label: "منقضی", color: "red.200", bg: "rgba(239,68,68,.12)" },
  limited: { label: "محدود", color: "orange.200", bg: "rgba(249,115,22,.12)" },
  error: { label: "خطا", color: "red.200", bg: "rgba(239,68,68,.12)" },
};

const fmtDateTime = (value: string | null | undefined) => {
  if (!value) return "—";
  const normalized = /(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    timeZone: "Asia/Tehran",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date).replace("،", " ");
};

const fmtExpire = (value: number | null) => {
  if (!value) return "نامحدود";
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    timeZone: "Asia/Tehran",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value * 1000));
};

const UsageCell: FC<{ user: User }> = ({ user }) => {
  const used = user.used_traffic ?? 0;
  const unlimited = !user.data_limit;
  const percent = unlimited ? 0 : Math.min(100, Math.max(0, (used / Math.max(user.data_limit || 1, 1)) * 100));
  const color = percent >= 90 ? "#ef4444" : percent >= 70 ? "#eab308" : "#22c55e";
  return (
    <HStack spacing={1.5} minW={0} w="full" overflow="hidden">
      <CircularProgress flexShrink={0} value={percent} size="36px" thickness="7px" color={unlimited ? "#3b82f6" : color} trackColor="rgba(148,163,184,.13)" capIsRound>
        <CircularProgressLabel dir="ltr" fontSize="10px" fontWeight="900">{unlimited ? "∞" : `${Math.round(percent)}%`}</CircularProgressLabel>
      </CircularProgress>
      <Box minW={0}>
        <Text dir="ltr" textAlign="start" fontSize="10px" fontWeight="800" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>
          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
        </Text>
        <Text mt={1} color="gray.500" fontSize="9px">مصرف داده</Text>
      </Box>
    </HStack>
  );
};

const StatusPill: FC<{ status: User["status"] }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <Badge px={2.5} py={1.5} borderRadius="full" bg={meta.bg} color={meta.color} textTransform="none" fontSize="10px" fontWeight="800">
      {meta.label}
    </Badge>
  );
};

const Action: FC<{ label: string; icon: React.ReactElement; onClick: () => void; tone?: "blue" | "green" | "yellow" | "red" | "gray"; disabled?: boolean }> = ({ label, icon, onClick, tone = "gray", disabled }) => {
  const palettes = {
    gray: { color: "gray.200", bg: "rgba(148,163,184,.07)", border: "rgba(148,163,184,.18)" },
    blue: { color: "blue.200", bg: "rgba(59,130,246,.12)", border: "rgba(96,165,250,.22)" },
    green: { color: "green.200", bg: "rgba(34,197,94,.11)", border: "rgba(74,222,128,.20)" },
    yellow: { color: "yellow.200", bg: "rgba(234,179,8,.11)", border: "rgba(250,204,21,.20)" },
    red: { color: "red.200", bg: "rgba(239,68,68,.11)", border: "rgba(248,113,113,.20)" },
  } as const;
  const palette = palettes[tone];
  return (
    <Tooltip label={label} hasArrow placement="top">
      <IconButton
        aria-label={label}
        icon={icon}
        size="xs"
        minW="28px"
        w="28px"
        h="28px"
        borderRadius="7px"
        color={palette.color}
        bg={palette.bg}
        borderWidth="1px"
        borderColor={palette.border}
        isDisabled={disabled}
        onClick={onClick}
        transition="transform .14s ease, background .14s ease"
        _hover={{ transform: "translateY(-1px)", bg: palette.bg }}
        _active={{ transform: "translateY(0)" }}
      />
    </Tooltip>
  );
};

export const UsersTablePro: FC = () => {
  const {
    filters,
    users: { users },
    onEditingUser,
    onDeletingUser,
    setQRCode,
    setSubLink,
    refetchUsers,
    editUser,
    resetDataUsage,
    revokeSubscription,
  } = useDashboard();
  const { i18n } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const renewalModal = useDisclosure();
  const { userData, getUserIsSuccess } = useGetUser();
  const isOwner = getUserIsSuccess && (userData.is_sudo || userData.role === "OWNER");
  const account = useQuery<AccountSummary, Error>("account-summary", () => fetch("/account/summary"));
  const readOnly = account.data?.account_status !== "ACTIVE";
  const [selectedMap, setSelectedMap] = useState<Map<string, User>>(() => new Map());
  const [busyUsername, setBusyUsername] = useState<string | null>(null);
  const [renewalUser, setRenewalUser] = useState<User | null>(null);
  const [renewalPlanId, setRenewalPlanId] = useState("");
  const renewalRequest = useRef<{ key: string; id: string } | null>(null);

  const plans = useQuery<UserPlan[], Error>("user-plans", () => fetch("/user-plans"), { enabled: renewalModal.isOpen });

  const renew = useMutation(
    ({ user, planId }: { user: User; planId: number }) => {
      const key = `${user.username}:${planId}`;
      if (renewalRequest.current?.key !== key) renewalRequest.current = { key, id: `renew-${crypto.randomUUID()}` };
      return fetch(`/users/${user.username}/renew-from-plan`, {
        method: "POST",
        body: { plan_id: planId, idempotency_key: renewalRequest.current.id },
      });
    },
    {
      onSuccess: () => {
        refetchUsers();
        queryClient.invalidateQueries("account-summary");
        renewalModal.onClose();
        setRenewalUser(null);
        setRenewalPlanId("");
        toast({ title: "کاربر با پلن تمدید شد", status: "success", duration: 2500 });
      },
      onError: (error) => {
        toast({ title: "تمدید انجام نشد", description: localizedApiError(error), status: "error", duration: 5000 });
      },
    }
  );

  useEffect(() => {
    setSelectedMap((current) => {
      if (current.size === 0) return current;
      const next = new Map(current);
      users.forEach((user) => {
        if (next.has(user.username)) next.set(user.username, user);
      });
      return next;
    });
  }, [users]);

  const selectedUsers = useMemo(() => Array.from(selectedMap.values()), [selectedMap]);
  const allVisibleSelected = users.length > 0 && users.every((user) => selectedMap.has(user.username));

  const setSelected = (user: User, checked: boolean) => {
    setSelectedMap((current) => {
      const next = new Map(current);
      if (checked) next.set(user.username, user);
      else next.delete(user.username);
      return next;
    });
  };

  const toggleAllVisible = (checked: boolean) => {
    setSelectedMap((current) => {
      const next = new Map(current);
      users.forEach((user) => checked ? next.set(user.username, user) : next.delete(user.username));
      return next;
    });
  };

  const copySubscription = async (user: User) => {
    const value = user.subscription_url.startsWith("/") ? window.location.origin + user.subscription_url : user.subscription_url;
    try {
      await navigator.clipboard.writeText(value);
      toast({ title: "لینک کپی شد", status: "success", duration: 1400 });
    } catch {
      toast({ title: "کپی لینک انجام نشد", status: "error", duration: 2200 });
    }
  };

  const toggleStatus = async (user: User) => {
    if (readOnly) return;
    setBusyUsername(user.username);
    try {
      const payload: UserCreate = {
        inbounds: user.inbounds,
        proxies: user.proxies,
        expire: user.expire,
        data_limit: user.data_limit,
        data_limit_reset_strategy: user.data_limit_reset_strategy,
        on_hold_expire_duration: user.on_hold_expire_duration,
        username: user.username,
        status: user.status === "disabled" ? "active" : "disabled",
        note: user.note,
      };
      await editUser(payload);
      toast({ title: user.status === "disabled" ? "کاربر فعال شد" : "کاربر غیرفعال شد", status: "success", duration: 1800 });
    } catch (error) {
      toast({ title: "تغییر وضعیت انجام نشد", description: localizedApiError(error), status: "error", duration: 4500 });
    } finally {
      setBusyUsername(null);
    }
  };

  const resetUsage = async (user: User) => {
    if (!window.confirm(`مصرف ${user.username} بازنشانی شود؟`)) return;
    setBusyUsername(user.username);
    try {
      await resetDataUsage(user);
      toast({ title: "مصرف کاربر بازنشانی شد", status: "success", duration: 1800 });
    } catch (error) {
      toast({ title: "بازنشانی انجام نشد", description: localizedApiError(error), status: "error", duration: 4500 });
    } finally {
      setBusyUsername(null);
    }
  };

  const revoke = async (user: User) => {
    if (!window.confirm(`لینک اشتراک ${user.username} باطل و دوباره ساخته شود؟`)) return;
    setBusyUsername(user.username);
    try {
      await revokeSubscription(user);
      toast({ title: "لینک اشتراک باطل شد", status: "success", duration: 1800 });
    } catch (error) {
      toast({ title: "ابطال لینک انجام نشد", description: localizedApiError(error), status: "error", duration: 4500 });
    } finally {
      setBusyUsername(null);
    }
  };

  if (users.length === 0) {
    return (
      <Stack py={12} align="center" spacing={2}>
        <Text fontWeight="800">کاربری برای نمایش نیست</Text>
        <Text color="gray.500" fontSize="sm">فیلترها را تغییر دهید یا کاربر جدید بسازید.</Text>
        <Pagination />
      </Stack>
    );
  }

  return (
    <Box dir={i18n.dir()} w="full" minW={0}>
      {!readOnly && (
        <Box px={0} pb={2.5}>
          <BulkUserActions
            users={selectedUsers}
            allVisibleSelected={allVisibleSelected}
            visibleCount={users.length}
            onToggleAll={toggleAllVisible}
            onClear={() => setSelectedMap(new Map())}
          />
          {selectedUsers.length > users.filter((user) => selectedMap.has(user.username)).length && (
            <Text mt={1.5} color="yellow.300" fontSize="10px">
              انتخاب‌ها بین صفحه‌ها حفظ شده‌اند؛ مجموع انتخاب‌شده: {selectedUsers.length.toLocaleString("fa-IR")}
            </Text>
          )}
        </Box>
      )}

      <TableContainer overflowX="hidden" borderWidth="1px" borderColor="rgba(148,163,184,.12)" borderRadius="10px">
        <Table size="sm" w="full" sx={{ tableLayout: "fixed", "th, td": { borderColor: "rgba(148,163,184,.10)", px: 2, py: 2, overflow: "hidden" }, "th": { whiteSpace: "normal", lineHeight: 1.3 } }}>
          <Thead bg="rgba(2,8,23,.46)">
            <Tr>
              {!readOnly && <Th w="36px"><Checkbox isChecked={allVisibleSelected} onChange={(event) => toggleAllVisible(event.target.checked)} colorScheme="yellow" /></Th>}
              <Th w="34px" textAlign="center">#</Th>
              <Th>کاربر</Th>
              <Th>وضعیت</Th>
              <Th>مصرف ترافیک</Th>
              <Th>پلن بعدی</Th>
              <Th>انقضا</Th>
              <Th>تاریخ ایجاد</Th>
              <Th>ادمین</Th>
              <Th>آخرین فعالیت</Th>
              <Th>کلاینت / نسخه</Th>
              <Th>بازنشانی</Th>
              <Th>توضیحات</Th>
              <Th w="18%" textAlign="end">عملیات</Th>
            </Tr>
          </Thead>
          <Tbody>
            {users.map((user, index) => {
              const busy = busyUsername === user.username;
              const nextPlan = user.next_plan;
              return (
                <Tr
                  key={user.username}
                  bg={selectedMap.has(user.username) ? "rgba(234,179,8,.045)" : "transparent"}
                  transition="background .14s ease"
                  _hover={{ bg: selectedMap.has(user.username) ? "rgba(234,179,8,.07)" : "rgba(255,255,255,.025)" }}
                >
                  {!readOnly && <Td><Checkbox isChecked={selectedMap.has(user.username)} onChange={(event) => setSelected(user, event.target.checked)} colorScheme="yellow" /></Td>}
                  <Td textAlign="center" fontWeight="800">{((filters.offset || 0) + index + 1).toLocaleString("fa-IR")}</Td>
                  <Td>
                    <HStack spacing={2.5}>
                      <Box w="32px" h="32px" display="grid" placeItems="center" borderRadius="full" bg="rgba(59,130,246,.18)" color="blue.100" fontWeight="900" flexShrink={0}>
                        {user.username.slice(0, 1).toUpperCase()}
                      </Box>
                      <Box minW={0}>
                        <Text dir="ltr" textAlign="start" color="cyan.200" fontSize="12px" fontWeight="850" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>{user.username}</Text>
                        <Text mt={1} color="gray.500" fontSize="9px">سقف اتصال: {user.concurrent_user_limit ?? "∞"}</Text>
                      </Box>
                    </HStack>
                  </Td>
                  <Td><StatusPill status={user.status} /></Td>
                  <Td><UsageCell user={user} /></Td>
                  <Td>
                    {nextPlan ? (
                      <Stack spacing={0.5}>
                        <Badge w="fit-content" colorScheme="yellow" variant="outline" textTransform="none" fontSize="9px">{nextPlan.data_limit ? String(formatBytes(nextPlan.data_limit)) : "نامحدود"}</Badge>
                        <Text color="gray.500" fontSize="9px">{nextPlan.expire ? fmtExpire(nextPlan.expire) : "بدون انقضا"}</Text>
                      </Stack>
                    ) : <Text color="gray.600" fontSize="10px">تنظیم نشده</Text>}
                  </Td>
                  <Td><Text fontSize="11px" fontWeight="700">{fmtExpire(user.expire)}</Text></Td>
                  <Td><Text fontSize="10px" lineHeight="1.6">{fmtDateTime(user.created_at)}</Text></Td>
                  <Td><Text dir="ltr" textAlign="start" fontSize="11px" fontWeight="800" sx={{ unicodeBidi: "isolate" }}>{user.admin?.username || "—"}</Text></Td>
                  <Td>
                    <Text fontSize="10px" lineHeight="1.6">{fmtDateTime(user.online_at)}</Text>
                    <Text mt={1} color={user.online_at ? "green.300" : "gray.600"} fontSize="9px">{user.online_at ? "دارای فعالیت" : "بدون فعالیت ثبت‌شده"}</Text>
                  </Td>
                  <Td>
                    <Tooltip label={user.sub_last_user_agent || "—"} hasArrow>
                      <Text dir="ltr" textAlign="start" fontSize="10px" noOfLines={2} overflowWrap="anywhere" sx={{ unicodeBidi: "isolate" }}>{user.sub_last_user_agent || "—"}</Text>
                    </Tooltip>
                  </Td>
                  <Td>
                    <Text fontSize="12px" fontWeight="850">{(user.reset_history?.length || 0).toLocaleString("fa-IR")}</Text>
                    <Text color="gray.500" fontSize="9px">مرتبه</Text>
                  </Td>
                  <Td>
                    <Tooltip label={user.note || "—"} hasArrow>
                      <Text fontSize="10px" noOfLines={2} color={user.note ? "gray.300" : "gray.600"}>{user.note || "—"}</Text>
                    </Tooltip>
                  </Td>
                  <Td textAlign="end">
                    <HStack justify="end" gap={1} rowGap={1} dir="ltr" flexWrap="wrap" maxW="full">
                      <Action label="کپی لینک اشتراک" icon={<CopyIcon />} onClick={() => copySubscription(user)} tone="green" />
                      <Action label="QR Code" icon={<QRIcon />} onClick={() => { setQRCode(user.links); setSubLink(user.subscription_url); }} tone="blue" />
                      <Action label="گزارش فعالیت" icon={<AuditIcon />} onClick={() => navigate(`/audit-logs/?search=${encodeURIComponent(user.username)}`)} tone="gray" />
                      {!readOnly && <Action label="تمدید با پلن" icon={<RenewIcon />} onClick={() => { renewalRequest.current = null; setRenewalUser(user); setRenewalPlanId(""); renewalModal.onOpen(); }} tone="yellow" disabled={busy} />}
                      {!readOnly && <Action label="ویرایش" icon={<EditIcon />} onClick={() => onEditingUser(user)} tone="blue" disabled={busy} />}
                      {!readOnly && <Action label={user.status === "disabled" ? "فعال‌سازی" : "غیرفعال‌سازی"} icon={user.status === "disabled" ? <PlayActionIcon /> : <PauseActionIcon />} onClick={() => toggleStatus(user)} tone={user.status === "disabled" ? "green" : "yellow"} disabled={busy} />}
                      {!readOnly && <Action label="بازنشانی مصرف" icon={<ResetIcon />} onClick={() => resetUsage(user)} tone="gray" disabled={busy} />}
                      {!readOnly && <Action label="ابطال لینک اشتراک" icon={<RevokeIcon />} onClick={() => revoke(user)} tone="yellow" disabled={busy} />}
                      {!readOnly && <Action label="حذف کاربر" icon={<DeleteIcon />} onClick={() => onDeletingUser(user)} tone="red" disabled={busy} />}
                    </HStack>
                  </Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      </TableContainer>

      <Pagination />

      <Modal
        isOpen={renewalModal.isOpen}
        onClose={() => {
          if (renew.isLoading) return;
          renewalModal.onClose();
          setRenewalUser(null);
          setRenewalPlanId("");
        }}
        isCentered
      >
        <ModalOverlay bg="rgba(0,0,0,.72)" />
        <ModalContent dir={i18n.dir()} mx={3} bg="#0c1524" color="gray.100" borderWidth="1px" borderColor="rgba(148,163,184,.16)" borderRadius="14px">
          <ModalHeader>تمدید «{renewalUser?.username}» با پلن</ModalHeader>
          <ModalCloseButton isDisabled={renew.isLoading} />
          <ModalBody>
            <Select
              minH="44px"
              value={renewalPlanId}
              onChange={(event) => setRenewalPlanId(event.target.value)}
              isDisabled={plans.isLoading || plans.isError || renew.isLoading}
            >
              <option value="">انتخاب پلن</option>
              {(plans.data || []).map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name} · v{plan.version_number} · {String(formatBytes(plan.version.data_limit))} · {plan.version.duration_days} روز</option>
              ))}
            </Select>
            {renewalPlanId && (
              <Text mt={2} color="gray.400" fontSize="sm">قیمت: {(plans.data?.find((plan) => plan.id === Number(renewalPlanId))?.effective_price_toman || 0).toLocaleString("fa-IR")} تومان</Text>
            )}
          </ModalBody>
          <ModalFooter gap={3}>
            <Button variant="ghost" onClick={renewalModal.onClose} isDisabled={renew.isLoading}>انصراف</Button>
            <Button colorScheme="yellow" color="gray.900" isDisabled={!renewalUser || !renewalPlanId} isLoading={renew.isLoading} onClick={() => renewalUser && renewalPlanId && renew.mutate({ user: renewalUser, planId: Number(renewalPlanId) })}>تمدید</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default UsersTablePro;
