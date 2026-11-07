import { Alert, AlertIcon, Badge, Box, Button, Drawer, DrawerBody, DrawerCloseButton, DrawerContent, DrawerFooter, DrawerHeader, DrawerOverlay, HStack, Icon, Input, Select, Stack, Text, Tooltip, usePrefersReducedMotion, useToast } from "@chakra-ui/react";
import { BellIcon, CheckCircleIcon, ChevronDownIcon, ChevronUpIcon, FunnelIcon } from "@heroicons/react/24/outline";
import { Link } from "react-router-dom";
import { Center, Incident, alertTime, fa, incidentSummary, incidentTitle, priorityIncidents, takeNewCriticalAlerts } from "./alerts/presentation";
import { ReactNode, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "react-query";
import { useLocation } from "react-router-dom";
import useGetUser from "hooks/useGetUser";
import { fetch as api } from "service/http";
import { getAuthToken } from "utils/authStorage";
import { localizedApiError } from "utils/apiError";

const number = (value: number, unit?: string) => unit === "bytes" ? `${fa(value / 1024 ** 3)} گیگ` : fa(value);
function Details({item}: {item: Incident}) {
  const d = item.details;
  if (item.resource === "financial") return <Text fontSize="sm" lineHeight="2">مانده: {fa(d.balance_toman)} تومان · مبنای آخرین شارژ: {fa(d.basis_toman)} تومان · بدهی: {d.debt_percent == null ? "بدون مبنای شارژ" : `${fa(d.debt_percent)}٪`}<br />حد فریز: {fa(d.freeze_percent)}٪ بدهی · حد قطع: {fa(d.cutoff_percent)}٪ بدهی<br />فاصله تا فریز: {fa(d.remaining_to_freeze_toman)} تومان · تا قطع: {fa(d.remaining_to_cutoff_toman)} تومان</Text>;
  if ("limit" in d) return <Text fontSize="sm">استفاده‌شده: {number(d.used,d.unit)} · سقف: {number(d.limit,d.unit)} · باقی‌مانده: {number(d.remaining,d.unit)} · {fa(d.percent)}٪</Text>;
  if ("remaining_days" in d) return <Text fontSize="sm">روز باقی‌مانده: {fa(d.remaining_days)} · پایان: {d.expiry_date}</Text>;
  return <Text fontSize="sm">حساب ادمین محدود شده؛ وضعیت و علت را در مدیریت ادمین‌ها بررسی کنید.</Text>;
}

// A single query/stream owns the compact trigger, dashboard summary and Drawer.
export function AlertCenter({ children }: { children: (ui: { trigger: ReactNode; summary: ReactNode }) => ReactNode }) {
  const { userData, getUserIsSuccess } = useGetUser();
  const client = useQueryClient();
  const toast = useToast();
  const location = useLocation();
  const actor = userData.username;
  const [open,setOpen] = useState(false);
  const [filtersOpen,setFiltersOpen] = useState(false);
  const [diagnosticsOpen,setDiagnosticsOpen] = useState(false);
  const [expanded,setExpanded] = useState<number | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const reduceMotion = usePrefersReducedMotion();
  const [status,setStatus] = useState("active");
  const [severity,setSeverity] = useState("");
  const [username,setUsername] = useState("");
  const [draft,setDraft] = useState("");
  const [before,setBefore] = useState<number | null>(null);
  const [busy,setBusy] = useState<number | null>(null);
  const [live,setLive] = useState(false);
  const baseKey = ["alert-center",actor];
  const announce = (data: Center) => {
      const fresh = takeNewCriticalAlerts(actor, data.items);
      if (fresh.length) toast({id:`critical-incident-${actor}-${fresh.map(i=>`${i.id}:${i.revision}`).join(",")}`,title:fresh.length === 1 ? `هشدار حیاتی برای ${fresh[0].admin_username}` : `${fa(fresh.length)} هشدار حیاتی جدید`,description:fresh.length === 1 ? incidentSummary(fresh[0]) : "برای بررسی حساب‌های مربوط، مرکز هشدارها را باز کنید.",status:"error",duration:6000,isClosable:true});
    };
  const summary = useQuery<Center,Error>(baseKey,()=>api("/admin-management/alert-center"), {
    enabled:getUserIsSuccess, staleTime:15000, refetchInterval:60000, refetchIntervalInBackground:false,
    onSuccess: announce,
  });
  const filtered = status!=="active" || severity!=="" || username!=="" || before!==null;
  const params = new URLSearchParams({status,...(severity?{severity}:{}),...(username?{username}:{}),...(before?{before:String(before)}:{})});
  const detail = useQuery<Center,Error>([...baseKey,status,severity,username,before],()=>api(`/admin-management/alert-center?${params}`),{enabled:getUserIsSuccess && open && filtered, staleTime:10000});
  const query = filtered ? detail : summary;
  const counts = summary.data?.counts;
  useEffect(()=>{
    if (!getUserIsSuccess) return;
    let disposed=false;
    let generation=0;
    let controller: AbortController | undefined;
    let retry: ReturnType<typeof setTimeout> | undefined;
    const connect=async()=>{
      if (disposed || document.hidden) return;
      const attempt=++generation;
      controller?.abort();
      controller=new AbortController();
      try {
        const base=import.meta.env.VITE_BASE_API || "/api/";
        const response=await window.fetch(`${base.replace(/\/$/,"")}/admin-management/alert-events`,{headers:{Authorization:`Bearer ${getAuthToken()}`},signal:controller.signal});
        if (!response.ok || !response.body) throw new Error("stream unavailable");
        setLive(true);
        const reader=response.body.getReader();
        const decoder=new TextDecoder();
        let buffer="";
        while (!disposed) {
          const chunk=await reader.read();
          if (chunk.done) break;
          buffer+=decoder.decode(chunk.value,{stream:true});
          let boundary;
          while ((boundary=buffer.indexOf("\n\n"))>=0) {
            const event=buffer.slice(0,boundary); buffer=buffer.slice(boundary+2);
            if(event.includes("event: alerts")) client.invalidateQueries(["alert-center",actor]);
          }
        }
      } catch (_) { /* The 60-second query is the independent fallback. */ }
      finally { if (!disposed && attempt===generation) {setLive(false);retry=setTimeout(connect,30000);} }
    };
    const visibility=()=>{if(document.hidden){generation++;controller?.abort();if(retry)clearTimeout(retry);setLive(false);}else{if(retry)clearTimeout(retry);client.invalidateQueries(["alert-center",actor]);connect();}};
    connect();document.addEventListener("visibilitychange",visibility);
    return()=>{disposed=true;generation++;controller?.abort();if(retry)clearTimeout(retry);document.removeEventListener("visibilitychange",visibility);};
  },[actor,getUserIsSuccess,client]);
  const markSeen=async(item:Incident)=>{setBusy(item.id);try{await api(`/admin-management/alert-center/${item.id}/seen?revision=${item.revision}`,{method:"POST"});client.invalidateQueries(baseKey);}catch(error){toast({title:localizedApiError(error),status:"error"});}finally{setBusy(null);}};
  const stale=!summary.data?.checked_at || Date.now()-new Date(summary.data.checked_at+"Z").getTime()>300000;
  const inherited = Boolean(summary.data?.inherited_restriction);
  const total = (counts?.critical || 0) + (counts?.warning || 0);
  const isOwner = userData.is_sudo || userData.role === "OWNER";
  const attention = inherited || Boolean(counts?.critical);
  const uncertain = summary.isError || (summary.isSuccess && stale);
  const badge = total ? total > 99 ? "۹۹+" : fa(total) : inherited || uncertain ? "!" : null;
  const triggerLabel = summary.isLoading ? "مرکز هشدارها؛ در حال دریافت" : `${counts ? `${fa(counts.critical)} هشدار حیاتی و ${fa(counts.warning)} هشدار مهم` : "دریافت هشدارها ناموفق است"}${inherited ? "؛ حساب بالادستی محدود شده" : ""}${uncertain ? "؛ اطلاعات ممکن است قدیمی باشد" : ""}`;
  const groups = new Map<string,Incident[]>();
  priorityIncidents(query.data?.items || []).forEach(i=>groups.set(i.admin_username,[...(groups.get(i.admin_username)||[]),i]));
  const preview = priorityIncidents(summary.data?.items || []).filter(i=>!i.resolved_at).slice(0,3);
  const trigger = getUserIsSuccess && <Tooltip label={triggerLabel} openDelay={300}>
    <Button ref={triggerRef} variant="ghost" minW="44px" h="44px" px={2} position="relative" aria-label={`مرکز هشدارها؛ ${triggerLabel}`} aria-haspopup="dialog" aria-expanded={open} onClick={()=>setOpen(!open)} color={attention ? "var(--panel-danger)" : "var(--panel-text-body)"}>
      <Icon as={BellIcon} boxSize={5} aria-hidden="true" />
      {badge && <Badge position="absolute" top="2px" insetEnd="0" minW="18px" px={1} borderRadius="full" fontSize="10px" textAlign="center" bg={attention ? "var(--panel-danger)" : "var(--panel-warning)"} color="var(--panel-bg)">{badge}</Badge>}
    </Button>
  </Tooltip>;
  const dashboardSummary = getUserIsSuccess && location.pathname === "/" && (total > 0 || inherited) && <Box as="section" aria-label="خلاصه هشدارهای فعال" borderWidth="1px" borderColor="var(--panel-border)" borderRadius="16px" bg="var(--panel-surface)" p={{base:4,md:5}} mb={5}>
    <HStack justify="space-between" gap={3} mb={3} flexWrap="wrap">
      <HStack flexWrap="wrap"><Text as="h2" fontWeight="700" fontSize="sm">نیاز به توجه</Text>{!!counts?.critical && <Badge colorScheme="red">{fa(counts.critical)} حیاتی</Badge>}{!!counts?.warning && <Badge colorScheme="orange">{fa(counts.warning)} مهم</Badge>}</HStack>
      <Button size="sm" variant="ghost" onClick={()=>setOpen(true)}>همه هشدارها</Button>
    </HStack>
    {inherited && <Text color="var(--panel-danger)" fontSize="sm" mb={3}>محدودیت حساب بالادستی روی حساب شما اثر گذاشته است؛ با ادمین بالادستی پیگیری کنید.</Text>}
    <Stack spacing={3}>{preview.map(item=><HStack key={item.id} align="start" justify="space-between" gap={3}>
      <Box minW={0}><Text fontSize="sm" fontWeight="600" overflowWrap="anywhere"><Box as="span" dir="ltr" sx={{unicodeBidi:"isolate"}}>{item.admin_username}</Box> · {incidentTitle(item)}</Text><Text fontSize="xs" color="var(--panel-text-muted)" mt={1}>{incidentSummary(item)}</Text></Box>
      <Button size="sm" variant="ghost" flexShrink={0} onClick={()=>{setExpanded(item.id);setOpen(true);}}>بررسی</Button>
    </HStack>)}</Stack>
    {summary.data?.next_before && <Text fontSize="xs" color="var(--panel-text-muted)" mt={3}>خلاصهٔ موارد اخیر؛ فهرست کامل در مرکز هشدارها در دسترس است.</Text>}
  </Box>;
  return <>
    {children({trigger,summary:dashboardSummary})}
    {getUserIsSuccess && <Drawer isOpen={open} onClose={()=>setOpen(false)} placement="left" size="md" finalFocusRef={triggerRef}>
      <DrawerOverlay bg="blackAlpha.600" />
      <DrawerContent style={{margin:0}} w={{base:"100vw",md:"full"}} borderRadius={{base:0,md:"var(--radius-panel)"}} bg="var(--panel-surface)" color="var(--panel-text)" maxW={{base:"100vw",md:"520px"}} h="100dvh" maxH="100dvh" motionProps={reduceMotion ? {initial:false,animate:{x:0,y:0},exit:{x:0,y:0},transition:{duration:0}} : {transition:{type:"tween",duration:0.18,ease:[0.2,0.8,0.2,1]}}}>
        <DrawerCloseButton aria-label="بستن مرکز هشدارها" style={{left:12,right:"auto"}} top={4} minW="44px" minH="44px" />
        <DrawerHeader flexShrink={0} borderBottomWidth="1px" borderColor="var(--panel-border)" pe={16} pt={6}>
          <Text>مرکز هشدارها</Text><Text fontSize="xs" fontWeight="400" color="var(--panel-text-muted)" mt={2}>{isOwner ? "هشدار همه ادمین‌ها؛ به تفکیک حساب" : "هشدارهای خودتان و زیرمجموعه‌هایتان"}</Text>
          <HStack mt={3} flexWrap="wrap" aria-live="polite"><Badge colorScheme="red">حیاتی: {counts ? fa(counts.critical) : "—"}</Badge><Badge colorScheme="orange">مهم: {counts ? fa(counts.warning) : "—"}</Badge></HStack>
        </DrawerHeader>
        <DrawerBody minH={0} p={{base:4,md:5}} overscrollBehavior="contain">
          {inherited && <Alert status="error" mb={4} alignItems="start"><AlertIcon /><Text fontSize="sm">محدودیت از حساب بالادستی اعمال شده است؛ برای رفع آن با ادمین بالادستی پیگیری کنید.</Text></Alert>}
          {summary.isError && <Alert status="error" mb={4} flexWrap="wrap"><AlertIcon /><Text fontSize="sm" flex="1">دریافت هشدارها ناموفق است؛ اطلاعات قبلی ممکن است قدیمی باشد.</Text><Button size="sm" onClick={()=>summary.refetch()}>تلاش مجدد</Button></Alert>}
          {stale && summary.isSuccess && <Alert status="warning" mb={4} alignItems="start"><AlertIcon /><Text fontSize="sm">اطلاعات هشدارها ممکن است قدیمی باشد. جزئیات دریافت را بررسی کنید.</Text></Alert>}
          <HStack mb={4} gap={3}>
            <Select aria-label="وضعیت هشدار" flex="1" value={status} onChange={e=>{setStatus(e.target.value);setBefore(null);}}><option value="active">فعال</option><option value="resolved">رفع‌شده</option><option value="all">همه</option></Select>
            <Button size="sm" variant="outline" leftIcon={<Icon as={FunnelIcon} boxSize={4} aria-hidden="true" />} aria-expanded={filtersOpen} aria-controls="alert-center-filters" onClick={()=>setFiltersOpen(!filtersOpen)}>فیلترها{severity || username ? " · فعال" : ""}</Button>
          </HStack>
          <Stack id="alert-center-filters" hidden={!filtersOpen} display={filtersOpen ? "flex" : "none"} spacing={3} mb={4} p={3} borderWidth="1px" borderColor="var(--panel-border)" borderRadius="12px">
            <Select aria-label="اهمیت هشدار" value={severity} onChange={e=>{setSeverity(e.target.value);setBefore(null);}}><option value="">همه اهمیت‌ها</option><option value="critical">حیاتی</option><option value="warning">مهم</option></Select>
            <HStack><Input aria-label="جستجوی ادمین هشدار" placeholder="نام کاربری ادمین" minW={0} value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"){setUsername(draft.trim());setBefore(null);}}}/><Button size="sm" onClick={()=>{setUsername(draft.trim());setBefore(null);}}>فیلتر</Button></HStack>
          </Stack>
          {filtered && query.isError && <Alert status="error" mb={4}><AlertIcon />{localizedApiError(query.error)}</Alert>}
          {query.isLoading && <Text role="status" py={8} textAlign="center" color="var(--panel-text-muted)">در حال دریافت…</Text>}
          {query.isSuccess && query.data?.items.length===0 && <Stack align="center" py={10} spacing={3} textAlign="center"><Icon as={CheckCircleIcon} boxSize={8} color="var(--panel-accent)" aria-hidden="true" /><Text fontWeight="600">{filtered ? "هشداری با این فیلتر وجود ندارد." : "هشدار فعالی وجود ندارد"}</Text><Text fontSize="sm" color="var(--panel-text-muted)">{filtered ? "فیلتر یا وضعیت انتخاب‌شده را بررسی کنید." : "هشدارهای جدید از همین بخش در دسترس خواهند بود."}</Text></Stack>}
          <Stack spacing={5}>
            {[...groups].map(([name,items])=><Box key={name} minW={0}><Text fontSize="sm" fontWeight="700" mb={3} dir="ltr" overflowWrap="anywhere">{name}</Text><Stack spacing={3}>{items.map(item=><Box as="article" key={item.id} minW={0} borderWidth="1px" borderRadius="12px" p={4} bg="var(--panel-nested)" borderColor={item.severity==="critical" && !item.resolved_at ? "var(--panel-danger-border)":"var(--panel-border)"}>
              <HStack justify="space-between" gap={2} flexWrap="wrap"><Text fontSize="sm" fontWeight="600" overflowWrap="anywhere">{incidentTitle(item)}</Text><Badge colorScheme={item.resolved_at?"green":item.severity==="critical"?"red":"orange"}>{item.resolved_at?"رفع‌شده":item.severity==="critical"?"حیاتی":"مهم"}</Badge></HStack>
              <Text fontSize="sm" lineHeight="1.9" mt={2} color="var(--panel-text-body)">{incidentSummary(item)}</Text>
              <Button variant="link" fontSize="xs" minH="36px" mt={1} rightIcon={<Icon as={expanded===item.id ? ChevronUpIcon : ChevronDownIcon} boxSize={3} aria-hidden="true" />} aria-expanded={expanded===item.id} aria-controls={`alert-details-${item.id}`} onClick={()=>setExpanded(expanded===item.id ? null : item.id)}>{expanded===item.id ? "بستن جزئیات" : "جزئیات و اقدام"}</Button>
              <Box id={`alert-details-${item.id}`} hidden={expanded!==item.id} pt={2}><Details item={item}/><Text fontSize="xs" color="var(--panel-text-muted)" mt={3}>{alertTime(item.opened_at)}</Text>{isOwner && <Button as={Link} to="/admins/" variant="outline" size="sm" mt={3} onClick={()=>setOpen(false)}>مدیریت حساب ادمین</Button>}{!isOwner && <Text fontSize="xs" mt={3} color="var(--panel-text-muted)">برای تغییر محدودیت‌ها با ادمین بالادستی پیگیری کنید.</Text>}</Box>
              <HStack mt={3} justify="space-between" flexWrap="wrap" gap={2}><Button size="sm" variant="ghost" isDisabled={item.seen} isLoading={busy===item.id} onClick={()=>markSeen(item)}>{item.seen?"دیده شده":"دیده شد"}</Button>{!item.resolved_at && <Text fontSize="xs" color="var(--panel-text-muted)">تا رفع مشکل فعال می‌ماند</Text>}</HStack>
            </Box>)}</Stack></Box>)}
          </Stack>
          <HStack mt={5} justify="space-between" flexWrap="wrap" gap={2}><Button size="sm" onClick={()=>setBefore(null)} isDisabled={before===null}>جدیدترین</Button><Button size="sm" isDisabled={!query.data?.next_before} onClick={()=>setBefore(query.data?.next_before || null)}>موارد قدیمی‌تر</Button></HStack>
        </DrawerBody>
        <DrawerFooter flexShrink={0} display="block" borderTopWidth="1px" borderColor="var(--panel-border)" px={5} py={3} pb="max(12px, env(safe-area-inset-bottom))">
          <Button size="sm" variant="ghost" aria-expanded={diagnosticsOpen} aria-controls="alert-center-diagnostics" onClick={()=>setDiagnosticsOpen(!diagnosticsOpen)}>وضعیت دریافت هشدارها</Button>
          <Box id="alert-center-diagnostics" hidden={!diagnosticsOpen} pt={2}><Text fontSize="xs" lineHeight="1.9" color="var(--panel-text-muted)">{live?"دریافت تغییرات متصل است":"تازه‌سازی دوره‌ای هر ۶۰ ثانیه"}<br />آخرین بررسی جامع: {alertTime(summary.data?.checked_at || null)}</Text></Box>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>}
  </>;
}
