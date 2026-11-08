import { EmptyState } from "design-system/Console";
import {
  Badge,
  Box,
  Button,
  Checkbox,
  HStack,
  IconButton,
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
  Text,
  Tooltip,
  chakra,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  ClipboardDocumentIcon,
  DocumentMagnifyingGlassIcon,
  InformationCircleIcon,
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
const InfoIcon = chakra(InformationCircleIcon, { baseStyle: { w: 4, h: 4 } });

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
  if (seconds <= 0) return days <= 1 ? "منقضی" : `${days.toLocaleString("fa-IR")} روز گذشته`;
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
        <Text dir="ltr" textAlign="start" fontSize="xs" fontWeight="700" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>
          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
        </Text>
        <Text flexShrink={0} color={unlimited ? "var(--panel-accent)" : color} fontSize="xs" fontWeight="700">
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
    <HStack w="fit-content" flexShrink={0} spacing={1.5} px={2.5} py={1} borderRadius="full" bg={meta.bg} borderWidth="1px" borderColor={meta.border}>
      <Box boxSize="6px" borderRadius="full" bg={meta.dot} />
      <Text color={meta.color} fontSize="xs" fontWeight="700">{meta.label}</Text>
    </HStack>
  );
};

const Action: FC<{ label: string; shortLabel: string; icon: React.ReactElement; onClick: () => void; tone?: "blue" | "green" | "red" | "gray"; disabled?: boolean; named?: boolean }> = ({ label, shortLabel, icon, onClick, tone = "gray", disabled, named }) => {
  const palettes = {
    gray: { color: "var(--panel-text-body)", bg: "var(--panel-muted-soft)", border: "var(--panel-border)" },
    blue: { color: "var(--panel-accent)", bg: "var(--panel-accent-soft)", border: "var(--panel-accent-border)" },
    green: { color: "var(--panel-success)", bg: "var(--panel-success-soft)", border: "var(--panel-success-border)" },
    red: { color: "var(--panel-danger)", bg: "var(--panel-danger-soft)", border: "var(--panel-danger-border)" },
  } as const;
  const palette = palettes[tone];
  return <Tooltip label={label} hasArrow placement="top" openDelay={250}>
    <Button aria-label={label} className="user-card-action" data-named={named || undefined} size="sm" minW={0} w="full" h="36px" px={1} gap={1} borderRadius="8px" color={palette.color} bg={palette.bg} borderWidth="1px" borderColor={palette.border} isDisabled={disabled} onClick={onClick} _hover={{ borderColor: "var(--panel-border-strong)", bg: palette.bg }}>
      <Box as="span" display="inline-flex" aria-hidden="true">{icon}</Box><Text as="span" className="user-card-action-label" fontSize="xs">{shortLabel}</Text>
    </Button>
  </Tooltip>;
};

export const UsersTablePro: FC = () => {
  const {
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

  const renderUserActions = (user: User, busy: boolean) => (
    <Box className="user-card-actions" role="group" aria-label={`عملیات ${user.username}`} data-read-only={readOnly || undefined}>
      {!readOnly && <Action label="تمدید با پلن" shortLabel="تمدید" icon={<RenewIcon />} onClick={() => openRenewal(user)} tone="green" disabled={busy} named />}
      {!readOnly && <Action label="ویرایش" shortLabel="ویرایش" icon={<EditIcon />} onClick={() => onEditingUser(user)} tone="blue" disabled={busy} named />}
      <Action label="کپی لینک اشتراک" shortLabel="کپی" icon={<CopyIcon />} onClick={() => copySubscription(user)} />
      <Action label="QR Code" shortLabel="QR" icon={<QRIcon />} onClick={() => showQr(user)} />
      <Action label="جزئیات کاربر" shortLabel="جزئیات" icon={<InfoIcon />} onClick={() => setDrawerUsername(user.username)} />
      <Action label="گزارش فعالیت" shortLabel="گزارش" icon={<AuditIcon />} onClick={() => navigate(`/audit-logs/?search=${encodeURIComponent(user.username)}`)} />
      {!readOnly && <Action label={user.status === "disabled" ? "فعال‌سازی" : "غیرفعال‌سازی"} shortLabel={user.status === "disabled" ? "فعال" : "توقف"} icon={user.status === "disabled" ? <PlayActionIcon /> : <PauseActionIcon />} onClick={() => toggleStatus(user)} disabled={busy} />}
      {!readOnly && <Action label="بازنشانی مصرف" shortLabel="ریست" icon={<ResetIcon />} onClick={() => resetUsage(user)} disabled={busy} />}
      {!readOnly && <Action label="ابطال لینک اشتراک" shortLabel="ابطال" icon={<RevokeIcon />} onClick={() => revoke(user)} disabled={busy} />}
      {!readOnly && <Action label="حذف کاربر" shortLabel="حذف" icon={<DeleteIcon />} onClick={() => onDeletingUser(user)} tone="red" disabled={busy} />}
    </Box>
  );

  if (users.length === 0) {
    return (
      <><EmptyState text="کاربری برای نمایش نیست" description="فیلترها را تغییر دهید یا کاربر جدید بسازید." /><Pagination /></>
    );
  }

  return (
    <Box
      dir={i18n.dir()}
      w="full"
      minW={0}
      pb={selectedUsers.length > 0 ? { base: "104px", md: "88px" } : 0}
    >
      <Box mb={readOnly ? 0 : 3}>
        {!readOnly && (
          <Box
            px={{ base: 2, md: 2.5 }}
            borderWidth="1px"
            borderRadius="10px"
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
              <Text pb={2} color="var(--panel-warning)" fontSize="xs">
                انتخاب‌ها بین صفحه‌ها حفظ شده‌اند؛ مجموع انتخاب‌شده: {selectedUsers.length.toLocaleString("fa-IR")}
              </Text>
            )}
          </Box>
        )}

      </Box>
      <Box role="list" aria-label="کارت‌های کاربران" className="user-card-grid">
        {users.map((user) => {
          const busy = busyUsername === user.username;
          const planMeta = plan_meta[user.username] || null;
          const deviceWarned = Boolean(user.device_limit_state && user.device_limit_state.penalty_status !== "clear");
          return <Box as="article" role="listitem" key={user.username} aria-labelledby={`user-card-title-${user.id}`} className="user-card" data-username={user.username} data-selected={selectedMap.has(user.username) || undefined} data-status={user.status}>
            <HStack justify="space-between" align="center" spacing={2} minW={0}>
              <HStack spacing={2} minW={0} flex="1">
                {!readOnly && <Checkbox aria-label={`انتخاب ${user.username}`} colorScheme="primary" isChecked={selectedMap.has(user.username)} onChange={(event) => setSelected(user, event.target.checked)} />}
                <Box aria-hidden="true" boxSize="30px" display="grid" placeItems="center" borderRadius="full" bg="var(--panel-accent-soft)" color="var(--panel-accent)" fontSize="xs" fontWeight="700" flexShrink={0}>{user.username.slice(0, 1).toUpperCase()}</Box>
                <Tooltip label={user.username} hasArrow openDelay={250}>
                  <Button id={`user-card-title-${user.id}`} flex="1" overflow="hidden" variant="link" color="var(--panel-text)" fontSize="sm" fontWeight="700" minW={0} maxW="full" h="auto" justifyContent="start" onClick={() => setDrawerUsername(user.username)}>
                    <Text as="bdi" dir="ltr" noOfLines={1} textAlign="start" sx={{ unicodeBidi: "isolate" }}>{user.username}</Text>
                  </Button>
                </Tooltip>
              </HStack>
              <StatusPill status={user.status} />
            </HStack>
            {user.note && <Text fontSize="xs" color="var(--panel-text-muted)" noOfLines={1} title={user.note} mt={-1}>{user.note}</Text>}
            <Box className="user-card-facts">
              <Box minW={0}><Text className="user-card-label">پلن</Text><HStack spacing={1} flexWrap="wrap" minW={0}><Text fontSize="xs" fontWeight="600" noOfLines={1} title={planMeta ? `${planMeta.plan_name} · نسخه ${planMeta.version_number.toLocaleString("fa-IR")}` : "ساخت سفارشی"}>{planMeta?.plan_name || "سفارشی"}</Text>{planMeta?.is_trial && <Badge colorScheme="yellow" fontSize="xs">آزمایشی</Badge>}</HStack></Box>
              <Box minW={0}><Text className="user-card-label">انقضا</Text><Tooltip label={fmtExpire(user.expire)} hasArrow><Text fontSize="xs" fontWeight="600" color={user.status === "expired" ? "var(--panel-danger)" : undefined} tabIndex={0}>{relativeExpiry(user.expire)}</Text></Tooltip></Box>
              <Box minW={0}><Text className="user-card-label">دستگاه</Text><HStack spacing={1} flexWrap="wrap"><Text dir="ltr" fontSize="xs" fontWeight="600">{user.concurrent_user_limit ?? "∞"}</Text>{deviceWarned && <Badge colorScheme="orange" fontSize="xs">هشدار</Badge>}{!readOnly && isOwner && user.concurrent_user_limit != null && <UserDeviceLimit user={user} compact />}</HStack></Box>
            </Box>
            <UsageCell user={user} />
            <HStack justify="space-between" align="center" spacing={2} minW={0} fontSize="xs" color="var(--panel-text-muted)">
              {isOwner && <Text minW={0} noOfLines={1} title={user.admin?.username || ""}>ادمین: <Box as="bdi" dir="ltr">{user.admin?.username || "—"}</Box></Text>}
              <Tooltip label={fmtDateTime(user.online_at)} hasArrow><Text tabIndex={0} ms={isOwner ? undefined : "auto"}>{relativeActivity(user.online_at)}</Text></Tooltip>
            </HStack>
            {renderUserActions(user, busy)}
          </Box>;
        })}
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
        <ModalOverlay bg="var(--panel-overlay)" />
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
