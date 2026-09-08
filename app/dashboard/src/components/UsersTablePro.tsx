import {
  Badge,
  Box,
  Button,
  Checkbox,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Progress,
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
import { UserDeviceLimit } from "./UserDeviceLimit";
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
  const color = percent >= 90 ? "var(--panel-danger)" : percent >= 70 ? "var(--panel-warning)" : "var(--panel-success)";
  return (
    <Stack spacing={1.5} minW={0} w="full">
      <HStack justify="space-between" spacing={2} minW={0}>
        <Text dir="ltr" textAlign="start" fontSize="10px" fontWeight="800" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>
          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
        </Text>
        {unlimited ? (
          <Box px={2} py={0.5} borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius="full" color="var(--panel-accent)" fontSize="11px" fontWeight="900">∞</Box>
        ) : (
          <Text color="var(--panel-text-muted)" fontSize="9px">{Math.round(percent)}٪</Text>
        )}
      </HStack>
      {!unlimited && <Progress value={percent} h="4px" borderRadius="full" bg="var(--panel-nested)" sx={{ "& > div": { background: color } }} />}
      <Text color="var(--panel-text-muted)" fontSize="9px">مصرف داده</Text>
    </Stack>
  );
};

const StatusPill: FC<{ status: User["status"] }> = ({ status }) => {
  const meta = statusMeta[status];
  return (
    <HStack w="fit-content" spacing={1.5} px={2.5} py={1.25} borderRadius="full" bg={meta.bg} borderWidth="1px" borderColor={meta.border}>
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.color} fontSize="10px" fontWeight="750">{meta.label}</Text>
    </HStack>
  );
};

const Action: FC<{ label: string; icon: React.ReactElement; onClick: () => void; tone?: "blue" | "green" | "yellow" | "red" | "gray"; disabled?: boolean }> = ({ label, icon, onClick, tone = "gray", disabled }) => {
  const palettes = {
    gray: { color: "var(--panel-text-muted)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },
    blue: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },
    green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
    yellow: { color: "var(--panel-warning)", bg: "var(--panel-warning-soft)", border: "var(--panel-warning-border)" },
    red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },
  } as const;
  const palette = palettes[tone];
  return (
    <Tooltip label={label} hasArrow placement="top">
      <IconButton
        aria-label={label}
        icon={icon}
        size="xs"
        minW="32px"
        w="32px"
        h="32px"
        borderRadius="12px"
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
          display={{ base: "block", lg: "none" }}
          px={3}
          py={2}
          color="var(--panel-text-muted)"
          bg="var(--panel-nested)"
          borderBottomWidth="1px"
          borderColor="var(--panel-border)"
          fontSize="10px"
          lineHeight="1.6"
        >
          برای دیدن همه جزئیات و عملیات، جدول را به صورت افقی بکشید.
        </Text>

        <TableContainer
          overflowX="auto"
          overscrollBehaviorX="contain"
          tabIndex={0}
          aria-label="جدول کاربران؛ برای مشاهده ستون‌های بیشتر به صورت افقی پیمایش کنید"
          sx={{
            WebkitOverflowScrolling: "touch",
            scrollbarGutter: "stable",
          }}
        >
          <Table size="sm" w="full" minW="1500px" sx={{ tableLayout: "fixed", "th, td": { borderBottom: "0 !important", px: 3.5, py: 3, overflow: "hidden" }, "th": { whiteSpace: "nowrap", overflowWrap: "normal", wordBreak: "keep-all", lineHeight: 1.45, fontWeight: 600, color: "var(--panel-text-muted)" } }}>
            <Thead bg="var(--panel-nested)">
              <Tr>
                {!readOnly && <Th w="36px"><Checkbox isChecked={allVisibleSelected} onChange={(event) => toggleAllVisible(event.target.checked)} colorScheme="primary" /></Th>}
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
                <Th w="190px" textAlign="end">عملیات</Th>
              </Tr>
            </Thead>
            <Tbody>
              {users.map((user, index) => {
                const busy = busyUsername === user.username;
                const nextPlan = user.next_plan;
                return (
                  <Tr
                    key={user.username}
                    data-selected={selectedMap.has(user.username) ? "true" : undefined}
                    data-disabled={user.status === "disabled" ? "true" : undefined}
                    transition="opacity .14s ease"
                  >
                    {!readOnly && <Td><Checkbox isChecked={selectedMap.has(user.username)} onChange={(event) => setSelected(user, event.target.checked)} colorScheme="primary" /></Td>}
                    <Td textAlign="center" fontWeight="800">{((filters.offset || 0) + index + 1).toLocaleString("fa-IR")}</Td>
                    <Td>
                      <HStack spacing={2.5}>
                        <Box w="32px" h="32px" display="grid" placeItems="center" borderRadius="full" bg="var(--panel-accent-soft)" color="var(--panel-accent)" fontWeight="900" flexShrink={0}>
                          {user.username.slice(0, 1).toUpperCase()}
                        </Box>
                        <Box minW={0}>
                          <Text dir="ltr" textAlign="start" color="var(--panel-accent)" fontSize="12px" fontWeight="850" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>{user.username}</Text>
                          <Text mt={1} color="var(--panel-text-muted)" fontSize="9px">سقف اتصال: {user.concurrent_user_limit ?? "∞"}</Text>
                        </Box>
                      </HStack>
                    </Td>
                    <Td><StatusPill status={user.status} /></Td>
                    <Td><UsageCell user={user} /></Td>
                    <Td>
                      {nextPlan ? (
                        <Stack spacing={0.5}>
                          <Badge w="fit-content" colorScheme="primary" variant="outline" textTransform="none" fontSize="9px">{nextPlan.data_limit ? String(formatBytes(nextPlan.data_limit)) : "نامحدود"}</Badge>
                          <Text color="var(--panel-text-muted)" fontSize="9px">{nextPlan.expire ? fmtExpire(nextPlan.expire) : "بدون انقضا"}</Text>
                        </Stack>
                      ) : <Text color="var(--panel-text-muted)" fontSize="10px">تنظیم نشده</Text>}
                    </Td>
                    <Td><Text fontSize="11px" fontWeight="700">{fmtExpire(user.expire)}</Text></Td>
                    <Td><Text fontSize="10px" lineHeight="1.6">{fmtDateTime(user.created_at)}</Text></Td>
                    <Td><Text dir="ltr" textAlign="start" fontSize="11px" fontWeight="800" sx={{ unicodeBidi: "isolate" }}>{user.admin?.username || "—"}</Text></Td>
                    <Td>
                      <Text fontSize="10px" lineHeight="1.6">{fmtDateTime(user.online_at)}</Text>
                      <Text mt={1} color={user.online_at ? "var(--panel-success)" : "var(--panel-text-muted)"} fontSize="9px">{user.online_at ? "دارای فعالیت" : "بدون فعالیت ثبت‌شده"}</Text>
                    </Td>
                    <Td>
                      <Tooltip label={user.sub_last_user_agent || "—"} hasArrow>
                        <Text dir="ltr" textAlign="start" fontSize="10px" noOfLines={2} overflowWrap="anywhere" sx={{ unicodeBidi: "isolate" }}>{user.sub_last_user_agent || "—"}</Text>
                      </Tooltip>
                    </Td>
                    <Td>
                      <Text fontSize="12px" fontWeight="850">{(user.reset_history?.length || 0).toLocaleString("fa-IR")}</Text>
                      <Text color="var(--panel-text-muted)" fontSize="9px">مرتبه</Text>
                    </Td>
                    <Td>
                      <Tooltip label={user.note || "—"} hasArrow>
                        <Text fontSize="10px" noOfLines={2} color={user.note ? "var(--panel-text-body)" : "var(--panel-text-muted)"}>{user.note || "—"}</Text>
                      </Tooltip>
                    </Td>
                    <Td textAlign="end">
                      <HStack justify="end" gap={1.5} dir="ltr" maxW="full">
                        <Action label="کپی لینک اشتراک" icon={<CopyIcon />} onClick={() => copySubscription(user)} tone="green" />
                        {!readOnly && isOwner && <UserDeviceLimit user={user} compact />}
                        {!readOnly && <Action label="ویرایش" icon={<EditIcon />} onClick={() => onEditingUser(user)} tone="blue" disabled={busy} />}
                        {!readOnly && <Action label="حذف کاربر" icon={<DeleteIcon />} onClick={() => onDeletingUser(user)} tone="red" disabled={busy} />}
                        <Menu placement="bottom-end" isLazy>
                          <MenuButton
                            as={IconButton}
                            aria-label="عملیات بیشتر"
                            icon={<MoreIcon />}
                            size="xs"
                            minW="32px"
                            w="32px"
                            h="32px"
                            borderRadius="12px"
                            color="var(--panel-text-body)"
                            bg="var(--panel-nested)"
                            borderWidth="1px"
                            borderColor="var(--panel-border)"
                            _hover={{ bg: "var(--panel-row-hover)" }}
                          />
                          <MenuList dir="rtl" minW="210px" bg="var(--panel-surface)" borderColor="var(--panel-border)" borderRadius="14px" boxShadow="var(--shadow-elevated)" py={1.5}>
                            <MenuItem icon={<QRIcon />} onClick={() => { setQRCode(user.links); setSubLink(user.subscription_url); }}>QR Code</MenuItem>
                            <MenuItem icon={<AuditIcon />} onClick={() => navigate(`/audit-logs/?search=${encodeURIComponent(user.username)}`)}>گزارش فعالیت</MenuItem>
                            {!readOnly && <MenuDivider borderColor="var(--panel-border)" />}
                            {!readOnly && <MenuItem icon={<RenewIcon />} isDisabled={busy} onClick={() => { renewalRequest.current = null; setRenewalUser(user); setRenewalPlanId(""); renewalModal.onOpen(); }}>تمدید با پلن</MenuItem>}
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
