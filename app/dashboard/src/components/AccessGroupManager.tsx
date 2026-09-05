import {
  Alert, AlertIcon, Badge, Box, Button, Card, Checkbox, FormControl,
  FormHelperText, FormLabel, HStack, Input, SimpleGrid, Skeleton, Stack,
  Text, Textarea, useToast,
} from "@chakra-ui/react";
import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { AccessGroup, AccessGroupNetworkOption } from "types/Admin";
import {
  missingAccessGroupHostIds,
  missingAccessGroupInboundTags,
  normalizeAccessGroupHostScope,
  normalizeAccessGroupInboundTags,
  toggleAccessGroupHostId,
  toggleAccessGroupInboundTag,
} from "utils/accessGroupScope";
import { localizedApiError } from "utils/apiError";

type NodeOption = { id?: number | null; name: string; status?: string | null };
type Draft = {
  id: number | null;
  name: string;
  description: string;
  nodeIds: number[];
  inbounds: string[];
  hosts: Record<string, number[]>;
};

const emptyDraft = (): Draft => ({
  id: null,
  name: "",
  description: "",
  nodeIds: [],
  inbounds: [],
  hosts: {},
});

export const AccessGroupManager = () => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Draft>(emptyDraft());
  const groups = useQuery<AccessGroup[], Error>("access-groups", () => fetch("/access-groups"));
  const network = useQuery<AccessGroupNetworkOption[], Error>(
    "access-group-network-options",
    () => fetch("/access-group-network-options")
  );
  const nodes = useQuery<NodeOption[], Error>("access-group-node-options", () => fetch("/nodes"));
  const options = network.data || [];
  const missingInbounds = network.isLoading
    ? []
    : missingAccessGroupInboundTags(draft.inbounds, options);
  const missingHosts = network.isLoading
    ? []
    : missingAccessGroupHostIds(draft.hosts, options);

  const save = useMutation(
    () => fetch<AccessGroup>(draft.id ? `/access-groups/${draft.id}` : "/access-groups", {
      method: draft.id ? "PUT" : "POST",
      body: {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        node_ids: draft.nodeIds,
        inbounds: normalizeAccessGroupInboundTags(draft.inbounds),
        hosts: normalizeAccessGroupHostScope(draft.hosts),
      },
    }),
    {
      onSuccess: (group) => {
        queryClient.invalidateQueries("access-groups");
        queryClient.invalidateQueries("users");
        setDraft(emptyDraft());
        toast({ title: `Access Group «${group.name}» ذخیره شد`, status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({
          title: "ذخیره Access Group انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  const archive = useMutation(
    (group: AccessGroup) => fetch(`/access-groups/${group.id}`, { method: "DELETE" }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("access-groups");
        setDraft(emptyDraft());
        toast({ title: "Access Group بایگانی شد", status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({
          title: "بایگانی Access Group انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  const edit = (group: AccessGroup) => setDraft({
    id: group.id,
    name: group.name,
    description: group.description || "",
    nodeIds: [...group.node_ids],
    inbounds: normalizeAccessGroupInboundTags(group.inbounds),
    hosts: normalizeAccessGroupHostScope(group.hosts),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.name.trim()) {
      toast({ title: "نام Access Group الزامی است", status: "warning" });
      return;
    }
    if (network.isLoading) {
      toast({ title: "گزینه‌های شبکه هنوز در حال دریافت است", status: "warning" });
      return;
    }
    if (!draft.inbounds.length) {
      toast({ title: "حداقل یک Inbound انتخاب کنید", status: "warning" });
      return;
    }
    if (missingInbounds.length || missingHosts.length) {
      toast({
        title: "انتخاب قدیمی یا غیرفعال را اصلاح کنید",
        description: missingHosts.length ? `Host ID: ${missingHosts.join(", ")}` : missingInbounds.join(", "),
        status: "warning",
        duration: 5000,
      });
      return;
    }
    if (draft.inbounds.some((tag) => !(draft.hosts[tag] || []).length)) {
      toast({ title: "برای هر Inbound حداقل یک Host فعال انتخاب کنید", status: "warning" });
      return;
    }
    save.mutate();
  };

  if (groups.isLoading || network.isLoading || nodes.isLoading) {
    return <Stack spacing={3}><Skeleton h="64px" /><Skeleton h="180px" /><Skeleton h="96px" /></Stack>;
  }
  if (groups.isError || network.isError || nodes.isError) {
    return <Alert status="error"><AlertIcon />گزینه‌های Access Group دریافت نشدند.<Button ms={3} onClick={() => { groups.refetch(); network.refetch(); nodes.refetch(); }}>تلاش دوباره</Button></Alert>;
  }

  return <Stack spacing={5}>
    <Alert status="info" variant="left-accent"><AlertIcon />Inbound، Host و Node فقط اینجا مدیریت می‌شوند. ویرایش گروه، کاربران فعال همان گروه را همگام می‌کند.</Alert>
    <Card as="form" onSubmit={submit} p={{ base: 3, md: 4 }} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
      <HStack justify="space-between" align="start" mb={4} gap={3} wrap="wrap"><Box><Text fontWeight="800">{draft.id ? "ویرایش Access Group" : "Access Group جدید"}</Text><Text mt={1} color="gray.600" _dark={{ color: "gray.400" }} fontSize="sm">انتخاب خالی هرگز به معنی همه نیست؛ فقط Node خالی یعنی بدون فیلتر Node.</Text></Box>{draft.id && <Button minH="44px" variant="ghost" onClick={() => setDraft(emptyDraft())}>انصراف از ویرایش</Button>}</HStack>
      <Stack spacing={4}>
        <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
          <FormControl isRequired><FormLabel>نام گروه</FormLabel><Input minH="44px" maxLength={128} value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
          <FormControl><FormLabel>توضیح</FormLabel><Textarea maxLength={512} value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
        </SimpleGrid>
        <FormControl>
          <FormLabel>Nodeها</FormLabel>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={1} p={2} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">
            {(nodes.data || []).map((node) => node.id != null && <Checkbox key={node.id} minH="44px" isChecked={draft.nodeIds.includes(node.id)} onChange={(event) => setDraft((current) => ({ ...current, nodeIds: event.target.checked ? [...new Set([...current.nodeIds, node.id!])].sort((a, b) => a - b) : current.nodeIds.filter((id) => id !== node.id) }))}><HStack><Text>{node.name}</Text>{node.status && <Badge>{node.status}</Badge>}</HStack></Checkbox>)}
            {!nodes.data?.length && <Text p={2} color="gray.500">Nodeی ثبت نشده است.</Text>}
          </SimpleGrid>
          <FormHelperText>{draft.nodeIds.length ? `${draft.nodeIds.length} Node انتخاب شده` : "همه Nodeها؛ فیلتر Node اعمال نمی‌شود."}</FormHelperText>
        </FormControl>
        <FormControl isRequired>
          <FormLabel>Inbound و Hostهای مجاز</FormLabel>
          <Stack maxH="360px" overflowY="auto" spacing={1} p={2} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px">
            {options.map((inbound) => <Box key={inbound.tag} px={2} py={1} borderRadius="8px" bg={draft.inbounds.includes(inbound.tag) ? "blackAlpha.100" : "transparent"} _dark={{ bg: draft.inbounds.includes(inbound.tag) ? "whiteAlpha.50" : "transparent" }}>
              <Checkbox minH="44px" colorScheme="primary" isChecked={draft.inbounds.includes(inbound.tag)} onChange={(event) => setDraft((current) => {
                const inbounds = toggleAccessGroupInboundTag(current.inbounds, inbound.tag, event.target.checked);
                const hosts = { ...current.hosts };
                if (event.target.checked) hosts[inbound.tag] = hosts[inbound.tag] || [];
                else delete hosts[inbound.tag];
                return { ...current, inbounds, hosts: normalizeAccessGroupHostScope(hosts) };
              })}><Stack spacing={0} dir="ltr"><Text fontSize="sm" fontWeight="700" overflowWrap="anywhere">{inbound.tag}</Text><Text color="gray.500" fontSize="xs">{inbound.protocol} · {inbound.network} · {inbound.tls || "none"}{inbound.port ? ` · ${inbound.port}` : ""}</Text></Stack></Checkbox>
              {draft.inbounds.includes(inbound.tag) && <Stack ms={7} mb={2} spacing={1}>{inbound.hosts.map((host) => <Checkbox key={host.id} minH="44px" colorScheme="cyan" isChecked={(draft.hosts[inbound.tag] || []).includes(host.id)} onChange={(event) => setDraft((current) => ({ ...current, hosts: toggleAccessGroupHostId(current.hosts, inbound.tag, host.id, event.target.checked) }))}><Text fontSize="sm" overflowWrap="anywhere" dir="ltr">#{host.id} · {host.remark}</Text></Checkbox>)}{(draft.hosts[inbound.tag] || []).filter((hostId) => !inbound.hosts.some((host) => host.id === hostId)).map((hostId) => <Checkbox key={hostId} minH="44px" colorScheme="red" isChecked onChange={(event) => setDraft((current) => ({ ...current, hosts: toggleAccessGroupHostId(current.hosts, inbound.tag, hostId, event.target.checked) }))}><HStack dir="ltr"><Text fontSize="sm">#{hostId}</Text><Badge colorScheme="red">حذف‌شده / غیرفعال</Badge></HStack></Checkbox>)}{!inbound.hosts.length && <Text color="red.500" fontSize="xs">Host فعال برای این Inbound وجود ندارد.</Text>}</Stack>}
            </Box>)}
            {missingInbounds.map((tag) => <Checkbox key={tag} minH="44px" px={2} colorScheme="red" isChecked onChange={(event) => setDraft((current) => ({ ...current, inbounds: toggleAccessGroupInboundTag(current.inbounds, tag, event.target.checked), hosts: Object.fromEntries(Object.entries(current.hosts).filter(([key]) => key !== tag)) }))}><HStack dir="ltr"><Text fontSize="sm">{tag}</Text><Badge colorScheme="red">حذف‌شده / قدیمی</Badge></HStack></Checkbox>)}
            {!options.length && <Text p={2} color="gray.500">Inbound واجدشرایطی پیدا نشد.</Text>}
          </Stack>
          <FormHelperText>برای هر Inbound انتخاب‌شده، حداقل یک Host فعال لازم است.</FormHelperText>
        </FormControl>
        <HStack justify="flex-end" wrap="wrap"><Button minH="44px" variant="ghost" onClick={() => setDraft(emptyDraft())}>پاک‌کردن فرم</Button><Button minH="44px" type="submit" colorScheme="primary" isLoading={save.isLoading}>{draft.id ? "ذخیره و همگام‌سازی" : "ساخت Access Group"}</Button></HStack>
      </Stack>
    </Card>
    <Stack spacing={2}>
      <Text fontWeight="800">گروه‌های فعال</Text>
      {(groups.data || []).map((group) => <HStack key={group.id} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="10px" align="start" gap={3} wrap="wrap"><Box flex="1" minW="220px"><HStack wrap="wrap"><Text fontWeight="700">{group.name}</Text><Badge colorScheme="cyan">{group.active_user_count} کاربر فعال</Badge><Badge>{group.inbounds.length} Inbound</Badge><Badge>{group.node_ids.length ? `${group.node_ids.length} Node` : "همه Nodeها"}</Badge></HStack><Text mt={1} color="gray.600" _dark={{ color: "gray.400" }} fontSize="sm">{group.description || group.inbounds.join(", ")}</Text></Box><HStack><Button minH="44px" variant="outline" onClick={() => edit(group)}>ویرایش</Button><Button minH="44px" colorScheme="red" variant="ghost" isDisabled={group.active_user_count > 0} isLoading={archive.isLoading} onClick={() => { if (window.confirm(`Access Group «${group.name}» بایگانی شود؟`)) archive.mutate(group); }}>بایگانی</Button></HStack></HStack>)}
      {!groups.data?.length && <Text role="status" color="gray.500">هنوز Access Group ساخته نشده است.</Text>}
    </Stack>
  </Stack>;
};
