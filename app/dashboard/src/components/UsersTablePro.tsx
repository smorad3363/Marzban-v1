import {
  Badge,
  Box,
  Button,
  Checkbox,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Progress,
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
  chakra,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  ClipboardDocumentIcon,
  DocumentMagnifyingGlassIcon,
  EllipsisVerticalIcon,
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
import { UserDetailsDrawer } from "./UserDetailsDrawer";
import { UserDeviceLimit } from "./UserDeviceLimit";

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
const MoreIcon = chakra(EllipsisVerticalIcon, { baseStyle: { w: 4, h: 4 } });

const statusMeta: Record<User["status"], { label: string; color: string; bg: string; border: string; dot: string }> = {
  active: { label: "فعال", color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)", dot: "var(--panel-success)" },
  connected: { label: "فعال", color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)", dot: "var(--panel-success)" },
  connecting: { label: "در اتصال", color: "var(--panel-info)", bg: "var(--panel-info-soft)", border: "var(--panel-info-border)", dot: "var(--panel-info)" },
  on_hold: { label: "در انتظار", color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)", dot: "var(--panel-warning)" },
  disabled: { label: "غیرفعال", color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border-strong)", dot: "var(--panel-text-muted)" },
  expired: { label: "منقضی", color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)", dot: "var(--panel-danger)" },
  limited: { label: "محدود", color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)", dot: "var(--panel-warning)" },
  error: { label: "خطا", color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)", dot: "var(--panel-danger)" },
};

const parseUtc = (value: string | null | undefined) => {
  if (!value) return null;
  const normalized = /(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
};

const fmtDateTime = (value: string | null | undefined) => {
  const date = parseUtc(value);
  if (!date) return "—";
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

const relativeActivity = (value: string | null | undefined) => {
  const date = parseUtc(value);
  if (!date) return "بدون فعالیت";
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return "همین الآن";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes.toLocaleString("fa-IR")} دقیقه پیش`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours.toLocaleString("fa-IR")} ساعت پیش`;
  const days = Math.floor(hours / 24);
  return `${days.toLocaleString("fa-IR")} روز پیش`;
};

const relativeExpiry = (value: number | null) => {
  if (!value) return "نامحدود";
  const seconds = value - Math.floor(Date.now() / 1000);
  const days = Math.ceil(Math.abs(seconds) / 86400);
  if (seconds <= 0) return days <= 1 ? "منقضی" : `${days.toLocaleString("fa-IR")} روز از انقضا گذشته`;
  if (days <= 1) return "کمتر از یک روز";
  return `${days.toLocaleString("fa-IR")} روز مانده`;
};

const UsageCell: FC<{ user: User }> = ({ user }) => {
  const used = user.used_traffic ?? 0;
  const unlimited = !user.data_limit;
  const percent = unlimited ? 0 : Math.min(100, Math.max(0, (used / Math.max(user.data_limit || 1, 1)) * 100));
  const color = percent >= 95 ? "var(--panel-danger)" : percent >= 80 ? "var(--panel-warning)" : "var(--panel-success)";
  return (
    <Stack spacing={1.25} minW={0} w="full">
      <HStack justify="space-between" spacing={2} minW={0}>
        <Text dir="ltr" textAlign="start" fontSize="10px" fontWeight="800" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>
          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
        </Text>
        <Text flexShrink={0} color={unlimited ? "var(--panel-accent)" : color} fontSize="9px" fontWeight="850">
          {unlimited ? "∞" : `${Math.round(percent)}٪`}
        </Text>
      </HStack>
      {!unlimited && <Progress value={percent} h="4px" borderRadius="full" bg="var(--panel-nested)" sx={{ "& > div": { background: color } }} />}
    </Stack>
  );
};

const StatusPill: FC<{ status: User["status"] }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack w="fit-content" spacing={1.5} px={2.5} py={1} borderRadius="full" bg={meta.bg} borderWidth="1px" borderColor={meta.border}>
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.color} fontSize="10px" fontWeight="750">{meta.label}</Text>
    </HStack>
  );
};

const Action: FC<{ label: string; icon: React.ReactElement; onClick: () => void; tone?: "blue" | "green" | "red" | "gray"; disabled?: boolean }> = ({ label, icon, onClick, tone = "gray", disabled }) => {
  const palettes = {
    gray: { color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },
    blue: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },
    green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
    red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },
  } as const;
  const palette = palettes[tone];
  return (
    <Tooltip label={label} hasArrow placement="top">
      <IconButton
        aria-label={label}
        icon={icon}
        size="xs"
        minW="30px"
        w="30px"
        h="30px"
        borderRadius="10px"
        color={palette.color}
        bg={palette.bg}
        borderWidth="1px"
        borderColor={palette.border}
        isDisabled={disabled}
        onClick={onClick}
        _hover={{ transform: "translateY(-1px)", bg: palette.bg }}
      />
    </Tooltip>
  );
};

export const UsersTablePro: FC = () => {
  const {
    filters,
    users: { users, plan_meta },
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
  const [drawerUsername, setDrawerUsername] = useState<string | null>(null);
  const renewalRequest = useRef<{ key: string; id: string } | null>(null);

  const plans = useQuery<UserPlan[], Error>("user-plans", () => fetch("/user-plans"), { enabled: renewalModal.isOpen });
  const drawerUser = drawerUsername ? users.find((user) => user.username === drawerUsername) || null : null;
  const drawerPlanMeta = drawerUser ? plan_meta[drawerUser.username] || null : null;

  const openRenewal = (user: User) => {
    renewalRequest.current = null;
    setRenewalUser(user);
    setRenewalPlanId("");
    renewalModal.onOpen();
  };

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
        queryClient.invalidateQueries(["users-summary"]);
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

  useEffect(() => {
    if (drawerUsername && !users.some((user) => user.username === drawerUsername)) {
      setDrawerUsername(null);
    }
  }, [drawerUsername, users]);

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

  const showQr = (user: User) => {
    setQRCode(user.links);
    setSubLink(user.subscription_url);
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
        <Text color="var(--panel-text-muted)" fontSize="sm">فیلترها را تغییر دهید یا کاربر جدید بسازید.</Text>
        <Pagination />
      </Stack>
    );
  }

  return (
    <Box dir={i18n.dir()} w="full" minW={0}>
      <Box borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" bg="var(--panel-surface)" boxShadow="var(--shadow-panel)" overflow="hidden">
        {!readOnly && (
          <Box
            px={{ base: 2, md: 2.5 }}
            borderBottomWidth="1px"
            borderColor="var(--panel-border)"
            bg="var(--panel-nested)"
            sx={{
              "& > div:first-of-type": {
                marginTop: "0 !important",
                paddingInline: "0 !important",
                paddingBlock: "8px !important",
                border: "0 !important",
                borderRadius: "0 !important",
                background: "transparent !important",
              },
            }}
          >
            <BulkUserActions
              users={selectedUsers}
              allVisibleSelected={allVisibleSelected}
              visibleCount={users.length}
              onToggleAll={toggleAllVisible}
              onClear={() => setSelectedMap(new Map())}
            />
            {selectedUsers.length > users.filter((user) => selectedMap.has(user.username)).length && (
              <Text pb={2} color="var(--panel-warning)" fontSize="10px">
                انتخاب‌ها بین صفحه‌ها حفظ شده‌اند؛ مجموع انتخاب‌شده: {selectedUsers.length.toLocaleString("fa-IR")}
              </Text>
            )}
          </Box>
        )}

        <Text
          display={{ base: "block", md: "none" }}
          px={3}
          py={2}
          color="var(--panel-text-muted)"
          bg="var(--panel-nested)"
          borderBottomWidth="1px"
          borderColor="var(--panel-border)"
          fontSize="10px"
          lineHeight="1.6"
        >
          برای جزئیات روی نام کاربر بزنید؛ جدول در موبایل افقی پیمایش می‌شود.
        </Text>

        <TableContainer overflowX="auto" overscrollBehaviorX="contain" tabIndex={0} aria-label="جدول کاربران">
          <Table
            size="sm"
            w="full"
            minW={isOwner ? "1220px" : "1100px"}
            sx={{
              tableLayout: "fixed",
              "th, td": { borderBottom: "1px solid var(--panel-border) !important", px: 3, py: 2.5, overflow: "hidden" },
              "tbody tr:last-of-type td": { borderBottom: "0 !important" },
              th: { whiteSpace: "nowrap", fontWeight: 700, color: "var(--panel-text-muted)", fontSize: "10px" },
              "tbody tr:hover": { background: "var(--panel-row-hover)" },
            }}
          >
            <Thead bg="var(--panel-nested)">
              <Tr>
                {!readOnly && <Th w="38px"><Checkbox isChecked={allVisibleSelected} onChange={(event) => toggleAllVisible(event.target.checked)} colorScheme="primary" /></Th>}
                <Th w="38px" textAlign="center">#</Th>
                <Th w="190px">کاربر</Th>
                <Th w="105px">وضعیت</Th>
                <Th w="150px">پلن</Th>
                <Th w="190px">مصرف</Th>
                <Th w="145px">انقضا</Th>
                <Th w="105px">دستگاه</Th>
                <Th w="145px">آخرین فعالیت</Th>
                {isOwner && <Th w="120px">ادمین</Th>}
                <Th w="154px" textAlign="end">عملیات</Th>
              </Tr>
            </Thead>
            <Tbody>
              {users.map((user, index) => {
                const busy = busyUsername === user.username;
                const planMeta = plan_meta[user.username] || null;
                const deviceWarned = Boolean(user.device_limit_state && user.device_limit_state.penalty_status !== "clear");
                return (
                  <Tr
                    key={user.username}
                    opacity={user.status === "disabled" ? 0.72 : 1}
                    bg={selectedMap.has(user.username) ? "var(--panel-accent-soft)" : undefined}
                  >
                    {!readOnly && <Td><Checkbox isChecked={selectedMap.has(user.username)} onChange={(event) => setSelected(user, event.target.checked)} colorScheme="primary" /></Td>}
                    <Td textAlign="center" color="var(--panel-text-muted)" fontSize="10px" fontWeight="800">{((filters.offset || 0) + index + 1).toLocaleString("fa-IR")}</Td>
                    <Td>
                      <HStack spacing={2.5} minW={0}>
                        <Box w="30px" h="30px" display="grid" placeItems="center" borderRadius="full" bg="var(--panel-accent-soft)" color="var(--panel-accent)" fontSize="11px" fontWeight="900" flexShrink={0}>
                          {user.username.slice(0, 1).toUpperCase()}
                        </Box>
                        <Box minW={0}>
                          <Button
                            variant="link"
                            h="auto"
                            minW={0}
                            maxW="full"
                            color="var(--panel-accent)"
                            fontSize="11px"
                            fontWeight="900"
                            justifyContent="flex-start"
                            onClick={() => setDrawerUsername(user.username)}
                          >
                            <Text dir="ltr" textAlign="start" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>{user.username}</Text>
                          </Button>
                          <Text mt={0.5} color="var(--panel-text-muted)" fontSize="9px" noOfLines={1}>{user.note || "بدون توضیح"}</Text>
                        </Box>
                      </HStack>
                    </Td>
                    <Td><StatusPill status={user.status} /></Td>
                    <Td>
                      {planMeta ? (
                        <Stack spacing={0.5}>
                          <HStack spacing={1.5} minW={0}>
                            <Text fontSize="10px" fontWeight="850" noOfLines={1}>{planMeta.plan_name}</Text>
                            {planMeta.is_trial && <Badge colorScheme="yellow" variant="subtle" fontSize="8px">آزمایشی</Badge>}
                          </HStack>
                          <Text color="var(--panel-text-muted)" fontSize="8px">نسخه {planMeta.version_number.toLocaleString("fa-IR")}</Text>
                        </Stack>
                      ) : <Text color="var(--panel-text-muted)" fontSize="10px">بدون پلن</Text>}
                    </Td>
                    <Td><UsageCell user={user} /></Td>
                    <Td>
                      <Tooltip label={fmtExpire(user.expire)} hasArrow>
                        <Stack spacing={0.5}>
                          <Text fontSize="10px" fontWeight="800" color={user.status === "expired" ? "var(--panel-danger)" : "var(--panel-text-body)"}>{relativeExpiry(user.expire)}</Text>
                          <Text color="var(--panel-text-muted)" fontSize="8px">{fmtExpire(user.expire)}</Text>
                        </Stack>
                      </Tooltip>
                    </Td>
                    <Td>
                      <HStack spacing={1.5}>
                        <Text dir="ltr" fontSize="10px" fontWeight="850" sx={{ unicodeBidi: "isolate" }}>{user.concurrent_user_limit ?? "∞"}</Text>
                        {deviceWarned && <Box boxSize="6px" borderRadius="full" bg="var(--panel-warning)" title="هشدار دستگاه" />}
                        {!readOnly && isOwner && user.concurrent_user_limit != null && <UserDeviceLimit user={user} compact />}
                      </HStack>
                    </Td>
                    <Td>
                      <Tooltip label={fmtDateTime(user.online_at)} hasArrow>
                        <Stack spacing={0.5}>
                          <Text fontSize="10px" fontWeight="750">{relativeActivity(user.online_at)}</Text>
                          <Text color="var(--panel-text-muted)" fontSize="8px">{fmtDateTime(user.online_at)}</Text>
                        </Stack>
                      </Tooltip>
                    </Td>
                    {isOwner && <Td><Text dir="ltr" textAlign="start" fontSize="10px" fontWeight="800" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>{user.admin?.username || "—"}</Text></Td>}
                    <Td textAlign="end">
                      <HStack justify="end" gap={1} dir="ltr" maxW="full">
                        <Action label="کپی لینک اشتراک" icon={<CopyIcon />} onClick={() => copySubscription(user)} tone="green" />
                        {!readOnly && <Action label="ویرایش" icon={<EditIcon />} onClick={() => onEditingUser(user)} tone="blue" disabled={busy} />}
                        {!readOnly && <Action label="حذف کاربر" icon={<DeleteIcon />} onClick={() => onDeletingUser(user)} tone="red" disabled={busy} />}
                        <Menu placement="bottom-end" isLazy>
                          <MenuButton
                            as={IconButton}
                            aria-label="عملیات بیشتر"
                            icon={<MoreIcon />}
                            size="xs"
                            minW="30px"
                            w="30px"
                            h="30px"
                            borderRadius="10px"
                            color="var(--panel-text-body)"
                            bg="var(--panel-nested)"
                            borderWidth="1px"
                            borderColor="var(--panel-border)"
                            _hover={{ bg: "var(--panel-row-hover)" }}
                          />
                          <MenuList dir="rtl" minW="210px" bg="var(--panel-surface)" borderColor="var(--panel-border)" borderRadius="14px" boxShadow="var(--shadow-elevated)" py={1.5}>
                            <MenuItem onClick={() => setDrawerUsername(user.username)}>جزئیات کاربر</MenuItem>
                            <MenuItem icon={<QRIcon />} onClick={() => showQr(user)}>QR Code</MenuItem>
                            <MenuItem icon={<AuditIcon />} onClick={() => navigate(`/audit-logs/?search=${encodeURIComponent(user.username)}`)}>گزارش فعالیت</MenuItem>
                            {!readOnly && <MenuDivider borderColor="var(--panel-border)" />}
                            {!readOnly && <MenuItem icon={<RenewIcon />} isDisabled={busy} onClick={() => openRenewal(user)}>تمدید با پلن</MenuItem>}
                            {!readOnly && <MenuItem icon={user.status === "disabled" ? <PlayActionIcon /> : <PauseActionIcon />} isDisabled={busy} onClick={() => toggleStatus(user)}>{user.status === "disabled" ? "فعال‌سازی" : "غیرفعال‌سازی"}</MenuItem>}
                            {!readOnly && <MenuItem icon={<ResetIcon />} isDisabled={busy} onClick={() => resetUsage(user)}>بازنشانی مصرف</MenuItem>}
                            {!readOnly && <MenuItem icon={<RevokeIcon />} isDisabled={busy} onClick={() => revoke(user)}>ابطال لینک اشتراک</MenuItem>}
                          </MenuList>
                        </Menu>
                      </HStack>
                    </Td>
                  </Tr>
                );
              })}
            </Tbody>
          </Table>
        </TableContainer>
      </Box>

      <Pagination />

      <UserDetailsDrawer
        user={drawerUser}
        planMeta={drawerPlanMeta}
        isOpen={Boolean(drawerUser)}
        onClose={() => setDrawerUsername(null)}
        readOnly={readOnly}
        canViewDevices={isOwner}
        onEdit={(user) => { setDrawerUsername(null); onEditingUser(user); }}
        onDelete={(user) => { setDrawerUsername(null); onDeletingUser(user); }}
        onRenew={(user) => { setDrawerUsername(null); openRenewal(user); }}
        onToggleStatus={toggleStatus}
        onResetUsage={resetUsage}
        onRevokeSubscription={revoke}
        onShowQr={showQr}
      />

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
        <ModalContent dir={i18n.dir()} mx={3} bg="var(--panel-surface)" color="var(--panel-text)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px">
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
              <Text mt={2} color="var(--panel-text-muted)" fontSize="sm">قیمت: {(plans.data?.find((plan) => plan.id === Number(renewalPlanId))?.effective_price_toman || 0).toLocaleString("fa-IR")} تومان</Text>
            )}
          </ModalBody>
          <ModalFooter gap={3}>
            <Button variant="ghost" onClick={renewalModal.onClose} isDisabled={renew.isLoading}>انصراف</Button>
            <Button colorScheme="primary" color="var(--panel-accent-contrast)" isDisabled={!renewalUser || !renewalPlanId} isLoading={renew.isLoading} onClick={() => renewalUser && renewalPlanId && renew.mutate({ user: renewalUser, planId: Number(renewalPlanId) })}>تمدید</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default UsersTablePro;
