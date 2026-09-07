import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Card,
  FormControl,
  FormHelperText,
  FormLabel,
  Grid,
  Heading,
  HStack,
  Input,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Switch,
  Text,
  Textarea,
  useToast,
} from "@chakra-ui/react";
import { AppShell } from "components/AppShell";
import { ChangeEvent, FC, FormEvent, ReactNode, useEffect, useState } from "react";
import { useMutation, useQuery } from "react-query";
import { Link as RouterLink } from "react-router-dom";
import { fetch } from "service/http";
import { SystemBranding } from "types/Admin";
import { localizedApiError } from "utils/apiError";
import { queryClient } from "utils/react-query";

type Pricing = {
  price_per_gib_toman: number;
  allow_unlimited_duration: boolean;
  duration_presets: Array<{
    duration_days: number;
    multiplier: number;
    enabled: boolean;
  }>;
};

type BackupSettings = {
  enabled: boolean;
  destination: "LOCAL" | "TELEGRAM" | "EMAIL" | "TELEGRAM_EMAIL";
  schedule: string;
  retention_count: number;
  telegram_bot_token?: string | null;
  telegram_chat_id?: string | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_password?: string | null;
  smtp_use_tls: boolean;
  email_from?: string | null;
  email_to?: string | null;
  telegram_configured: boolean;
  smtp_configured: boolean;
};

type SectionItem = {
  id: string;
  title: string;
  caption: string;
};

const sections: SectionItem[] = [
  { id: "base-pricing", title: "قیمت‌گذاری پایه", caption: "فرم آزاد و مدت‌ها" },
  { id: "backup", title: "پشتیبان‌گیری", caption: "بکاپ و بازیابی آفلاین" },
  { id: "branding", title: "هویت پنل", caption: "نام، لوگو و صفحه ورود" },
];

const scheduleLabels: Record<string, string> = {
  "15m": "هر ۱۵ دقیقه",
  "30m": "هر ۳۰ دقیقه",
  "1h": "هر ۱ ساعت",
  "3h": "هر ۳ ساعت",
  "6h": "هر ۶ ساعت",
  "12h": "هر ۱۲ ساعت",
  "24h": "هر ۲۴ ساعت",
};

const destinationLabels: Record<BackupSettings["destination"], string> = {
  LOCAL: "فقط محلی",
  TELEGRAM: "تلگرام",
  EMAIL: "ایمیل",
  TELEGRAM_EMAIL: "تلگرام و ایمیل",
};

const Section: FC<{
  id: string;
  title: string;
  description: string;
  children: ReactNode;
}> = ({ id, title, description, children }) => (
  <Card
    id={id}
    tabIndex={-1}
    scrollMarginTop="24px"
    p={{ base: 4, md: 6 }}
    borderWidth="1px"
    borderColor="var(--panel-border)"
    borderRadius="var(--radius-panel)"
    boxShadow="var(--shadow-panel)"
    bg="var(--panel-surface)"
  >
    <Stack spacing={1}>
      <Heading size="md">{title}</Heading>
      <Text color="gray.600" _dark={{ color: "gray.400" }} fontSize="sm" lineHeight="1.9">
        {description}
      </Text>
    </Stack>
    <Box mt={5}>{children}</Box>
  </Card>
);

const QueryState: FC<{
  label: string;
  query: { isLoading: boolean; isError: boolean; refetch: () => unknown };
}> = ({ label, query }) => {
  if (query.isLoading) return <Skeleton height="72px" borderRadius="12px" />;
  if (!query.isError) return null;
  return (
    <Alert status="error" borderRadius="12px">
      <AlertIcon />
      دریافت اطلاعات {label} انجام نشد.
      <Button ms={3} size="sm" variant="outline" onClick={() => query.refetch()}>
        تلاش دوباره
      </Button>
    </Alert>
  );
};

export const Settings: FC = () => {
  const toast = useToast();
  const [uploading, setUploading] = useState(false);
  const brandingQuery = useQuery<SystemBranding>("system-branding", () => fetch("/branding/public"));
  const pricingQuery = useQuery<Pricing>("owner-pricing", () => fetch("/owner/pricing"), {
    refetchOnWindowFocus: false,
  });
  const backupQuery = useQuery<BackupSettings>("backup-settings", () => fetch("/owner/backups/settings"), {
    refetchOnWindowFocus: false,
  });
  const [branding, setBranding] = useState<SystemBranding | null>(null);
  const [pricing, setPricing] = useState<Pricing | null>(null);
  const [backup, setBackup] = useState<BackupSettings | null>(null);
  const [restoreFiles, setRestoreFiles] = useState<File[]>([]);
  const [validation, setValidation] = useState<{ token: string; manifest: Record<string, unknown> } | null>(null);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    if (brandingQuery.data) setBranding((current) => current ?? brandingQuery.data!);
  }, [brandingQuery.data]);
  useEffect(() => {
    if (pricingQuery.data) setPricing((current) => current ?? pricingQuery.data!);
  }, [pricingQuery.data]);
  useEffect(() => {
    if (backupQuery.data) setBackup((current) => current ?? backupQuery.data!);
  }, [backupQuery.data]);

  const success = (title: string) => {
    toast({ title, status: "success", duration: 2500 });
  };
  const failure = (error: unknown) => {
    toast({
      title: "عملیات انجام نشد",
      description: localizedApiError(error),
      status: "error",
      duration: 5000,
    });
  };

  const saveBranding = useMutation(
    () => fetch<SystemBranding>("/branding/system", { method: "PUT", body: branding }),
    {
      onSuccess: (value) => {
        setBranding(value);
        queryClient.setQueryData("system-branding", value);
        success("تنظیمات هویت پنل ذخیره شد");
      },
      onError: failure,
    }
  );

  const uploadBrand = async (kind: "logo" | "favicon", event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || uploading) return;
    setUploading(true);
    const body = new FormData();
    body.append(kind, file);
    try {
      const value = await fetch<SystemBranding>(`/branding/system/${kind}`, { method: "POST", body });
      setBranding(value);
      queryClient.setQueryData("system-branding", value);
      success(kind === "logo" ? "لوگو بارگذاری شد" : "آیکن پنل بارگذاری شد");
    } catch (error) {
      failure(error);
    } finally {
      setUploading(false);
    }
  };

  const savePricing = useMutation(
    () => fetch<Pricing>("/owner/pricing", { method: "PUT", body: pricing }),
    {
      onSuccess: (value) => {
        setPricing(value);
        success("قیمت‌گذاری پایه ذخیره شد");
      },
      onError: failure,
    }
  );

  const saveBackup = useMutation(
    () => fetch<BackupSettings>("/owner/backups/settings", { method: "PUT", body: backup }),
    {
      onSuccess: (value) => {
        setBackup(value);
        success("تنظیمات پشتیبان‌گیری ذخیره شد");
      },
      onError: failure,
    }
  );

  const createBackup = useMutation(() => fetch("/owner/backups", { method: "POST" }), {
    onSuccess: () => success("نسخه پشتیبان ساخته شد"),
    onError: failure,
  });

  const validateRestore = async (files: File[]) => {
    if (!files.length || validating) return;
    setRestoreFiles(files);
    const body = new FormData();
    files.forEach((file) => body.append("backups", file));
    setValidating(true);
    setValidation(null);
    try {
      const value = await fetch<{ validation_token: string; manifest: Record<string, unknown> }>(
        "/owner/backups/validate",
        { method: "POST", body }
      );
      setValidation({ token: value.validation_token, manifest: value.manifest });
      success("فایل پشتیبان معتبر است");
    } catch (error) {
      setValidation(null);
      failure(error);
    } finally {
      setValidating(false);
    }
  };

  const scrollTo = (id: string) => {
    const section = document.getElementById(id);
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
    section?.focus({ preventScroll: true });
  };

  return (
    <AppShell>
      <Stack spacing={6}>
        <Card
          p={{ base: 4, md: 6 }}
          borderWidth="1px"
          borderColor="var(--panel-border)"
          borderRadius="var(--radius-panel)"
          bg="var(--panel-surface)"
        >
          <Stack spacing={2}>
            <Text color="primary.400" fontSize="xs" fontWeight="800" letterSpacing=".08em">
              پیکربندی مالک پنل
            </Text>
            <Heading size="lg">پیکربندی</Heading>
            <Text color="gray.600" _dark={{ color: "gray.400" }} maxW="820px" lineHeight="1.9">
              این صفحه فقط تنظیمات سراسری و واقعی سیستم را نگه می‌دارد. سیاست هر ادمین هنگام ساخت یا ویرایش همان ادمین
              تعیین می‌شود و پلن‌های تجاری نیز در صفحه پلن‌ها مدیریت می‌شوند.
            </Text>
            <HStack pt={2} spacing={2} wrap="wrap">
              <Button as={RouterLink} to="/admins/?create=1" colorScheme="primary" size="sm">
                ساخت ادمین
              </Button>
              <Button as={RouterLink} to="/plans/" variant="outline" size="sm">
                مدیریت پلن‌ها
              </Button>
            </HStack>
          </Stack>
        </Card>

        <Grid templateColumns={{ base: "1fr", xl: "250px minmax(0, 1fr)" }} gap={5} alignItems="start">
          <Card
            as="nav"
            position={{ xl: "sticky" }}
            top={{ xl: 6 }}
            p={3}
            borderWidth="1px"
            borderColor="var(--panel-border)"
            borderRadius="var(--radius-panel)"
            bg="var(--panel-surface)"
          >
            <Text px={2} pb={2} fontSize="xs" color="gray.500" fontWeight="700">
              دسترسی سریع
            </Text>
            <Stack spacing={1}>
              {sections.map((section) => (
                <Button
                  key={section.id}
                  variant="ghost"
                  justifyContent="flex-start"
                  h="auto"
                  py={2.5}
                  px={2}
                  onClick={() => scrollTo(section.id)}
                >
                  <Stack spacing={0} align="start" textAlign="start">
                    <Text fontSize="sm" fontWeight="700">{section.title}</Text>
                    <Text fontSize="xs" color="gray.500" fontWeight="400">{section.caption}</Text>
                  </Stack>
                </Button>
              ))}
            </Stack>
          </Card>

          <Stack spacing={5} minW={0}>
            <QueryState label="قیمت‌گذاری" query={pricingQuery} />
            <QueryState label="پشتیبان‌گیری" query={backupQuery} />
            <QueryState label="هویت پنل" query={brandingQuery} />

            <Section
              id="base-pricing"
              title="قیمت‌گذاری پایه"
              description="این مقادیر فقط مبنای ساخت کاربر به روش فرم آزاد هستند. قیمت و سیاست اختصاصی هر ادمین در فرم ساخت یا ویرایش ادمین تعیین می‌شود و مشخصات پلن‌های تجاری در صفحه پلن‌ها قرار دارند."
            >
              {pricing && (
                <Stack
                  as="form"
                  onSubmit={(event: FormEvent) => {
                    event.preventDefault();
                    savePricing.mutate();
                  }}
                  spacing={5}
                >
                  <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                    <FormControl>
                      <FormLabel>قیمت پایه هر گیگابایت</FormLabel>
                      <Input
                        type="number"
                        min={0}
                        value={pricing.price_per_gib_toman}
                        onChange={(event) =>
                          setPricing({ ...pricing, price_per_gib_toman: Number(event.target.value) })
                        }
                      />
                      <FormHelperText>مبلغ به تومان و فقط برای محاسبات فرم آزاد.</FormHelperText>
                    </FormControl>
                    <FormControl>
                      <FormLabel>مدت نامحدود</FormLabel>
                      <HStack minH="40px" justify="space-between" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" px={3}>
                        <Text fontSize="sm">امکان ساخت کاربر بدون تاریخ انقضا</Text>
                        <Switch
                          colorScheme="primary"
                          isChecked={pricing.allow_unlimited_duration}
                          onChange={(event) =>
                            setPricing({ ...pricing, allow_unlimited_duration: event.target.checked })
                          }
                          aria-label="مدت نامحدود"
                        />
                      </HStack>
                    </FormControl>
                  </SimpleGrid>

                  <Box>
                    <HStack mb={3} justify="space-between" wrap="wrap">
                      <Box>
                        <Text fontWeight="800">مدت‌های آماده</Text>
                        <Text color="gray.500" fontSize="sm">ضریب هر مدت روی قیمت پایه اعمال می‌شود.</Text>
                      </Box>
                      <Badge colorScheme="cyan">{pricing.duration_presets.filter((item) => item.enabled).length.toLocaleString("fa-IR")} فعال</Badge>
                    </HStack>
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                      {pricing.duration_presets.map((preset, index) => (
                        <Card
                          key={preset.duration_days}
                          p={3}
                          borderWidth="1px"
                          borderColor="var(--panel-border)"
                          borderRadius="12px"
                          bg="var(--panel-nested)"
                        >
                          <HStack align="center" gap={3}>
                            <Box flex="1">
                              <Text fontWeight="700">{preset.duration_days.toLocaleString("fa-IR")} روز</Text>
                              <Text color="gray.500" fontSize="xs">ضریب قیمت</Text>
                            </Box>
                            <Input
                              aria-label={`ضریب ${preset.duration_days} روز`}
                              type="number"
                              step="0.0001"
                              min="0.0001"
                              w="110px"
                              value={preset.multiplier}
                              onChange={(event) => {
                                const duration_presets = [...pricing.duration_presets];
                                duration_presets[index] = { ...preset, multiplier: Number(event.target.value) };
                                setPricing({ ...pricing, duration_presets });
                              }}
                            />
                            <Switch
                              colorScheme="primary"
                              aria-label={`فعال بودن مدت ${preset.duration_days} روز`}
                              isChecked={preset.enabled}
                              onChange={(event) => {
                                const duration_presets = [...pricing.duration_presets];
                                duration_presets[index] = { ...preset, enabled: event.target.checked };
                                setPricing({ ...pricing, duration_presets });
                              }}
                            />
                          </HStack>
                        </Card>
                      ))}
                    </SimpleGrid>
                  </Box>

                  <HStack justify="space-between" wrap="wrap" gap={3}>
                    <Text color="gray.500" fontSize="sm">
                      سیاست ساخت ادمین از این صفحه حذف شده و در صفحه ادمین‌ها مدیریت می‌شود.
                    </Text>
                    <Button type="submit" colorScheme="primary" isLoading={savePricing.isLoading}>
                      ذخیره قیمت‌گذاری
                    </Button>
                  </HStack>
                </Stack>
              )}
            </Section>


            <Section
              id="backup"
              title="پشتیبان‌گیری و بازیابی"
              description="نسخه پشتیبان منطقی MySQL را زمان‌بندی کنید، مقصد ارسال را انتخاب کنید و فایل‌های بازیابی را پیش از عملیات آفلاین اعتبارسنجی کنید."
            >
              {backup && (
                <Stack spacing={5}>
                  <Card p={4} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                    <HStack justify="space-between" align="start" gap={4}>
                      <Box>
                        <Text fontWeight="800">پشتیبان‌گیری خودکار</Text>
                        <Text color="gray.500" fontSize="sm" mt={1}>
                          حتی در صورت خطای ارسال، نسخه محلی قابل بازیابی نگه داشته می‌شود.
                        </Text>
                      </Box>
                      <Switch
                        colorScheme="primary"
                        aria-label="پشتیبان‌گیری خودکار"
                        isChecked={backup.enabled}
                        onChange={(event) => setBackup({ ...backup, enabled: event.target.checked })}
                      />
                    </HStack>
                  </Card>

                  <SimpleGrid columns={{ base: 1, md: 3 }} gap={3}>
                    <FormControl>
                      <FormLabel>مقصد</FormLabel>
                      <Select
                        value={backup.destination}
                        onChange={(event) =>
                          setBackup({ ...backup, destination: event.target.value as BackupSettings["destination"] })
                        }
                      >
                        {(Object.keys(destinationLabels) as BackupSettings["destination"][]).map((value) => (
                          <option key={value} value={value}>{destinationLabels[value]}</option>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl>
                      <FormLabel>زمان‌بندی</FormLabel>
                      <Select value={backup.schedule} onChange={(event) => setBackup({ ...backup, schedule: event.target.value })}>
                        {Object.entries(scheduleLabels).map(([value, label]) => (
                          <option key={value} value={value}>{label}</option>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl>
                      <FormLabel>تعداد نسخه‌های نگهداری‌شده</FormLabel>
                      <Input
                        type="number"
                        min={1}
                        max={365}
                        value={backup.retention_count}
                        onChange={(event) => setBackup({ ...backup, retention_count: Number(event.target.value) })}
                      />
                    </FormControl>
                  </SimpleGrid>

                  {backup.destination.includes("TELEGRAM") && (
                    <Card p={4} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                      <Text fontWeight="800" mb={3}>ارسال به تلگرام</Text>
                      <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                        <FormControl>
                          <FormLabel>توکن ربات</FormLabel>
                          <Input
                            type="password"
                            placeholder={backup.telegram_configured ? "تنظیم شده؛ برای حفظ مقدار خالی بگذارید" : "توکن ربات را وارد کنید"}
                            onChange={(event) => setBackup({ ...backup, telegram_bot_token: event.target.value || null })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>شناسه چت</FormLabel>
                          <Input
                            dir="ltr"
                            value={backup.telegram_chat_id || ""}
                            onChange={(event) => setBackup({ ...backup, telegram_chat_id: event.target.value })}
                          />
                        </FormControl>
                      </SimpleGrid>
                    </Card>
                  )}

                  {backup.destination.includes("EMAIL") && (
                    <Card p={4} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px" bg="var(--panel-nested)">
                      <Text fontWeight="800" mb={3}>ارسال به ایمیل</Text>
                      <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                        <FormControl>
                          <FormLabel>نام کاربری SMTP</FormLabel>
                          <Input
                            autoComplete="off"
                            dir="ltr"
                            value={backup.smtp_username || ""}
                            onChange={(event) => setBackup({ ...backup, smtp_username: event.target.value })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>رمز عبور SMTP</FormLabel>
                          <Input
                            type="password"
                            autoComplete="new-password"
                            placeholder={backup.smtp_configured ? "تنظیم شده؛ برای حفظ مقدار خالی بگذارید" : "اختیاری"}
                            onChange={(event) => setBackup({ ...backup, smtp_password: event.target.value || null })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>میزبان SMTP</FormLabel>
                          <Input
                            dir="ltr"
                            value={backup.smtp_host || ""}
                            onChange={(event) => setBackup({ ...backup, smtp_host: event.target.value })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>پورت SMTP</FormLabel>
                          <Input
                            type="number"
                            dir="ltr"
                            value={backup.smtp_port || ""}
                            onChange={(event) =>
                              setBackup({ ...backup, smtp_port: event.target.value ? Number(event.target.value) : null })
                            }
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>ایمیل فرستنده</FormLabel>
                          <Input
                            dir="ltr"
                            value={backup.email_from || ""}
                            onChange={(event) => setBackup({ ...backup, email_from: event.target.value })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>ایمیل گیرنده</FormLabel>
                          <Input
                            dir="ltr"
                            value={backup.email_to || ""}
                            onChange={(event) => setBackup({ ...backup, email_to: event.target.value })}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>رمزنگاری TLS</FormLabel>
                          <HStack minH="40px" px={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" justify="space-between">
                            <Text fontSize="sm">استفاده از اتصال امن</Text>
                            <Switch
                              colorScheme="primary"
                              isChecked={backup.smtp_use_tls}
                              onChange={(event) => setBackup({ ...backup, smtp_use_tls: event.target.checked })}
                            />
                          </HStack>
                        </FormControl>
                      </SimpleGrid>
                    </Card>
                  )}

                  <HStack wrap="wrap" gap={2}>
                    <Button colorScheme="primary" onClick={() => saveBackup.mutate()} isLoading={saveBackup.isLoading}>
                      ذخیره تنظیمات بکاپ
                    </Button>
                    <Button variant="outline" onClick={() => createBackup.mutate()} isLoading={createBackup.isLoading}>
                      ساخت بکاپ الآن
                    </Button>
                  </HStack>

                  <Box pt={5} borderTopWidth="1px" borderColor="var(--panel-border)">
                    <Text fontWeight="800">اعتبارسنجی فایل برای بازیابی آفلاین</Text>
                    <Alert mt={3} status="warning" borderRadius="12px" alignItems="start">
                      <AlertIcon mt={1} />
                      بازیابی آنلاین برای حفاظت از داده فعال غیرفعال است. این مرحله فقط سلامت آرشیو را بررسی می‌کند و هیچ داده‌ای را بازیابی نمی‌کند.
                    </Alert>
                    <FormControl mt={4} maxW="520px">
                      <FormLabel>فایل پشتیبان</FormLabel>
                      <Input
                        aria-label="فایل پشتیبان"
                        p={1.5}
                        type="file"
                        multiple
                        isDisabled={validating}
                        onChange={(event) => {
                          setValidation(null);
                          const files = Array.from(event.target.files || []);
                          setRestoreFiles(files);
                          void validateRestore(files);
                        }}
                      />
                    </FormControl>
                    {restoreFiles.length > 0 && (
                      <Text mt={2} role="status" color="gray.500" fontSize="sm">
                        {restoreFiles.length > 1
                          ? `بکاپ چندبخشی · ${restoreFiles.length.toLocaleString("fa-IR")} فایل`
                          : "بکاپ کامل"}
                        {" · "}
                        {(restoreFiles.reduce((sum, file) => sum + file.size, 0) / 1024 ** 2).toLocaleString("fa-IR", { maximumFractionDigits: 1 })} مگابایت
                        {validating ? " · در حال بررسی…" : ""}
                      </Text>
                    )}
                    {validation && (
                      <Alert mt={3} status="success" borderRadius="12px">
                        <AlertIcon />آرشیو معتبر است؛ برای بازیابی همچنان باید روال آفلاین اجرا شود.
                      </Alert>
                    )}
                  </Box>
                </Stack>
              )}
            </Section>

            <Section
              id="branding"
              title="هویت پنل"
              description="نام پنل، عنوان صفحه ورود، توضیح، لوگو و favicon را از یک محل مدیریت کنید."
            >
              {branding && (
                <Stack spacing={4}>
                  <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                    <FormControl>
                      <FormLabel>نام پنل</FormLabel>
                      <Input
                        value={branding.panel_name}
                        onChange={(event) => setBranding({ ...branding, panel_name: event.target.value })}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>عنوان صفحه ورود</FormLabel>
                      <Input
                        value={branding.login_title}
                        onChange={(event) => setBranding({ ...branding, login_title: event.target.value })}
                      />
                    </FormControl>
                  </SimpleGrid>
                  <FormControl>
                    <FormLabel>توضیح اختیاری</FormLabel>
                    <Textarea
                      value={branding.description || ""}
                      onChange={(event) => setBranding({ ...branding, description: event.target.value })}
                    />
                  </FormControl>
                  <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                    <FormControl>
                      <FormLabel>لوگو</FormLabel>
                      <Input
                        p={1.5}
                        isDisabled={uploading}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(event) => uploadBrand("logo", event)}
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>آیکن مرورگر</FormLabel>
                      <Input
                        p={1.5}
                        isDisabled={uploading}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(event) => uploadBrand("favicon", event)}
                      />
                    </FormControl>
                  </SimpleGrid>
                  <HStack justify="flex-end">
                    <Button
                      colorScheme="primary"
                      onClick={() => saveBranding.mutate()}
                      isDisabled={uploading}
                      isLoading={saveBranding.isLoading}
                    >
                      ذخیره هویت پنل
                    </Button>
                  </HStack>
                </Stack>
              )}
            </Section>
          </Stack>
        </Grid>
      </Stack>
    </AppShell>
  );
};

export default Settings;
