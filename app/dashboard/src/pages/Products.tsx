import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Card,
  Checkbox,
  FormControl,
  FormHelperText,
  FormLabel,
  HStack,
  Input,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Textarea,
  useToast,
} from "@chakra-ui/react";
import { AppShell } from "components/AppShell";
import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { AccessGroupNetworkOption, Product } from "types/Admin";
import {
  missingAccessGroupHostIds,
  missingAccessGroupInboundTags,
  normalizeAccessGroupHostScope,
  normalizeAccessGroupInboundTags,
  toggleAccessGroupHostId,
  toggleAccessGroupInboundTag,
} from "utils/accessGroupScope";
import { localizedApiError } from "utils/apiError";

type Draft = {
  id: number | null;
  name: string;
  description: string;
  multiplier: string;
  inbounds: string[];
  hosts: Record<string, number[]>;
};

const emptyDraft = (): Draft => ({
  id: null,
  name: "",
  description: "",
  multiplier: "1",
  inbounds: [],
  hosts: {},
});

export const Products = () => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Draft>(emptyDraft());
  const products = useQuery<Product[], Error>(
    "products",
    () => fetch<Product[]>("/products?include_archived=true")
  );
  const network = useQuery<AccessGroupNetworkOption[], Error>(
    "product-network-options",
    () => fetch("/access-group-network-options")
  );
  const options = network.data || [];
  const missingInbounds = network.isLoading
    ? []
    : missingAccessGroupInboundTags(draft.inbounds, options);
  const missingHosts = network.isLoading
    ? []
    : missingAccessGroupHostIds(draft.hosts, options);

  const save = useMutation(
    () => fetch<Product>(draft.id ? `/products/${draft.id}` : "/products", {
      method: draft.id ? "PUT" : "POST",
      body: {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        traffic_price_multiplier: draft.multiplier.trim(),
        inbounds: normalizeAccessGroupInboundTags(draft.inbounds),
        hosts: normalizeAccessGroupHostScope(draft.hosts),
      },
    }),
    {
      onSuccess: (product) => {
        queryClient.invalidateQueries("products");
        setDraft(emptyDraft());
        toast({ title: `محصول «${product.name}» ذخیره شد`, status: "success" });
      },
      onError: (error) => {
        toast({
          title: "ذخیره محصول انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  const archive = useMutation(
    (product: Product) => fetch(`/products/${product.id}`, { method: "DELETE" }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("products");
        setDraft(emptyDraft());
        toast({ title: "محصول بایگانی شد", status: "success" });
      },
      onError: (error) => {
        toast({
          title: "بایگانی محصول انجام نشد",
          description: localizedApiError(error),
          status: "error",
        });
      },
    }
  );

  const restore = useMutation(
    (product: Product) => fetch(`/products/${product.id}/restore`, { method: "POST" }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("products");
        toast({ title: "محصول بازیابی شد", status: "success" });
      },
      onError: (error) => {
        toast({
          title: "بازیابی محصول انجام نشد",
          description: localizedApiError(error),
          status: "error",
        });
      },
    }
  );

  const edit = (product: Product) => setDraft({
    id: product.id,
    name: product.name,
    description: product.description || "",
    multiplier: String(product.traffic_price_multiplier),
    inbounds: normalizeAccessGroupInboundTags(product.inbounds),
    hosts: normalizeAccessGroupHostScope(product.hosts),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const multiplier = Number(draft.multiplier);
    if (!draft.name.trim()) {
      toast({ title: "نام محصول الزامی است", status: "warning" });
      return;
    }
    if (!Number.isFinite(multiplier) || multiplier <= 0) {
      toast({ title: "ضریب باید عددی مثبت باشد", status: "warning" });
      return;
    }
    if (!draft.inbounds.length) {
      toast({ title: "حداقل یک اینباند انتخاب کنید", status: "warning" });
      return;
    }
    if (missingInbounds.length || missingHosts.length) {
      toast({
        title: "انتخاب حذف‌شده یا غیرفعال را اصلاح کنید",
        description: missingHosts.length
          ? `شناسه هاست: ${missingHosts.join(", ")}`
          : missingInbounds.join(", "),
        status: "warning",
      });
      return;
    }
    if (draft.inbounds.some((tag) => !(draft.hosts[tag] || []).length)) {
      toast({ title: "برای هر اینباند یک هاست فعال انتخاب کنید", status: "warning" });
      return;
    }
    save.mutate();
  };

  return <AppShell>
    <Stack spacing={6}>
      <Box>
        <Text as="h1" fontSize={{ base: "2xl", md: "3xl" }} fontWeight="900">محصول‌ها</Text>
        <Text mt={2} color="var(--panel-text-body)" lineHeight="1.9">
          هویت و شبکهٔ محصول‌های جدید را مدیریت کنید. Product از پلن‌های قدیمی مستقل است.
        </Text>
      </Box>

      <Alert status="info" borderRadius="14px">
        <AlertIcon />
        این صفحه حجم، مدت، تعداد دستگاه یا قیمت ثابت را مدیریت نمی‌کند؛ این مقادیر در جریان خرید و قیمت‌گذاری مراحل بعد تعیین می‌شوند.
      </Alert>

      <Card as="form" onSubmit={submit} p={{ base: 4, md: 6 }} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="20px">
        <Stack spacing={5}>
          <HStack justify="space-between" align="start" gap={3} wrap="wrap">
            <Box><Text fontSize="lg" fontWeight="900">{draft.id ? "ویرایش محصول" : "محصول جدید"}</Text><Text color="var(--panel-text-muted)" fontSize="sm" mt={1}>فقط Owner می‌تواند این تنظیمات را تغییر دهد.</Text></Box>
            {draft.id && <Button variant="ghost" onClick={() => setDraft(emptyDraft())}>انصراف از ویرایش</Button>}
          </HStack>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
            <FormControl isRequired><FormLabel>نام محصول</FormLabel><Input maxLength={128} value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
            <FormControl isRequired><FormLabel>ضریب قیمت ترافیک</FormLabel><Input type="number" min="0.000001" step="0.000001" dir="ltr" value={draft.multiplier} onChange={(event) => setDraft((current) => ({ ...current, multiplier: event.target.value }))} /><FormHelperText>پیش‌فرض ۱ است؛ قیمت‌گذاری ثابت مدل اکانتی در این فرم نیست.</FormHelperText></FormControl>
          </SimpleGrid>
          <FormControl><FormLabel>توضیح</FormLabel><Textarea maxLength={512} value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
          <FormControl isRequired>
            <FormLabel>اینباند و هاست</FormLabel>
            <Stack maxH="420px" overflowY="auto" spacing={2} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px">
              {options.map((inbound) => <Box key={inbound.tag} p={2} borderRadius="12px" bg={draft.inbounds.includes(inbound.tag) ? "var(--panel-accent-soft)" : "transparent"}>
                <Checkbox isChecked={draft.inbounds.includes(inbound.tag)} onChange={(event) => setDraft((current) => {
                  const inbounds = toggleAccessGroupInboundTag(current.inbounds, inbound.tag, event.target.checked);
                  const hosts = { ...current.hosts };
                  if (event.target.checked) hosts[inbound.tag] = hosts[inbound.tag] || [];
                  else delete hosts[inbound.tag];
                  return { ...current, inbounds, hosts: normalizeAccessGroupHostScope(hosts) };
                })}><Stack spacing={0} dir="ltr"><Text fontWeight="700">{inbound.tag}</Text><Text fontSize="xs" color="var(--panel-text-muted)">{inbound.protocol} · {inbound.network} · {inbound.tls || "none"}</Text></Stack></Checkbox>
                {draft.inbounds.includes(inbound.tag) && <Stack ms={7} mt={2} spacing={1}>{inbound.hosts.map((host) => <Checkbox key={host.id} isChecked={(draft.hosts[inbound.tag] || []).includes(host.id)} onChange={(event) => setDraft((current) => ({ ...current, hosts: toggleAccessGroupHostId(current.hosts, inbound.tag, host.id, event.target.checked) }))}><Text dir="ltr">#{host.id} · {host.remark}</Text></Checkbox>)}{!inbound.hosts.length && <Text color="red.400" fontSize="sm">هاست فعالی برای این اینباند وجود ندارد.</Text>}</Stack>}
              </Box>)}
              {missingInbounds.map((tag) => <Checkbox key={tag} isChecked colorScheme="red" onChange={(event) => setDraft((current) => ({ ...current, inbounds: toggleAccessGroupInboundTag(current.inbounds, tag, event.target.checked), hosts: Object.fromEntries(Object.entries(current.hosts).filter(([key]) => key !== tag)) }))}><HStack><Text dir="ltr">{tag}</Text><Badge colorScheme="red">قدیمی / حذف‌شده</Badge></HStack></Checkbox>)}
              {!options.length && <Text color="var(--panel-text-muted)">اینباند قابل استفاده‌ای پیدا نشد.</Text>}
            </Stack>
            <FormHelperText>برای هر اینباند حداقل یک هاست فعال لازم است؛ انتخاب Node مستقل در Product وجود ندارد.</FormHelperText>
          </FormControl>
          <HStack justify="flex-end"><Button variant="ghost" onClick={() => setDraft(emptyDraft())}>پاک‌کردن فرم</Button><Button type="submit" colorScheme="primary" isLoading={save.isLoading}>{draft.id ? "ذخیره تغییرات" : "ساخت محصول"}</Button></HStack>
        </Stack>
      </Card>

      {(products.isLoading || network.isLoading) && <Stack><Skeleton h="120px" /><Skeleton h="120px" /></Stack>}
      {(products.isError || network.isError) && <Alert status="error"><AlertIcon />اطلاعات محصول‌ها دریافت نشد.</Alert>}
      {!products.isLoading && !products.isError && <Stack spacing={3}>
        <Text fontWeight="900">محصول‌های ثبت‌شده</Text>
        {(products.data || []).map((product) => <Card key={product.id} p={4} bg="var(--panel-surface)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" opacity={product.archived_at ? 0.72 : 1}>
          <HStack justify="space-between" align="start" gap={4} wrap="wrap">
            <Box flex="1" minW="220px"><HStack wrap="wrap"><Text fontWeight="900">{product.name}</Text><Badge colorScheme={product.archived_at ? "gray" : "green"}>{product.archived_at ? "بایگانی" : "فعال"}</Badge><Badge>{product.inbounds.length.toLocaleString("fa-IR")} اینباند</Badge><Badge>ضریب {String(product.traffic_price_multiplier)}</Badge></HStack><Text mt={2} color="var(--panel-text-muted)" fontSize="sm">{product.description || product.inbounds.join("، ")}</Text></Box>
            <HStack>{product.archived_at ? <Button colorScheme="green" variant="outline" isLoading={restore.isLoading} onClick={() => restore.mutate(product)}>بازیابی</Button> : <><Button variant="outline" onClick={() => edit(product)}>ویرایش</Button><Button colorScheme="red" variant="ghost" isLoading={archive.isLoading} onClick={() => window.confirm(`محصول «${product.name}» بایگانی شود؟`) && archive.mutate(product)}>بایگانی</Button></>}</HStack>
          </HStack>
        </Card>)}
        {!(products.data || []).length && <Text color="var(--panel-text-muted)">هنوز محصولی ثبت نشده است.</Text>}
      </Stack>}
    </Stack>
  </AppShell>;
};

export default Products;
