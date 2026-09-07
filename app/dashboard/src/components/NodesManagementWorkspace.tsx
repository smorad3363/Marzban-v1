import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Collapse,
  FormControl,
  FormLabel,
  Grid,
  HStack,
  IconButton,
  Input,
  Select,
  Skeleton,
  Stack,
  Switch,
  Text,
  Textarea,
  Tooltip,
  VStack,
  useToast,
} from "@chakra-ui/react";
import {
  ArrowPathIcon,
  EyeIcon,
  EyeSlashIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  FetchNodesQueryKey,
  getNodeDefaultValues,
  NodeSchema,
  NodeType,
  NodeWatchdogSettings,
  useNodes,
  useNodesQuery,
} from "contexts/NodesContext";
import { FC, useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { Status } from "types/User";
import {
  generateErrorMessage,
  generateSuccessMessage,
} from "utils/toastHandler";
import { NodeModalStatusBadge } from "./NodeModalStatusBadge";

type NodeBandwidthEntry = {
  node_id: number | null;
  node_name: string;
  state: "online" | "warming_up" | "stale" | "offline" | string;
  sampled_at: string | null;
  sample_age_seconds: number | null;
  uplink_bps: number;
  downlink_bps: number;
  total_bps: number;
  peak_5m_uplink_bps: number;
  peak_5m_downlink_bps: number;
};

type BandwidthResponse = {
  nodes: NodeBandwidthEntry[];
  total_uplink_bps: number;
  total_downlink_bps: number;
  total_bps: number;
  online_nodes: number;
  total_nodes: number;
};

type NodeRow = {
  key: string;
  name: string;
  node: NodeType | null;
  bandwidth?: NodeBandwidthEntry;
  status: Status;
  editable: boolean;
};

type StatusFilter = "all" | "connected" | "connecting" | "disabled" | "error";

const formatRate = (value?: number | null) => {
  const safe = Number.isFinite(value) && Number(value) > 0 ? Number(value) : 0;
  const units = ["bps", "Kbps", "Mbps", "Gbps", "Tbps"];
  let amount = safe;
  let unit = 0;
  while (amount >= 1000 && unit < units.length - 1) {
    amount /= 1000;
    unit += 1;
  }
  return `${new Intl.NumberFormat("fa-IR", {
    maximumFractionDigits: unit === 0 ? 0 : 1,
  }).format(amount)} ${units[unit]}`;
};

const bandwidthStateToStatus = (state?: string): Status => {
  if (state === "online") return "connected";
  if (state === "warming_up") return "connecting";
  return "error";
};

const sampleAgeLabel = (age?: number | null) => {
  if (age == null || !Number.isFinite(age)) return "بدون نمونه";
  if (age < 60) {
    return `${new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(age)} ثانیه پیش`;
  }
  const minutes = age / 60;
  if (minutes < 60) {
    return `${new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(minutes)} دقیقه پیش`;
  }
  return `${new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(minutes / 60)} ساعت پیش`;
};

const sampledAtLabel = (value?: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fa-IR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const Sparkline: FC<{ values: number[] }> = ({ values }) => {
  const normalized = values.length > 1 ? values : [0, ...(values.length ? values : [0])];
  const max = Math.max(...normalized, 1);
  const min = Math.min(...normalized, 0);
  const spread = Math.max(max - min, 1);
  const points = normalized
    .map((value, index) => {
      const x = normalized.length === 1 ? 50 : (index / (normalized.length - 1)) * 100;
      const y = 30 - ((value - min) / spread) * 24;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 32" width="100%" height="34" role="img" aria-label="روند زنده ترافیک">
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

const SummaryCard: FC<{
  label: string;
  value: string;
  hint?: string;
  accent?: string;
}> = ({ label, value, hint, accent = "var(--panel-accent)" }) => (
  <Box
    minW={0}
    p={3}
    borderWidth="1px"
    borderColor="var(--panel-border)"
    borderRadius="12px"
    bg="var(--panel-nested)"
  >
    <HStack justify="space-between" align="start" spacing={3}>
      <Box minW={0}>
        <Text fontSize="xs" color="var(--panel-text-muted)" fontWeight="700">
          {label}
        </Text>
        <Text mt={1} fontSize={{ base: "lg", md: "xl" }} fontWeight="900" dir="ltr" textAlign="start">
          {value}
        </Text>
        {hint && (
          <Text mt={1} fontSize="xs" color="var(--panel-text-muted)" noOfLines={1}>
            {hint}
          </Text>
        )}
      </Box>
      <Box mt={1} boxSize="9px" borderRadius="full" bg={accent} boxShadow={`0 0 14px ${accent}`} />
    </HStack>
  </Box>
);

const WatchdogPanel: FC = () => {
  const toast = useToast();
  const [expanded, setExpanded] = useState(false);
  const [settings, setSettings] = useState<NodeWatchdogSettings | null>(null);
  const [token, setToken] = useState("");
  const query = useQuery<NodeWatchdogSettings>({
    queryKey: "node-watchdog-settings",
    queryFn: () => fetch("/node/watchdog/settings"),
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (query.data) setSettings(query.data);
  }, [query.data]);

  const save = useMutation(
    () =>
      fetch<NodeWatchdogSettings>("/node/watchdog/settings", {
        method: "PUT",
        body: {
          ...settings,
          telegram_bot_token: token || undefined,
        },
      }),
    {
      onSuccess: (value) => {
        setSettings(value);
        setToken("");
        generateSuccessMessage("تنظیمات نگهبان نودها ذخیره شد", toast);
      },
      onError: (error) => {
        generateErrorMessage(error, toast);
      },
    }
  );

  const test = useMutation(() => fetch("/node/watchdog/test", { method: "POST" }), {
    onSuccess: () => {
      generateSuccessMessage("پیام آزمایشی نگهبان ارسال شد", toast);
    },
    onError: (error) => {
        generateErrorMessage(error, toast);
      },
  });

  const setNumber = (key: keyof NodeWatchdogSettings, value: string) => {
    const parsed = Number(value);
    setSettings((current) =>
      current && Number.isFinite(parsed) ? { ...current, [key]: parsed } : current
    );
  };

  return (
    <Box mt={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" overflow="hidden">
      <Button
        w="full"
        variant="ghost"
        borderRadius="0"
        justifyContent="space-between"
        px={3}
        py={5}
        onClick={() => setExpanded((value) => !value)}
      >
        <Box textAlign="start">
          <Text fontSize="sm" fontWeight="800">نگهبان نودها</Text>
          <Text fontSize="xs" color="var(--panel-text-muted)">هشدار قطعی و اعلان تلگرام</Text>
        </Box>
        <Badge colorScheme={settings?.enabled ? "green" : "gray"}>
          {settings?.enabled ? "فعال" : "غیرفعال"}
        </Badge>
      </Button>
      <Collapse in={expanded} animateOpacity>
        <Box p={3} pt={1}>
          {query.isLoading || !settings ? (
            <Skeleton height="130px" borderRadius="10px" />
          ) : (
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Box>
                  <Text fontSize="sm" fontWeight="700">فعال‌سازی نگهبان</Text>
                  <Text fontSize="xs" color="var(--panel-text-muted)">پایش قطعی نودها و اعلان رخدادها</Text>
                </Box>
                <Switch
                  colorScheme="green"
                  isChecked={settings.enabled}
                  onChange={(event) => setSettings({ ...settings, enabled: event.target.checked })}
                />
              </HStack>
              <Input
                size="sm"
                type="password"
                placeholder={settings.telegram_bot_token_configured ? "توکن تنظیم شده است" : "Telegram bot token"}
                value={token}
                onChange={(event) => setToken(event.target.value)}
              />
              <Input
                size="sm"
                placeholder="Telegram chat id"
                value={settings.telegram_chat_id || ""}
                onChange={(event) => setSettings({ ...settings, telegram_chat_id: event.target.value })}
              />
              <Grid templateColumns={{ base: "1fr", sm: "repeat(3, 1fr)" }} gap={2}>
                <FormControl>
                  <FormLabel fontSize="xs">بازه بررسی</FormLabel>
                  <Input size="sm" type="number" value={settings.check_interval} onChange={(event) => setNumber("check_interval", event.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="xs">حد backoff</FormLabel>
                  <Input size="sm" type="number" value={settings.backoff_cap} onChange={(event) => setNumber("backoff_cap", event.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="xs">یادآوری</FormLabel>
                  <Input size="sm" type="number" value={settings.remind_every} onChange={(event) => setNumber("remind_every", event.target.value)} />
                </FormControl>
              </Grid>
              <HStack>
                <Button flex="1" size="sm" variant="outline" onClick={() => test.mutate()} isLoading={test.isLoading}>ارسال تست</Button>
                <Button flex="1" size="sm" colorScheme="primary" onClick={() => save.mutate()} isLoading={save.isLoading}>ذخیره نگهبان</Button>
              </HStack>
            </VStack>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

const NodeEditor: FC<{
  node: NodeType | null;
  bandwidth?: NodeBandwidthEntry;
  isNew: boolean;
  onSaved: () => void;
}> = ({ node, bandwidth, isNew, onSaved }) => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { addNode, updateNode, reconnectNode, setDeletingNode } = useNodes();
  const [showCertificate, setShowCertificate] = useState(false);
  const form = useForm<NodeType>({
    resolver: zodResolver(NodeSchema),
    defaultValues: isNew
      ? { ...getNodeDefaultValues(), add_as_new_host: false }
      : node || getNodeDefaultValues(),
  });

  useEffect(() => {
    form.reset(
      isNew
        ? { ...getNodeDefaultValues(), add_as_new_host: false }
        : node || getNodeDefaultValues()
    );
  }, [form, isNew, node]);

  const nodeSettings = useQuery<{ min_node_version: string; certificate: string }>({
    queryKey: "node-settings",
    queryFn: () => fetch("/node/settings"),
    refetchOnWindowFocus: false,
  });

  const certificateUrl = useMemo(() => {
    if (!nodeSettings.data?.certificate) return null;
    return URL.createObjectURL(new Blob([nodeSettings.data.certificate], { type: "text/plain" }));
  }, [nodeSettings.data?.certificate]);

  useEffect(() => {
    return () => {
      if (certificateUrl) URL.revokeObjectURL(certificateUrl);
    };
  }, [certificateUrl]);

  const normalize = (value: NodeType): NodeType => {
    const normalized: NodeType = { ...value };
    if (normalized.ip_source_mode === "direct") {
      normalized.cdn_provider = null;
      normalized.trusted_proxy_cidrs = [];
    } else if (normalized.ip_source_mode === "proxy_protocol") {
      normalized.cdn_provider = null;
    }
    return normalized;
  };

  const saveNode = useMutation(
    (value: NodeType) => (isNew ? addNode(normalize(value)) : updateNode(normalize(value))),
    {
      onSuccess: () => {
        generateSuccessMessage(isNew ? "نود با موفقیت اضافه شد" : "تغییرات نود ذخیره شد", toast);
        queryClient.invalidateQueries(FetchNodesQueryKey);
        queryClient.invalidateQueries(["nodes-live-bandwidth"]);
        onSaved();
      },
      onError: (error) => {
        generateErrorMessage(error, toast, form);
      },
    }
  );

  const reconnect = useMutation(
    () => (node ? reconnectNode(node) : Promise.resolve()),
    {
      onSuccess: () => {
        generateSuccessMessage("درخواست اتصال مجدد ارسال شد", toast);
        queryClient.invalidateQueries(FetchNodesQueryKey);
      },
      onError: (error) => {
        generateErrorMessage(error, toast);
      },
    }
  );

  const ipSourceMode = form.watch("ip_source_mode") || "direct";
  const cdnProvider = form.watch("cdn_provider");
  const nodeStatus: Status = node?.status || bandwidthStateToStatus(bandwidth?.state);

  const selectCertificate = (target: HTMLElement) => {
    const selection = window.getSelection();
    if (!selection) return;
    const range = document.createRange();
    range.selectNodeContents(target);
    selection.removeAllRanges();
    selection.addRange(range);
  };

  return (
    <Box
      borderWidth="1px"
      borderColor="var(--panel-border)"
      borderRadius="14px"
      bg="var(--panel-surface)"
      overflow="hidden"
      position={{ xl: "sticky" }}
      top={{ xl: 0 }}
    >
      <Box p={4} borderBottomWidth="1px" borderColor="var(--panel-border)">
        <HStack justify="space-between" align="start" gap={3}>
          <Box minW={0}>
            <Text fontSize="xs" color="var(--panel-accent)" fontWeight="800">جزئیات نود</Text>
            <HStack mt={1} spacing={2}>
              <Text fontSize="lg" fontWeight="900" noOfLines={1} dir="ltr">{isNew ? "نود جدید" : node?.name || "—"}</Text>
              {!isNew && <NodeModalStatusBadge status={nodeStatus} compact />}
            </HStack>
            {!isNew && bandwidth && (
              <Text mt={1} fontSize="xs" color="var(--panel-text-muted)">
                آخرین نمونه: {sampleAgeLabel(bandwidth.sample_age_seconds)}
              </Text>
            )}
          </Box>
          {!isNew && node?.xray_version && (
            <Badge colorScheme="primary" borderRadius="full" px={2} py={1}>Xray {node.xray_version}</Badge>
          )}
        </HStack>
      </Box>

      <Box p={4} maxH={{ base: "none", xl: "calc(100vh - 245px)" }} overflowY={{ xl: "auto" }}>
        {!isNew && nodeStatus === "error" && (
          <Alert status="error" mb={4} borderRadius="10px" alignItems="start">
            <AlertIcon mt={0.5} />
            <Box>
              <Text fontSize="sm" fontWeight="800">خطا در اتصال نود</Text>
              <Text mt={1} fontSize="xs">{node?.message || "اتصال با نود برقرار نیست."}</Text>
            </Box>
          </Alert>
        )}

        {nodeSettings.data?.certificate && (
          <Alert status="info" mb={4} borderRadius="10px" alignItems="start">
            <AlertDescription w="full" overflow="hidden">
              <Text fontSize="sm" fontWeight="700">این گواهی را روی نود نصب کنید تا اتصال امن با سرور کنترل برقرار شود.</Text>
              <HStack mt={2} justify="flex-end">
                <Tooltip label={showCertificate ? "پنهان کردن گواهی" : "نمایش گواهی"}>
                  <IconButton
                    aria-label={showCertificate ? "پنهان کردن گواهی" : "نمایش گواهی"}
                    size="xs"
                    variant="ghost"
                    onClick={() => setShowCertificate((value) => !value)}
                    icon={showCertificate ? <EyeSlashIcon width={16} /> : <EyeIcon width={16} />}
                  />
                </Tooltip>
                {certificateUrl && (
                  <Button as="a" href={certificateUrl} download="ssl_client_cert.pem" size="xs" colorScheme="primary">دانلود گواهی</Button>
                )}
              </HStack>
              <Collapse in={showCertificate} animateOpacity>
                <Text
                  mt={2}
                  p={2}
                  borderRadius="8px"
                  bg="blackAlpha.300"
                  fontFamily="mono"
                  fontSize="10px"
                  whiteSpace="pre"
                  overflow="auto"
                  dir="ltr"
                  textAlign="left"
                  cursor="text"
                  onClick={(event) => selectCertificate(event.currentTarget)}
                >
                  {nodeSettings.data.certificate}
                </Text>
              </Collapse>
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={form.handleSubmit((value) => saveNode.mutate(value))}>
          <VStack align="stretch" spacing={3}>
            <HStack align="end" spacing={2}>
              <FormControl isInvalid={Boolean(form.formState.errors.name)}>
                <FormLabel fontSize="sm">نام</FormLabel>
                <Input size="sm" placeholder="Edge-Node-2" {...form.register("name")} />
              </FormControl>
              {!isNew && (
                <Controller
                  name="status"
                  control={form.control}
                  render={({ field }) => (
                    <Tooltip label={field.value === "disabled" ? "فعال کردن نود" : "غیرفعال کردن نود"}>
                      <Box pb={1}>
                        <Switch
                          colorScheme="green"
                          isChecked={field.value !== "disabled"}
                          onChange={(event) => field.onChange(event.target.checked ? "connecting" : "disabled")}
                        />
                      </Box>
                    </Tooltip>
                  )}
                />
              )}
            </HStack>

            <FormControl isInvalid={Boolean(form.formState.errors.address)}>
              <FormLabel fontSize="sm">آدرس</FormLabel>
              <Input size="sm" dir="ltr" textAlign="left" placeholder="51.20.12.13" {...form.register("address")} />
            </FormControl>

            <Grid templateColumns={{ base: "1fr", sm: "repeat(3, 1fr)" }} gap={2}>
              <FormControl>
                <FormLabel fontSize="sm">پورت</FormLabel>
                <Input size="sm" type="number" dir="ltr" {...form.register("port")} />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">پورت API</FormLabel>
                <Input size="sm" type="number" dir="ltr" {...form.register("api_port")} />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">ضریب گره</FormLabel>
                <Input size="sm" type="number" step="0.1" dir="ltr" {...form.register("usage_coefficient")} />
              </FormControl>
            </Grid>

            <Box borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" p={3} bg="var(--panel-nested)">
              <VStack align="stretch" spacing={3}>
                <FormControl>
                  <FormLabel fontSize="sm">منبع تشخیص IP کاربر</FormLabel>
                  <Controller
                    name="ip_source_mode"
                    control={form.control}
                    render={({ field }) => (
                      <Select size="sm" value={field.value || "direct"} onChange={field.onChange}>
                        <option value="direct">اتصال مستقیم</option>
                        <option value="trusted_xff">هدر X-Forwarded-For مورد اعتماد</option>
                        <option value="proxy_protocol">Proxy Protocol</option>
                      </Select>
                    )}
                  />
                  <Text mt={1} fontSize="xs" color="var(--panel-text-muted)">
                    مشخص کنید این نود IP واقعی کاربر را مستقیم می‌بیند یا پشت CDN / پراکسی مورد اعتماد قرار دارد.
                  </Text>
                </FormControl>

                {ipSourceMode === "trusted_xff" && (
                  <FormControl>
                    <FormLabel fontSize="sm">ارائه‌دهنده CDN</FormLabel>
                    <Controller
                      name="cdn_provider"
                      control={form.control}
                      render={({ field }) => (
                        <Select size="sm" value={field.value || ""} onChange={(event) => field.onChange(event.target.value || null)}>
                          <option value="">انتخاب کنید</option>
                          <option value="cloudflare">Cloudflare</option>
                          <option value="custom">پراکسی سفارشی</option>
                        </Select>
                      )}
                    />
                  </FormControl>
                )}

                {(ipSourceMode === "proxy_protocol" || (ipSourceMode === "trusted_xff" && cdnProvider === "custom")) && (
                  <FormControl>
                    <FormLabel fontSize="sm">CIDR پراکسی‌های مورد اعتماد</FormLabel>
                    <Controller
                      name="trusted_proxy_cidrs"
                      control={form.control}
                      render={({ field }) => (
                        <Textarea
                          size="sm"
                          rows={3}
                          dir="ltr"
                          textAlign="left"
                          value={(field.value || []).join("\n")}
                          onChange={(event) =>
                            field.onChange(
                              event.target.value
                                .split(/[\n,]+/)
                                .map((value) => value.trim())
                                .filter(Boolean)
                            )
                          }
                          placeholder={"173.245.48.0/20\n2400:cb00::/32"}
                        />
                      )}
                    />
                  </FormControl>
                )}

                {ipSourceMode !== "direct" && (
                  <Alert status="warning" borderRadius="8px" alignItems="start">
                    <AlertIcon mt={0.5} />
                    <Text fontSize="xs">تنظیمات منبع IP فقط باید برای پراکسی‌های کاملاً مورد اعتماد فعال شود.</Text>
                  </Alert>
                )}
              </VStack>
            </Box>

            {isNew && (
              <Checkbox {...form.register("add_as_new_host")}>برای همه inboundها هاست جدید ساخته شود</Checkbox>
            )}

            <Controller
              name="watchdog_enabled"
              control={form.control}
              render={({ field }) => (
                <HStack justify="space-between" p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">
                  <Box>
                    <Text fontSize="sm" fontWeight="700">پایش این نود</Text>
                    <Text fontSize="xs" color="var(--panel-text-muted)">قطعی این نود توسط نگهبان بررسی شود.</Text>
                  </Box>
                  <Switch colorScheme="green" isChecked={field.value !== false} onChange={field.onChange} />
                </HStack>
              )}
            />

            <HStack pt={1} flexWrap="wrap">
              {!isNew && node && (
                <>
                  <Button
                    size="sm"
                    colorScheme="red"
                    variant="outline"
                    leftIcon={<TrashIcon width={16} />}
                    onClick={() => setDeletingNode(node)}
                  >
                    حذف
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<ArrowPathIcon width={16} />}
                    onClick={() => reconnect.mutate()}
                    isLoading={reconnect.isLoading}
                  >
                    اتصال مجدد
                  </Button>
                </>
              )}
              <Button flex="1" minW="150px" type="submit" size="sm" colorScheme="primary" isLoading={saveNode.isLoading}>
                {isNew ? "افزودن نود" : "ذخیره تغییرات"}
              </Button>
            </HStack>
          </VStack>
        </form>
      </Box>
    </Box>
  );
};

export const NodesManagementWorkspace: FC = () => {
  const { data: nodes, isLoading } = useNodesQuery();
  const bandwidth = useQuery<BandwidthResponse>({
    queryKey: ["nodes-live-bandwidth"],
    queryFn: () => fetch("/nodes/bandwidth"),
    refetchInterval: 5_000,
    refetchOnWindowFocus: false,
    staleTime: 3_000,
  });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [history, setHistory] = useState<Record<string, number[]>>({});

  useEffect(() => {
    if (!bandwidth.data?.nodes) return;
    setHistory((current) => {
      const next = { ...current };
      bandwidth.data!.nodes.forEach((item) => {
        const key = item.node_id == null ? "master" : String(item.node_id);
        next[key] = [...(next[key] || []), item.total_bps].slice(-24);
      });
      return next;
    });
  }, [bandwidth.data]);

  const rows = useMemo<NodeRow[]>(() => {
    const bandwidthById = new Map<string, NodeBandwidthEntry>();
    (bandwidth.data?.nodes || []).forEach((item) => {
      bandwidthById.set(item.node_id == null ? "master" : String(item.node_id), item);
    });

    const result: NodeRow[] = [];
    const masterBandwidth = bandwidthById.get("master");
    if (masterBandwidth) {
      result.push({
        key: "master",
        name: masterBandwidth.node_name || "Master",
        node: null,
        bandwidth: masterBandwidth,
        status: bandwidthStateToStatus(masterBandwidth.state),
        editable: false,
      });
    }

    (nodes || []).forEach((node) => {
      const key = String(node.id);
      const nodeBandwidth = bandwidthById.get(key);
      result.push({
        key,
        name: node.name,
        node,
        bandwidth: nodeBandwidth,
        status: node.status || bandwidthStateToStatus(nodeBandwidth?.state),
        editable: true,
      });
    });
    return result;
  }, [bandwidth.data?.nodes, nodes]);

  useEffect(() => {
    if (selectedKey === "new") return;
    if (selectedKey && rows.some((row) => row.key === selectedKey)) return;
    const firstEditable = rows.find((row) => row.editable);
    setSelectedKey(firstEditable?.key || rows[0]?.key || null);
  }, [rows, selectedKey]);

  const counts = useMemo(() => {
    return rows.reduce(
      (acc, row) => {
        acc.all += 1;
        if (row.status === "connected") acc.connected += 1;
        else if (row.status === "connecting") acc.connecting += 1;
        else if (row.status === "disabled") acc.disabled += 1;
        else acc.error += 1;
        return acc;
      },
      { all: 0, connected: 0, connecting: 0, disabled: 0, error: 0 }
    );
  }, [rows]);

  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesSearch =
        !needle ||
        row.name.toLowerCase().includes(needle) ||
        row.node?.address?.toLowerCase().includes(needle);
      const matchesStatus = statusFilter === "all" || row.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [rows, search, statusFilter]);

  useEffect(() => setPage(1), [search, statusFilter, pageSize]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const visibleRows = filteredRows.slice((safePage - 1) * pageSize, safePage * pageSize);
  const selected = selectedKey === "new" ? null : rows.find((row) => row.key === selectedKey) || null;

  const filterButtons: Array<{ key: StatusFilter; label: string; scheme: string; count: number }> = [
    { key: "all", label: "همه", scheme: "primary", count: counts.all },
    { key: "connected", label: "زنده", scheme: "green", count: counts.connected },
    { key: "connecting", label: "در حال اتصال", scheme: "yellow", count: counts.connecting },
    { key: "disabled", label: "غیرفعال", scheme: "gray", count: counts.disabled },
    { key: "error", label: "خطادار", scheme: "red", count: counts.error },
  ];

  return (
    <VStack align="stretch" spacing={4}>
      <Box
        borderWidth="1px"
        borderColor="var(--panel-border)"
        borderRadius="14px"
        bg="var(--panel-surface)"
        p={{ base: 3, md: 4 }}
      >
        <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
          <Box>
            <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">زیرساخت</Text>
            <Text mt={1} fontSize={{ base: "xl", md: "2xl" }} fontWeight="900">مدیریت گره‌ها</Text>
            <Text mt={1} fontSize="sm" color="var(--panel-text-muted)">
              وضعیت، ترافیک زنده و تنظیمات هر نود را از یک نمای فشرده مدیریت کنید.
            </Text>
          </Box>
          <Button
            colorScheme="yellow"
            color="gray.900"
            leftIcon={<PlusIcon width={18} />}
            onClick={() => setSelectedKey("new")}
          >
            افزودن نود
          </Button>
        </HStack>

        <Grid mt={4} templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(3, minmax(0, 1fr))", xl: "repeat(6, minmax(0, 1fr))" }} gap={2}>
          <SummaryCard label="کل گره‌ها" value={new Intl.NumberFormat("fa-IR").format(counts.all)} hint="شامل Master" />
          <SummaryCard label="گره‌های فعال" value={new Intl.NumberFormat("fa-IR").format(counts.connected)} accent="#22c55e" />
          <SummaryCard label="در حال اتصال" value={new Intl.NumberFormat("fa-IR").format(counts.connecting)} accent="#eab308" />
          <SummaryCard label="گره‌های غیرفعال" value={new Intl.NumberFormat("fa-IR").format(counts.disabled)} accent="#94a3b8" />
          <SummaryCard label="گره‌های خطادار" value={new Intl.NumberFormat("fa-IR").format(counts.error)} accent="#ef4444" />
          <SummaryCard label="پهنای‌باند لحظه‌ای" value={formatRate(bandwidth.data?.total_bps)} hint="مجموع دانلود و آپلود" accent="#38bdf8" />
        </Grid>
      </Box>

      <Grid
        dir="ltr"
        templateColumns={{ base: "1fr", xl: "minmax(0, 1.8fr) minmax(370px, .8fr)" }}
        gap={4}
        alignItems="start"
      >
        <Box dir="rtl" minW={0}>
          <Box
            borderWidth="1px"
            borderColor="var(--panel-border)"
            borderRadius="14px"
            bg="var(--panel-surface)"
            overflow="hidden"
          >
            <Box p={4} borderBottomWidth="1px" borderColor="var(--panel-border)">
              <HStack justify="space-between" align="start" gap={3} flexWrap="wrap">
                <Box>
                  <Text fontSize="lg" fontWeight="900">لیست گره‌ها</Text>
                  <Text mt={1} fontSize="xs" color="var(--panel-text-muted)">برای ویرایش، روی ردیف نود کلیک کنید.</Text>
                </Box>
                <HStack flexWrap="wrap" justify="flex-end">
                  {filterButtons.map((item) => (
                    <Button
                      key={item.key}
                      size="sm"
                      colorScheme={item.scheme}
                      variant={statusFilter === item.key ? "solid" : "outline"}
                      onClick={() => setStatusFilter(item.key)}
                    >
                      {item.label} {new Intl.NumberFormat("fa-IR").format(item.count)}
                    </Button>
                  ))}
                </HStack>
              </HStack>
              <HStack mt={3} gap={2}>
                <Box position="relative" flex="1" minW="190px">
                  <Box position="absolute" insetInlineStart="10px" top="50%" transform="translateY(-50%)" color="var(--panel-text-muted)" zIndex={1}>
                    <MagnifyingGlassIcon width={17} />
                  </Box>
                  <Input
                    size="sm"
                    ps="34px"
                    placeholder="جستجو در نام نود یا آدرس..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </Box>
                <Tooltip label="به‌روزرسانی اطلاعات">
                  <IconButton
                    aria-label="به‌روزرسانی نودها"
                    size="sm"
                    variant="outline"
                    icon={<ArrowPathIcon width={17} />}
                    onClick={() => {
                      bandwidth.refetch();
                    }}
                    isLoading={bandwidth.isFetching}
                  />
                </Tooltip>
              </HStack>
            </Box>

            <Box overflowX="auto">
              <Box minW="790px">
                <Grid
                  templateColumns="minmax(170px, 1.35fr) minmax(105px, .8fr) minmax(105px, .8fr) minmax(120px, .9fr) minmax(135px, 1fr) minmax(90px, .65fr)"
                  gap={2}
                  px={3}
                  py={2}
                  bg="var(--panel-nested)"
                  borderBottomWidth="1px"
                  borderColor="var(--panel-border)"
                >
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">نام نود / وضعیت</Text>
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">دانلود</Text>
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">آپلود</Text>
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">آخرین نمونه</Text>
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">روند زنده</Text>
                  <Text fontSize="xs" fontWeight="800" color="var(--panel-text-muted)">عملیات</Text>
                </Grid>

                {isLoading ? (
                  <Stack p={3} spacing={2}>
                    {[0, 1, 2, 3].map((item) => <Skeleton key={item} height="62px" borderRadius="10px" />)}
                  </Stack>
                ) : visibleRows.length === 0 ? (
                  <Box p={8} textAlign="center">
                    <Text fontWeight="800">نودی با این فیلتر پیدا نشد.</Text>
                    <Text mt={1} fontSize="sm" color="var(--panel-text-muted)">فیلتر یا عبارت جستجو را تغییر دهید.</Text>
                  </Box>
                ) : (
                  visibleRows.map((row) => {
                    const selectedRow = selectedKey === row.key;
                    const color = row.status === "connected" ? "green.300" : row.status === "connecting" ? "yellow.300" : row.status === "disabled" ? "gray.400" : "red.300";
                    return (
                      <Grid
                        key={row.key}
                        templateColumns="minmax(170px, 1.35fr) minmax(105px, .8fr) minmax(105px, .8fr) minmax(120px, .9fr) minmax(135px, 1fr) minmax(90px, .65fr)"
                        gap={2}
                        px={3}
                        py={2.5}
                        alignItems="center"
                        borderBottomWidth="1px"
                        borderColor="var(--panel-border)"
                        bg={selectedRow ? "rgba(59,130,246,.12)" : "transparent"}
                        boxShadow={selectedRow ? "inset 3px 0 0 var(--panel-accent)" : "none"}
                        cursor={row.editable ? "pointer" : "default"}
                        _hover={row.editable ? { bg: selectedRow ? "rgba(59,130,246,.14)" : "whiteAlpha.50" } : undefined}
                        onClick={() => row.editable && setSelectedKey(row.key)}
                      >
                        <Box minW={0}>
                          <HStack spacing={2} minW={0}>
                            <Text fontWeight="900" noOfLines={1} dir="ltr">{row.name}</Text>
                            <NodeModalStatusBadge status={row.status} compact />
                          </HStack>
                          <Text mt={1} fontSize="xs" color="var(--panel-text-muted)" noOfLines={1} dir="ltr" textAlign="start">
                            {row.node?.address || (row.key === "master" ? "Local core" : "—")}
                          </Text>
                        </Box>
                        <Text fontSize="sm" fontWeight="800" dir="ltr" textAlign="start">{formatRate(row.bandwidth?.downlink_bps)}</Text>
                        <Text fontSize="sm" fontWeight="800" dir="ltr" textAlign="start">{formatRate(row.bandwidth?.uplink_bps)}</Text>
                        <Box>
                          <Text fontSize="xs" fontWeight="700">{sampleAgeLabel(row.bandwidth?.sample_age_seconds)}</Text>
                          <Text mt={1} fontSize="10px" color="var(--panel-text-muted)" dir="ltr" textAlign="start">{sampledAtLabel(row.bandwidth?.sampled_at)}</Text>
                        </Box>
                        <Box color={color} minW={0}>
                          <Sparkline values={history[row.key] || []} />
                        </Box>
                        <Button
                          size="xs"
                          variant="outline"
                          isDisabled={!row.editable}
                          onClick={(event) => {
                            event.stopPropagation();
                            if (row.editable) setSelectedKey(row.key);
                          }}
                        >
                          {row.editable ? "ویرایش" : "سیستمی"}
                        </Button>
                      </Grid>
                    );
                  })
                )}
              </Box>
            </Box>

            <HStack px={3} py={3} justify="space-between" gap={3} flexWrap="wrap">
              <HStack>
                <Button size="sm" variant="outline" isDisabled={safePage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>قبلی</Button>
                <Badge colorScheme="primary" px={3} py={1.5} borderRadius="8px">{new Intl.NumberFormat("fa-IR").format(safePage)}</Badge>
                <Button size="sm" variant="outline" isDisabled={safePage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>بعدی</Button>
              </HStack>
              <HStack>
                <Text fontSize="xs" color="var(--panel-text-muted)">
                  نمایش {new Intl.NumberFormat("fa-IR").format(filteredRows.length ? (safePage - 1) * pageSize + 1 : 0)} تا {new Intl.NumberFormat("fa-IR").format(Math.min(safePage * pageSize, filteredRows.length))} از {new Intl.NumberFormat("fa-IR").format(filteredRows.length)} گره
                </Text>
                <Select size="sm" w="74px" value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </Select>
              </HStack>
            </HStack>
          </Box>

          <WatchdogPanel />
        </Box>

        <Box dir="rtl" minW={0}>
          {selectedKey === "new" ? (
            <NodeEditor node={null} isNew bandwidth={undefined} onSaved={() => setSelectedKey(null)} />
          ) : selected?.editable && selected.node ? (
            <NodeEditor node={selected.node} bandwidth={selected.bandwidth} isNew={false} onSaved={() => undefined} />
          ) : selected ? (
            <Box borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" bg="var(--panel-surface)" p={4}>
              <Text color="var(--panel-accent)" fontSize="xs" fontWeight="800">جزئیات گره سیستمی</Text>
              <HStack mt={1} spacing={2}>
                <Text fontSize="lg" fontWeight="900" dir="ltr">{selected.name}</Text>
                <NodeModalStatusBadge status={selected.status} compact />
              </HStack>
              <Text mt={2} fontSize="sm" color="var(--panel-text-muted)">
                Master هسته محلی پنل است و از این بخش قابل ویرایش نیست.
              </Text>
              <Grid mt={4} templateColumns="repeat(2, minmax(0, 1fr))" gap={2}>
                <SummaryCard label="دانلود" value={formatRate(selected.bandwidth?.downlink_bps)} />
                <SummaryCard label="آپلود" value={formatRate(selected.bandwidth?.uplink_bps)} />
              </Grid>
            </Box>
          ) : (
            <Box borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" bg="var(--panel-surface)" p={6} textAlign="center">
              <Text fontWeight="800">یک نود را از لیست انتخاب کنید.</Text>
            </Box>
          )}
        </Box>
      </Grid>
    </VStack>
  );
};
