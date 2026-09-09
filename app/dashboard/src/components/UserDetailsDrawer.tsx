import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Divider,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  HStack,
  Progress,
  SimpleGrid,
  Skeleton,
  Stack,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  Tooltip,
  useToast,
} from "@chakra-ui/react";
import { FC, useEffect, useState } from "react";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { AuditLogList } from "types/Audit";
import { DeviceLimitUserSummary } from "types/DeviceLimit";
import { User, UserPlanMeta } from "types/User";
import { formatBytes } from "utils/formatByte";

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

const statusLabel: Record<User["status"], string> = {
  active: "فعال",
  disabled: "غیرفعال",
  limited: "محدود",
  expired: "منقضی",
  on_hold: "در انتظار",
  error: "خطا",
  connecting: "در اتصال",
  connected: "فعال",
};

const Detail: FC<{ label: string; value: React.ReactNode; dir?: "ltr" | "rtl" }> = ({
  label,
  value,
  dir,
}) => (
  <Box minW={0} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
    <Text color="var(--panel-text-muted)" fontSize="9px" fontWeight="800">{label}</Text>
    <Box mt={1.5} dir={dir} fontSize="12px" fontWeight="750" overflowWrap="anywhere">
      {value}
    </Box>
  </Box>
);

export type UserDetailsDrawerProps = {
  user: User | null;
  planMeta: UserPlanMeta | null;
  isOpen: boolean;
  onClose: () => void;
  readOnly: boolean;
  canViewDevices: boolean;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onRenew: (user: User) => void;
  onToggleStatus: (user: User) => void;
  onResetUsage: (user: User) => void;
  onRevokeSubscription: (user: User) => void;
  onShowQr: (user: User) => void;
};

export const UserDetailsDrawer: FC<UserDetailsDrawerProps> = ({
  user,
  planMeta,
  isOpen,
  onClose,
  readOnly,
  canViewDevices,
  onEdit,
  onDelete,
  onRenew,
  onToggleStatus,
  onResetUsage,
  onRevokeSubscription,
  onShowQr,
}) => {
  const toast = useToast();
  const [tabIndex, setTabIndex] = useState(0);
  const username = user?.username || "";
  const deviceTabIndex = 2;
  const auditTabIndex = canViewDevices && user?.concurrent_user_limit != null ? 3 : 2;

  useEffect(() => {
    if (!isOpen) setTabIndex(0);
  }, [isOpen, username]);

  const devices = useQuery<DeviceLimitUserSummary, Error>(
    ["device-limit-user", username],
    () => fetch(`/device-limit/users/${encodeURIComponent(username)}`),
    {
      enabled:
        isOpen &&
        Boolean(username) &&
        canViewDevices &&
        user?.concurrent_user_limit != null &&
        tabIndex === deviceTabIndex,
      refetchOnWindowFocus: false,
    }
  );

  const audit = useQuery<AuditLogList, Error>(
    ["user-audit-drawer", username],
    () => fetch("/audit-logs", { query: { target: username, offset: 0, limit: 25, sort: "newest" } }),
    {
      enabled: isOpen && Boolean(username) && tabIndex === auditTabIndex,
      refetchOnWindowFocus: false,
    }
  );

  if (!user) return null;

  const used = user.used_traffic ?? 0;
  const unlimited = !user.data_limit;
  const usagePercent = unlimited
    ? 0
    : Math.min(100, Math.max(0, (used / Math.max(user.data_limit || 1, 1)) * 100));
  const usageTone = usagePercent >= 95
    ? "var(--panel-danger)"
    : usagePercent >= 80
    ? "var(--panel-warning)"
    : "var(--panel-success)";

  const copy = async (value: string, success = "کپی شد") => {
    try {
      await navigator.clipboard.writeText(value);
      toast({ title: success, status: "success", duration: 1400 });
    } catch {
      toast({ title: "کپی انجام نشد", status: "error", duration: 2200 });
    }
  };

  const absoluteSubscription = user.subscription_url.startsWith("/")
    ? window.location.origin + user.subscription_url
    : user.subscription_url;

  return (
    <Drawer isOpen={isOpen} placement="end" onClose={onClose} size="lg">
      <DrawerOverlay bg="rgba(0,0,0,.72)" backdropFilter="blur(5px)" />
      <DrawerContent
        dir="rtl"
        bg="var(--panel-surface)"
        color="var(--panel-text)"
        borderInlineStartWidth="1px"
        borderColor="var(--panel-border)"
        boxShadow="-24px 0 70px rgba(0,0,0,.42)"
      >
        <DrawerCloseButton mt={2} />
        <DrawerHeader pe={14} pb={3} borderBottomWidth="1px" borderColor="var(--panel-border)">
          <HStack spacing={3} align="center">
            <Box
              boxSize="42px"
              display="grid"
              placeItems="center"
              borderRadius="full"
              bg="var(--panel-accent-soft)"
              color="var(--panel-accent)"
              fontWeight="900"
            >
              {user.username.slice(0, 1).toUpperCase()}
            </Box>
            <Box minW={0}>
              <Text dir="ltr" textAlign="start" fontSize="lg" fontWeight="900" sx={{ unicodeBidi: "isolate" }}>
                {user.username}
              </Text>
              <HStack mt={1} spacing={2} flexWrap="wrap">
                <Badge colorScheme={user.status === "active" ? "green" : user.status === "expired" ? "red" : "yellow"} textTransform="none">
                  {statusLabel[user.status]}
                </Badge>
                <Text color="var(--panel-text-muted)" fontSize="10px">
                  {planMeta ? `${planMeta.plan_name} · v${planMeta.version_number}` : "بدون پلن"}
                </Text>
              </HStack>
            </Box>
          </HStack>
        </DrawerHeader>

        <DrawerBody p={0} overflow="hidden">
          <Tabs index={tabIndex} onChange={setTabIndex} display="flex" flexDirection="column" h="full" colorScheme="primary" isLazy>
            <TabList px={4} pt={2} overflowX="auto" borderColor="var(--panel-border)">
              <Tab fontSize="11px" whiteSpace="nowrap">نمای کلی</Tab>
              <Tab fontSize="11px" whiteSpace="nowrap">اشتراک</Tab>
              {canViewDevices && user.concurrent_user_limit != null && (
                <Tab fontSize="11px" whiteSpace="nowrap">دستگاه‌ها</Tab>
              )}
              <Tab fontSize="11px" whiteSpace="nowrap">فعالیت</Tab>
            </TabList>
            <TabPanels flex="1" overflowY="auto">
              <TabPanel p={{ base: 3, md: 4 }}>
                <Stack spacing={4}>
                  <SimpleGrid columns={{ base: 1, sm: 2 }} gap={2.5}>
                    <Detail label="ادمین" value={user.admin?.username || "—"} dir="ltr" />
                    <Detail label="پلن فعلی" value={planMeta ? `${planMeta.plan_name} · v${planMeta.version_number}${planMeta.is_trial ? " · آزمایشی" : ""}` : "بدون پلن"} />
                    <Detail label="تاریخ ایجاد" value={fmtDateTime(user.created_at)} />
                    <Detail label="آخرین فعالیت" value={fmtDateTime(user.online_at)} />
                    <Detail label="انقضا" value={fmtExpire(user.expire)} />
                    <Detail label="سقف دستگاه" value={user.concurrent_user_limit ?? "نامحدود"} />
                  </SimpleGrid>

                  <Box p={3.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                    <HStack justify="space-between" align="end">
                      <Box>
                        <Text color="var(--panel-text-muted)" fontSize="9px" fontWeight="800">مصرف ترافیک</Text>
                        <Text dir="ltr" mt={1} fontSize="13px" fontWeight="900" sx={{ unicodeBidi: "isolate" }}>
                          {String(formatBytes(used))} / {user.data_limit ? String(formatBytes(user.data_limit)) : "∞"}
                        </Text>
                      </Box>
                      <Text color={usageTone} fontSize="11px" fontWeight="900">{unlimited ? "∞" : `${Math.round(usagePercent)}٪`}</Text>
                    </HStack>
                    {!unlimited && <Progress mt={2.5} value={usagePercent} h="5px" borderRadius="full" bg="var(--panel-surface)" sx={{ "& > div": { background: usageTone } }} />}
                  </Box>

                  <Box p={3.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                    <Text color="var(--panel-text-muted)" fontSize="9px" fontWeight="800">توضیحات</Text>
                    <Text mt={2} fontSize="12px" lineHeight="1.9" whiteSpace="pre-wrap">{user.note || "توضیحی ثبت نشده است."}</Text>
                  </Box>

                  <SimpleGrid columns={{ base: 1, sm: 2 }} gap={2.5}>
                    <Detail label="User-Agent آخر" value={user.sub_last_user_agent || "—"} dir="ltr" />
                    <Detail label="دفعات بازنشانی مصرف" value={(user.reset_history?.length || 0).toLocaleString("fa-IR")} />
                  </SimpleGrid>

                  {user.next_plan && (
                    <Box p={3.5} borderWidth="1px" borderColor="var(--panel-accent-border)" borderRadius="12px" bg="var(--panel-accent-soft)">
                      <Text color="var(--panel-accent)" fontSize="10px" fontWeight="900">پلن بعدی تنظیم‌شده</Text>
                      <Text mt={1.5} fontSize="11px">
                        حجم: {user.next_plan.data_limit ? String(formatBytes(user.next_plan.data_limit)) : "نامحدود"} · انقضا: {fmtExpire(user.next_plan.expire)}
                      </Text>
                    </Box>
                  )}
                </Stack>
              </TabPanel>

              <TabPanel p={{ base: 3, md: 4 }}>
                <Stack spacing={4}>
                  <Box p={3.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                    <Text color="var(--panel-text-muted)" fontSize="9px" fontWeight="800">لینک اشتراک</Text>
                    <Tooltip label={absoluteSubscription} hasArrow>
                      <Text dir="ltr" textAlign="start" mt={2} fontFamily="mono" fontSize="10px" noOfLines={2} overflowWrap="anywhere" sx={{ unicodeBidi: "isolate" }}>
                        {absoluteSubscription}
                      </Text>
                    </Tooltip>
                    <HStack mt={3} spacing={2} flexWrap="wrap">
                      <Button size="sm" onClick={() => copy(absoluteSubscription, "لینک اشتراک کپی شد")}>کپی لینک</Button>
                      <Button size="sm" variant="outline" borderColor="var(--panel-border)" onClick={() => onShowQr(user)}>نمایش QR</Button>
                      {!readOnly && (
                        <Button size="sm" variant="outline" color="var(--panel-warning)" borderColor="var(--panel-warning-border)" onClick={() => onRevokeSubscription(user)}>
                          ابطال لینک
                        </Button>
                      )}
                    </HStack>
                  </Box>

                  <Box>
                    <Text fontSize="11px" fontWeight="900">لینک‌های اتصال</Text>
                    <Stack mt={2.5} spacing={2}>
                      {user.links.length === 0 && <Text color="var(--panel-text-muted)" fontSize="11px">لینکی موجود نیست.</Text>}
                      {user.links.map((link, index) => (
                        <HStack key={`${index}-${link.slice(0, 12)}`} p={2.5} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" bg="var(--panel-nested)" align="center">
                          <Text flex="1" minW={0} dir="ltr" textAlign="start" fontFamily="mono" fontSize="9px" noOfLines={1} sx={{ unicodeBidi: "isolate" }}>{link}</Text>
                          <Button size="xs" variant="ghost" onClick={() => copy(link)}>کپی</Button>
                        </HStack>
                      ))}
                    </Stack>
                  </Box>
                </Stack>
              </TabPanel>

              {canViewDevices && user.concurrent_user_limit != null && (
                <TabPanel p={{ base: 3, md: 4 }}>
                  {devices.isLoading && (
                    <Stack>{Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} h="92px" borderRadius="12px" />)}</Stack>
                  )}
                  {devices.isError && <Alert status="error" borderRadius="10px"><AlertIcon />دریافت اطلاعات دستگاه‌ها انجام نشد.</Alert>}
                  {devices.data && (
                    <Stack spacing={4}>
                      <SimpleGrid columns={{ base: 2, sm: 4 }} gap={2}>
                        <Detail label="سقف" value={devices.data.configured_limit ?? "∞"} />
                        <Detail label="اتصال زنده" value={devices.data.live_active_ip_count.toLocaleString("fa-IR")} />
                        <Detail label="اخطارها" value={devices.data.state.violation_count.toLocaleString("fa-IR")} />
                        <Detail label="اسلات‌ها" value={devices.data.slots.length.toLocaleString("fa-IR")} />
                      </SimpleGrid>
                      {devices.data.state.last_reason && (
                        <Alert status="warning" borderRadius="10px"><AlertIcon /><Text fontSize="11px">{devices.data.state.last_reason}</Text></Alert>
                      )}
                      <Box>
                        <Text fontSize="11px" fontWeight="900">دستگاه‌های ثبت‌شده</Text>
                        <Stack mt={2.5} spacing={2}>
                          {devices.data.slots.length === 0 && <Text color="var(--panel-text-muted)" fontSize="11px">اسلات فعالی ثبت نشده است.</Text>}
                          {devices.data.slots.map((slot) => (
                            <Box key={slot.id} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="11px" bg="var(--panel-nested)">
                              <HStack justify="space-between" align="start">
                                <Box minW={0}>
                                  <Text fontSize="11px" fontWeight="850">{slot.label || `دستگاه ${slot.slot_index.toLocaleString("fa-IR")}`}</Text>
                                  <Text dir="ltr" textAlign="start" mt={1} color="var(--panel-text-muted)" fontSize="9px" sx={{ unicodeBidi: "isolate" }}>{slot.last_ip || "—"}</Text>
                                </Box>
                                <Text color="var(--panel-text-muted)" fontSize="9px">{fmtDateTime(slot.last_seen_at)}</Text>
                              </HStack>
                              {slot.client_observations[0] && (
                                <Text mt={2} dir="ltr" textAlign="start" color="var(--panel-text-body)" fontSize="9px" sx={{ unicodeBidi: "isolate" }}>
                                  {slot.client_observations[0].client_name} {slot.client_observations[0].client_version || ""} · {slot.client_observations[0].platform || slot.client_observations[0].os_token || "—"}
                                </Text>
                              )}
                            </Box>
                          ))}
                        </Stack>
                      </Box>
                    </Stack>
                  )}
                </TabPanel>
              )}

              <TabPanel p={{ base: 3, md: 4 }}>
                <Stack spacing={3}>
                  <SimpleGrid columns={{ base: 1, sm: 2 }} gap={2.5}>
                    <Detail label="آخرین فعالیت کاربر" value={fmtDateTime(user.online_at)} />
                    <Detail label="آخرین دریافت اشتراک" value={fmtDateTime(user.sub_updated_at)} />
                  </SimpleGrid>
                  <Divider borderColor="var(--panel-border)" />
                  <Text fontSize="11px" fontWeight="900">گزارش فعالیت مدیریتی</Text>
                  {audit.isLoading && <Stack>{Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} h="64px" borderRadius="10px" />)}</Stack>}
                  {audit.isError && <Alert status="error" borderRadius="10px"><AlertIcon />دریافت گزارش فعالیت انجام نشد.</Alert>}
                  {audit.data?.logs.length === 0 && <Text color="var(--panel-text-muted)" fontSize="11px">فعالیت مدیریتی برای این کاربر ثبت نشده است.</Text>}
                  {audit.data?.logs.map((log) => (
                    <Box key={log.id} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="11px" bg="var(--panel-nested)">
                      <HStack justify="space-between" align="start" gap={3}>
                        <Box minW={0}>
                          <Text dir="ltr" textAlign="start" color="var(--panel-accent)" fontSize="9px" fontWeight="850" sx={{ unicodeBidi: "isolate" }}>{log.action}</Text>
                          <Text mt={1} fontSize="10px" lineHeight="1.8">{log.description}</Text>
                          <Text mt={1} color="var(--panel-text-muted)" fontSize="9px">توسط {log.admin_username}</Text>
                        </Box>
                        <Text flexShrink={0} color="var(--panel-text-muted)" fontSize="9px">{fmtDateTime(log.created_at)}</Text>
                      </HStack>
                    </Box>
                  ))}
                </Stack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </DrawerBody>

        <DrawerFooter borderTopWidth="1px" borderColor="var(--panel-border)" gap={2} flexWrap="wrap">
          {!readOnly && <Button size="sm" colorScheme="primary" color="var(--panel-accent-contrast)" onClick={() => onEdit(user)}>ویرایش</Button>}
          {!readOnly && <Button size="sm" variant="outline" borderColor="var(--panel-border)" onClick={() => onRenew(user)}>تمدید با پلن</Button>}
          {!readOnly && <Button size="sm" variant="ghost" onClick={() => onToggleStatus(user)}>{user.status === "disabled" ? "فعال‌سازی" : "غیرفعال‌سازی"}</Button>}
          {!readOnly && <Button size="sm" variant="ghost" onClick={() => onResetUsage(user)}>بازنشانی مصرف</Button>}
          {!readOnly && <Button size="sm" variant="ghost" color="var(--panel-danger)" onClick={() => onDelete(user)}>حذف</Button>}
          <Button size="sm" variant="ghost" ms="auto" onClick={onClose}>بستن</Button>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
};

export default UserDetailsDrawer;
