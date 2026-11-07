import {
  Alert, AlertIcon, Badge, Box, Button, Checkbox, FormControl, Flex,
  Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay,
  FormHelperText, FormLabel, HStack, Input, SimpleGrid, Skeleton, Stack,
  Text, Textarea, useToast,
} from "@chakra-ui/react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { EmptyState, Surface } from "design-system/Console";
import { CatalogPager } from "components/plans/CatalogPager";
import { accessGroupPermissionLabel, catalogPage, catalogText, filterNetworkOptions } from "components/plans/presentation";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { AccessGroup, AccessGroupNetworkOption, ManagedAdmin, ManagedAdminList } from "types/Admin";
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
  allowedAdminIds: number[];
};

const emptyDraft = (): Draft => ({
  id: null,
  name: "",
  description: "",
  nodeIds: [],
  inbounds: [],
  hosts: {},
  allowedAdminIds: [],
});

const adminStatusLabel = (status?: string | null) => ({
  ACTIVE: "فعال",
  SUSPENDED: "تعلیق",
  DISABLED: "غیرفعال",
}[status || ""] || status || "نامشخص");

const nodeStatusLabel = (status?: string | null) => ({
  connected: "متصل",
  connecting: "در حال اتصال",
  disabled: "غیرفعال",
  error: "خطا",
}[status || ""] || status || "نامشخص");

const fetchAdmins = async (): Promise<ManagedAdmin[]> => {
  const result: ManagedAdmin[] = [];
  let offset = 0;
  let total = 0;
  do {
    const page = await fetch<ManagedAdminList>(`/admin-management?offset=${offset}&limit=100`);
    result.push(...page.admins);
    total = page.total;
    if (!page.admins.length) break;
    offset += page.admins.length;
  } while (offset < total);
  return result;
};

export const AccessGroupManager = () => {
  const toast = useToast();
  const queryClient = useQueryClient();
  const submitLock = useRef(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [adminSearch, setAdminSearch] = useState("");
  const [networkSearch, setNetworkSearch] = useState("");
  const [selectedOnly, setSelectedOnly] = useState(false);
  const [draft, setDraft] = useState<Draft>(emptyDraft());
  const groups = useQuery<AccessGroup[], Error>("access-groups", () => fetch("/access-groups"));
  const network = useQuery<AccessGroupNetworkOption[], Error>(
    "access-group-network-options",
    () => fetch("/access-group-network-options")
  );
  const nodes = useQuery<NodeOption[], Error>("access-group-node-options", () => fetch("/nodes"));
  const admins = useQuery<ManagedAdmin[], Error>("access-group-admin-options", fetchAdmins);
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
        allowed_admin_ids: draft.allowedAdminIds,
      },
    }),
    {
      onSuccess: (group) => {
        queryClient.invalidateQueries("access-groups");
        queryClient.invalidateQueries("users");
        setDraft(emptyDraft());
        toast({ title: `گروه دسترسی «${group.name}» ذخیره شد`, status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({
          title: "ذخیره گروه دسترسی انجام نشد",
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
        toast({ title: "گروه دسترسی بایگانی شد", status: "success", duration: 3000 });
      },
      onError: (error) => {
        toast({
          title: "بایگانی گروه دسترسی انجام نشد",
          description: localizedApiError(error),
          status: "error",
          duration: 5000,
        });
      },
    }
  );

  useEffect(() => { if (!save.isLoading) submitLock.current = false; }, [save.isLoading]);
  useEffect(() => { if (save.isSuccess) setEditorOpen(false); }, [save.isSuccess]);
  const resetSearches = () => { setAdminSearch(""); setNetworkSearch(""); setSelectedOnly(false); };
  const openCreate = () => { save.reset(); setDraft(emptyDraft()); resetSearches(); setEditorOpen(true); };
  const closeEditor = () => { if (!save.isLoading) setEditorOpen(false); };
  const edit = (group: AccessGroup) => { save.reset(); resetSearches(); setEditorOpen(true); setDraft({
    id: group.id,
    name: group.name,
    description: group.description || "",
    nodeIds: [...group.node_ids],
    inbounds: normalizeAccessGroupInboundTags(group.inbounds),
    hosts: normalizeAccessGroupHostScope(group.hosts),
    allowedAdminIds: [...group.allowed_admin_ids],
  }); };

  const formReady = !network.isLoading && !nodes.isLoading && !admins.isLoading && !network.isError && !nodes.isError && !admins.isError;
  const filteredOptions = filterNetworkOptions(options, networkSearch, draft.inbounds, selectedOnly);
  const filteredGroups = (groups.data || []).filter(group => catalogText(`${group.name} ${group.description || ""} ${group.inbounds.join(" ")}`).includes(catalogText(search)));
  const currentPage = catalogPage(filteredGroups, page);
  const currentGroup = (groups.data || []).find(group => group.id === draft.id);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (save.isLoading || submitLock.current || !formReady) return;
    if (!draft.name.trim()) {
      toast({ title: "نام گروه دسترسی الزامی است", status: "warning" });
      return;
    }
    if (network.isLoading) {
      toast({ title: "گزینه‌های شبکه هنوز در حال دریافت است", status: "warning" });
      return;
    }
    if (!draft.inbounds.length) {
      toast({ title: "حداقل یک اینباند انتخاب کنید", status: "warning" });
      return;
    }
    if (missingInbounds.length || missingHosts.length) {
      toast({
        title: "انتخاب قدیمی یا غیرفعال را اصلاح کنید",
        description: missingHosts.length ? `شناسه هاست: ${missingHosts.join(", ")}` : missingInbounds.join(", "),
        status: "warning",
        duration: 5000,
      });
      return;
    }
    if (draft.inbounds.some((tag) => !(draft.hosts[tag] || []).length)) {
      toast({ title: "برای هر اینباند حداقل یک هاست فعال انتخاب کنید", status: "warning" });
      return;
    }
    submitLock.current = true;
    save.mutate();
  };

  const loadError = (groups.isError || network.isError || nodes.isError || admins.isError) && <Alert status="error"><AlertIcon /><Box>بخشی از اطلاعات گروه‌های دسترسی دریافت نشد.<Button ms={3} onClick={() => { groups.refetch(); network.refetch(); nodes.refetch(); admins.refetch(); }}>تلاش دوباره</Button></Box></Alert>;

  return <Stack spacing={4}>
    <Flex justify="space-between" align="center" gap={3} flexWrap="wrap">
      <Box minW={0}><Text as="h2" fontSize="lg" fontWeight="700">گروه‌های دسترسی</Text><Text mt={1} color="var(--panel-text-muted)" fontSize="xs">هر گروه، مسیرهای اتصال و ادمین‌های مجاز به استفاده از آن را مشخص می‌کند.</Text></Box>
      <Button colorScheme="primary" onClick={openCreate}>گروه دسترسی جدید</Button>
    </Flex>
    {loadError}
    <Surface p={{ base: 3, md: 4 }}>
      <Input type="search" aria-label="جستجوی گروه دسترسی" placeholder="جستجوی نام گروه یا اینباند…" value={search} onChange={(event) => { setSearch(event.target.value); setPage(0); }} mb={4} />
      {groups.isLoading ? <Stack spacing={3}><Skeleton h="76px" /><Skeleton h="76px" /><Skeleton h="76px" /></Stack> : !groups.isError && <>
        <Stack spacing={3}>
          {currentPage.items.map(group => <Box key={group.id} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="14px" p={{ base: 3, md: 4 }}>
            <Flex justify="space-between" align="start" gap={3} flexWrap="wrap">
              <Box flex="1" minW={0}><Text as="h3" fontWeight="700" overflowWrap="anywhere">{group.name}</Text>
                <HStack spacing={2} flexWrap="wrap" mt={2}><Badge colorScheme={group.admin_access_restricted && !group.allowed_admin_ids.length ? "gray" : "green"}>{accessGroupPermissionLabel(group)}</Badge><Badge>{group.active_user_count.toLocaleString("fa-IR")} کاربر فعال</Badge></HStack>
                <Text mt={2} color="var(--panel-text-muted)" fontSize="xs">{group.inbounds.length.toLocaleString("fa-IR")} اینباند · {Object.values(group.hosts).reduce((sum, ids) => sum + ids.length, 0).toLocaleString("fa-IR")} هاست · {group.node_ids.length ? `${group.node_ids.length.toLocaleString("fa-IR")} نود` : "همه نودها"}</Text>
                {group.description && <Text mt={2} fontSize="sm" color="var(--panel-text-muted)" noOfLines={2} title={group.description}>{group.description}</Text>}
              </Box>
              <HStack spacing={1} flexWrap="wrap"><Button minH="44px" variant="outline" onClick={() => edit(group)}>ویرایش</Button><Button minH="44px" colorScheme="red" variant="ghost" isDisabled={group.active_user_count > 0} isLoading={archive.isLoading} onClick={() => { if (window.confirm(`گروه دسترسی «${group.name}» بایگانی شود؟`)) archive.mutate(group); }}>بایگانی</Button></HStack>
            </Flex>
            {group.active_user_count > 0 && <Text fontSize="xs" color="var(--panel-text-muted)" mt={2}>تا زمانی که کاربر فعال دارد، بایگانی غیرفعال است.</Text>}
          </Box>)}
        </Stack>
        {!currentPage.items.length && <EmptyState text={search ? "گروهی با این جستجو پیدا نشد" : "هنوز گروه دسترسی ساخته نشده است"} description={search ? "نام یا اینباند دیگری جستجو کنید." : "یک گروه بسازید و اینباند، هاست و ادمین‌های مجاز آن را انتخاب کنید."} />}
        <CatalogPager count={filteredGroups.length} page={currentPage.current} onPageChange={setPage} noun="گروه" />
      </>}
    </Surface>
    <Modal isOpen={editorOpen} onClose={closeEditor} size="3xl" scrollBehavior="inside" closeOnEsc={!save.isLoading} closeOnOverlayClick={!save.isLoading}>
      <ModalOverlay /><ModalContent as="form" onSubmit={submit} mx={3} my={3} maxH="calc(100dvh - 24px)">
        <ModalHeader ps={14}>{draft.id ? "ویرایش گروه دسترسی" : "گروه دسترسی جدید"}</ModalHeader><ModalCloseButton isDisabled={save.isLoading} />
        <ModalBody><Stack spacing={5}>
          {loadError}
          {save.isError && <Alert status="error" role="alert"><AlertIcon />{localizedApiError(save.error)}</Alert>}
          <Box as="fieldset" disabled={!formReady || save.isLoading} minW={0} border={0} p={0} m={0}>
            <Stack spacing={5}>
        <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
          <FormControl isRequired><FormLabel>نام گروه</FormLabel><Input minH="44px" maxLength={128} value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} /></FormControl>
          <FormControl><FormLabel>توضیح</FormLabel><Textarea rows={2} maxLength={512} value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></FormControl>
        </SimpleGrid>
        <FormControl as="fieldset" isRequired>
          <FormLabel as="legend">۱. اینباندها و هاست‌های مجاز</FormLabel>
          <Stack direction={{ base: "column", sm: "row" }} spacing={2} mb={2}>
            <Input id="group-network-search" isRequired={false} type="search" aria-label="جستجوی اینباند یا هاست" placeholder="جستجوی اینباند یا هاست…" value={networkSearch} onChange={(event) => setNetworkSearch(event.target.value)} />
            <Checkbox id="group-selected-only" isRequired={false} minH="44px" flexShrink={0} isChecked={selectedOnly} onChange={(event) => setSelectedOnly(event.target.checked)}>فقط انتخاب‌شده‌ها</Checkbox>
          </Stack>
          <Text fontSize="xs" color="var(--panel-text-muted)" mb={2}>{draft.inbounds.length.toLocaleString("fa-IR")} اینباند و {Object.values(draft.hosts).reduce((sum, ids) => sum + ids.length, 0).toLocaleString("fa-IR")} هاست انتخاب شده</Text>
          <Stack maxH="360px" overflowY="auto" spacing={1} p={2} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
            {filteredOptions.map((inbound) => <Box key={inbound.tag} px={2} py={1} borderRadius="12px" bg={draft.inbounds.includes(inbound.tag) ? "blackAlpha.100" : "transparent"} _dark={{ bg: draft.inbounds.includes(inbound.tag) ? "whiteAlpha.50" : "transparent" }}>
              <Checkbox id={`group-inbound-${inbound.tag}`} isRequired={false} minH="44px" colorScheme="primary" isChecked={draft.inbounds.includes(inbound.tag)} onChange={(event) => setDraft((current) => {
                const inbounds = toggleAccessGroupInboundTag(current.inbounds, inbound.tag, event.target.checked);
                const hosts = { ...current.hosts };
                if (event.target.checked) hosts[inbound.tag] = hosts[inbound.tag] || [];
                else delete hosts[inbound.tag];
                return { ...current, inbounds, hosts: normalizeAccessGroupHostScope(hosts) };
              })}><Stack spacing={0} dir="ltr"><Text fontSize="sm" fontWeight="700" overflowWrap="anywhere">{inbound.tag}</Text><Text color="var(--panel-text-muted)" fontSize="xs">{inbound.protocol} · {inbound.network} · {inbound.tls || "none"}{inbound.port ? ` · ${inbound.port}` : ""}</Text></Stack></Checkbox>
              {draft.inbounds.includes(inbound.tag) && <Stack ms={7} mb={2} spacing={1}>{inbound.hosts.map((host) => <Checkbox isRequired={false} key={host.id} id={`group-host-${inbound.tag}-${host.id}`} minH="44px" colorScheme="cyan" isChecked={(draft.hosts[inbound.tag] || []).includes(host.id)} onChange={(event) => setDraft((current) => ({ ...current, hosts: toggleAccessGroupHostId(current.hosts, inbound.tag, host.id, event.target.checked) }))}><Text fontSize="sm" overflowWrap="anywhere" dir="ltr">#{host.id} · {host.remark}</Text></Checkbox>)}{(draft.hosts[inbound.tag] || []).filter((hostId) => !inbound.hosts.some((host) => host.id === hostId)).map((hostId) => <Checkbox isRequired={false} key={hostId} id={`group-stale-host-${inbound.tag}-${hostId}`} minH="44px" colorScheme="red" isChecked onChange={(event) => setDraft((current) => ({ ...current, hosts: toggleAccessGroupHostId(current.hosts, inbound.tag, hostId, event.target.checked) }))}><HStack dir="ltr"><Text fontSize="sm">#{hostId}</Text><Badge colorScheme="red">حذف‌شده / غیرفعال</Badge></HStack></Checkbox>)}{!inbound.hosts.length && <Text color="var(--panel-danger)" fontSize="xs">هاست فعالی برای این اینباند وجود ندارد.</Text>}</Stack>}
            </Box>)}
            {missingInbounds.map((tag) => <Checkbox isRequired={false} key={tag} id={`group-stale-inbound-${tag}`} minH="44px" px={2} colorScheme="red" isChecked onChange={(event) => setDraft((current) => ({ ...current, inbounds: toggleAccessGroupInboundTag(current.inbounds, tag, event.target.checked), hosts: Object.fromEntries(Object.entries(current.hosts).filter(([key]) => key !== tag)) }))}><HStack dir="ltr"><Text fontSize="sm">{tag}</Text><Badge colorScheme="red">حذف‌شده / قدیمی</Badge></HStack></Checkbox>)}
            {!!options.length && !filteredOptions.length && <Text role="status" p={2} fontSize="sm" color="var(--panel-text-muted)">موردی با این جستجو پیدا نشد؛ انتخاب‌های قبلی حفظ شده‌اند.</Text>}
            {!options.length && <Text p={2} color="var(--panel-text-muted)">اینباند قابل استفاده‌ای پیدا نشد.</Text>}
          </Stack>
          <FormHelperText>با انتخاب هر اینباند، هاست‌های همان اینباند باز می‌شوند. برای هر اینباند انتخاب‌شده حداقل یک هاست فعال لازم است.</FormHelperText>
        </FormControl>

              <Box as="details" p={3} bg="var(--panel-nested)" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
                <Box as="summary" cursor="pointer" fontSize="sm" fontWeight="600" minH="32px">نودها: {draft.nodeIds.length ? `${draft.nodeIds.length.toLocaleString("fa-IR")} نود انتخاب‌شده` : "همه نودها"}</Box><Box mt={3}>
        <FormControl as="fieldset">
          <FormLabel as="legend">محدودیت نودها</FormLabel>
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={1} p={2} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
            {(nodes.data || []).map((node) => node.id != null && <Checkbox isRequired={false} key={node.id} id={`group-node-${node.id}`} minH="44px" isChecked={draft.nodeIds.includes(node.id)} onChange={(event) => setDraft((current) => ({ ...current, nodeIds: event.target.checked ? [...new Set([...current.nodeIds, node.id!])].sort((a, b) => a - b) : current.nodeIds.filter((id) => id !== node.id) }))}><HStack><Text>{node.name}</Text>{node.status && <Badge>{nodeStatusLabel(node.status)}</Badge>}</HStack></Checkbox>)}
            {!nodes.data?.length && <Text p={2} color="var(--panel-text-muted)">نودی ثبت نشده است.</Text>}
          </SimpleGrid>
          <FormHelperText>{draft.nodeIds.length ? `${draft.nodeIds.length} نود انتخاب شده` : "همه نودها؛ فیلتر نود اعمال نمی‌شود."}</FormHelperText>
        </FormControl>

                </Box>
              </Box>
        <FormControl as="fieldset">
          <FormLabel as="legend">۲. ادمین‌های مجاز</FormLabel><Input id="group-admin-search" type="search" mb={2} aria-label="جستجوی ادمین مجاز" placeholder="جستجوی نام ادمین…" value={adminSearch} onChange={(event) => setAdminSearch(event.target.value)} />
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={1} p={2} maxH="240px" overflowY="auto" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
            {(admins.data || []).filter((admin) => admin.role === "ADMIN" && catalogText(admin.username).includes(catalogText(adminSearch))).map((admin) => (
              <Checkbox isRequired={false}
                key={admin.id}
                id={`group-admin-${admin.id}`}
                minH="44px"
                isChecked={draft.allowedAdminIds.includes(admin.id)}
                onChange={(event) => setDraft((current) => ({
                  ...current,
                  allowedAdminIds: event.target.checked
                    ? [...new Set([...current.allowedAdminIds, admin.id])].sort((a, b) => a - b)
                    : current.allowedAdminIds.filter((id) => id !== admin.id),
                }))}
              >
                <HStack><Text>{admin.username}</Text><Badge>{adminStatusLabel(admin.account_status)}</Badge></HStack>
              </Checkbox>
            ))}
            {!(admins.data || []).some((admin) => admin.role === "ADMIN") && <Text p={2} color="var(--panel-text-muted)">ادمینی برای واگذاری این گروه وجود ندارد.</Text>}
          </SimpleGrid>
          {!!adminSearch && <Text fontSize="xs" color="var(--panel-text-muted)" mt={2}>جستجو انتخاب‌های قبلی را تغییر نمی‌دهد.</Text>}
          <FormHelperText>
            {draft.allowedAdminIds.length
              ? `فقط ${draft.allowedAdminIds.length} ادمین انتخاب‌شده می‌توانند از این گروه استفاده کنند.`
              : "هیچ ادمینی انتخاب نشده: با ذخیره این تنظیم، دسترسی همه ادمین‌های واگذارشده بسته می‌شود؛ Owner همچنان دسترسی مدیریتی دارد."}
          </FormHelperText>
        </FormControl>

              {currentGroup && !currentGroup.admin_access_restricted && <Alert status="warning"><AlertIcon /><Text fontSize="sm">این گروه اکنون برای همهٔ ادمین‌ها قابل انتخاب است. با ذخیره، فقط ادمین‌های انتخاب‌شده مجاز خواهند بود؛ بدون انتخاب ادمین، گروه فقط در اختیار مالک می‌ماند.</Text></Alert>}
              <Box p={4} bg="var(--panel-nested)" borderRadius="12px" borderWidth="1px" borderColor="var(--panel-border)">
                <Text as="h3" fontSize="sm" fontWeight="700">۳. مرور و ذخیره</Text>
                <HStack mt={3} spacing={2} flexWrap="wrap"><Badge>{draft.inbounds.length.toLocaleString("fa-IR")} اینباند</Badge><Badge>{Object.values(draft.hosts).reduce((sum, ids) => sum + ids.length, 0).toLocaleString("fa-IR")} هاست</Badge><Badge>{draft.nodeIds.length ? `${draft.nodeIds.length.toLocaleString("fa-IR")} نود` : "همه نودها"}</Badge><Badge>{draft.allowedAdminIds.length ? `${draft.allowedAdminIds.length.toLocaleString("fa-IR")} ادمین مجاز` : "فقط مالک"}</Badge></HStack>
                <Text mt={3} fontSize="xs" color="var(--panel-text-muted)">{currentGroup ? `این گروه ${currentGroup.active_user_count.toLocaleString("fa-IR")} کاربر فعال دارد. تغییرات شبکه با ذخیره همگام می‌شوند.` : "پس از ساخت، گروه در فهرست دسترسی‌های مجاز برای ساخت کاربر نمایش داده می‌شود."}</Text>
              </Box>
            </Stack>
          </Box>
          {!formReady && !network.isError && !nodes.isError && !admins.isError && <Text role="status" fontSize="sm">در حال دریافت گزینه‌های شبکه و ادمین‌ها…</Text>}
        </Stack></ModalBody>
        <ModalFooter flexShrink={0} gap={2} flexWrap="wrap"><Button minH="44px" variant="ghost" onClick={() => setDraft(emptyDraft())} isDisabled={save.isLoading}>پاک‌کردن فرم</Button><Button minH="44px" variant="outline" onClick={closeEditor} isDisabled={save.isLoading}>انصراف</Button><Button minH="44px" type="submit" colorScheme="primary" isDisabled={!formReady} isLoading={save.isLoading} loadingText="در حال ذخیره">{draft.id ? "ذخیره و همگام‌سازی" : "ساخت گروه دسترسی"}</Button></ModalFooter>
      </ModalContent>
    </Modal>
  </Stack>;
};
