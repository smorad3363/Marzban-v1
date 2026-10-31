import { Alert, AlertIcon, Badge, Box, Button, Collapse, HStack, Input, Select, Stack, Text, useToast } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "react-query";
import { useLocation } from "react-router-dom";
import useGetUser from "hooks/useGetUser";
import { fetch as api } from "service/http";
import { getAuthToken } from "utils/authStorage";
import { localizedApiError } from "utils/apiError";

type Incident = { id: number; admin_id: number; admin_username: string; resource: string; state: string; severity: string; revision: number; seen: boolean; resolved_at: string | null; opened_at: string; details: Record<string, any> };
type Center = { items: Incident[]; counts: { critical: number; warning: number }; next_before: number | null; inherited_restriction: boolean; checked_at: string | null };
const labels: Record<string,string> = { financial: "موجودی و بدهی", accounts: "سقف تعداد اکانت", create_operations: "سهمیه ساخت و تغییر زمان", renewals: "سهمیه تمدید", renewal_budget: "سقف تمدید", provisioning_volume: "سقف حجم ساخت", devices: "ظرفیت دستگاه", traffic: "اعتبار حجم", trials: "سهمیه تست", expiry: "انقضای حساب", account: "وضعیت حساب" };
const states: Record<string,string> = {low:"کمبود موجودی",empty:"اتمام موجودی",frozen:"فریز مالی",disabled:"غیرفعال",suspended:"تعلیق",near_limit:"نزدیک محدودیت",exhausted:"سهمیه تمام شده",expired:"منقضی شده"};
const fa = (n: number) => n.toLocaleString("fa-IR", { maximumFractionDigits: 2 });
const announced = new Map<string,string>();
const number = (value: number, unit?: string) => unit === "bytes" ? `${fa(value / 1024 ** 3)} گیگ` : fa(value);
function Details({item}: {item: Incident}) {
  const d = item.details;
  if (item.resource === "financial") return <Text fontSize="sm" lineHeight="2">مانده: {fa(d.balance_toman)} تومان · مبنای آخرین شارژ: {fa(d.basis_toman)} تومان · بدهی: {d.debt_percent == null ? "بدون مبنای شارژ" : `${fa(d.debt_percent)}٪`}<br />حد فریز: {fa(d.freeze_percent)}٪ بدهی · حد قطع: {fa(d.cutoff_percent)}٪ بدهی<br />فاصله تا فریز: {fa(d.remaining_to_freeze_toman)} تومان · تا قطع: {fa(d.remaining_to_cutoff_toman)} تومان</Text>;
  if ("limit" in d) return <Text fontSize="sm">استفاده‌شده: {number(d.used,d.unit)} · سقف: {number(d.limit,d.unit)} · باقی‌مانده: {number(d.remaining,d.unit)} · {fa(d.percent)}٪</Text>;
  if ("remaining_days" in d) return <Text fontSize="sm">روز باقی‌مانده: {fa(d.remaining_days)} · پایان: {d.expiry_date}</Text>;
  return <Text fontSize="sm">حساب ادمین محدود شده؛ وضعیت و علت را در مدیریت ادمین‌ها بررسی کنید.</Text>;
}

export function AlertCenter() {
  const { userData, getUserIsSuccess } = useGetUser();
  const client = useQueryClient();
  const toast = useToast();
  const location = useLocation();
  const actor = userData.username;
  const [open,setOpen] = useState(location.pathname === "/");
  const [status,setStatus] = useState("active");
  const [severity,setSeverity] = useState("");
  const [username,setUsername] = useState("");
  const [draft,setDraft] = useState("");
  const [before,setBefore] = useState<number | null>(null);
  const [busy,setBusy] = useState<number | null>(null);
  const [live,setLive] = useState(false);
  const baseKey = ["alert-center",actor];
  const summary = useQuery<Center,Error>(baseKey,()=>api("/admin-management/alert-center"), {
    enabled:getUserIsSuccess, staleTime:15000, refetchInterval:60000, refetchIntervalInBackground:false,
    onSuccess: data => {
      const signature = data.items.filter(i=>!i.resolved_at).map(i=>`${i.id}:${i.revision}`).sort().join(",");
      const previous = announced.get(actor);
      if (signature && signature !== previous) toast({id:`incident-${actor}-${signature}`,title:`${fa(data.counts.critical)} هشدار حیاتی و ${fa(data.counts.warning)} هشدار مهم`,description:"هشدارهای فعال را بررسی کنید؛ مشاهده‌کردن، مشکل را رفع نمی‌کند.",status:data.counts.critical ? "error" : "warning",duration:7000,isClosable:true});
      announced.set(actor,signature);
    },
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
  if (!getUserIsSuccess) return null;
  const stale=!summary.data?.checked_at || Date.now()-new Date(summary.data.checked_at+"Z").getTime()>300000;
  const groups = new Map<string,Incident[]>();
  [...(query.data?.items || [])].sort((a,b)=>Number(b.severity==="critical")-Number(a.severity==="critical")).forEach(i=>groups.set(i.admin_username,[...(groups.get(i.admin_username)||[]),i]));
  return <Box position="sticky" top={2} zIndex={20} mb={5} borderWidth="1px" borderColor={counts?.critical ? "var(--panel-danger-border)" : "var(--panel-border)"} borderRadius="12px" bg="var(--panel-surface)" aria-label="مرکز هشدارها">
    <HStack p={3} flexWrap="wrap" justify="space-between" aria-live="polite">
      <HStack flexWrap="wrap"><Text fontWeight="850">هشدارهای فعال</Text><Badge colorScheme="red">حیاتی: {counts ? fa(counts.critical) : "—"}</Badge><Badge colorScheme="orange">مهم: {counts ? fa(counts.warning) : "—"}</Badge></HStack>
      <Button size="sm" onClick={()=>setOpen(!open)} aria-expanded={open}>{open ? "جمع‌کردن جزئیات" : "بررسی هشدارها"}</Button>
    </HStack>
    <Text px={3} pb={2} fontSize="xs" color="var(--panel-text-muted)">{live?"دریافت تغییرات متصل است":"تازه‌سازی دوره‌ای هر ۶۰ ثانیه"} · {summary.data?.checked_at ? `آخرین بررسی جامع: ${new Date(summary.data.checked_at+"Z").toLocaleTimeString("fa-IR")}`:"در انتظار بررسی جامع"}</Text>
    {summary.data?.inherited_restriction && <Alert status="error"><AlertIcon />محدودیت از حساب بالادستی اعمال شده است؛ برای رفع آن با ادمین بالادستی پیگیری کنید.</Alert>}
    {summary.isError && <Alert status="error"><AlertIcon />دریافت هشدارها ناموفق است؛ اطلاعات قبلی ممکن است قدیمی باشد.<Button size="xs" onClick={()=>summary.refetch()}>تلاش مجدد</Button></Alert>}
    {stale && summary.isSuccess && <Alert status="warning"><AlertIcon />بررسی جامع هشدارها تازه نیست؛ وضعیت اتصال و سرور را بررسی کنید.</Alert>}
    <Collapse in={open}><Box p={3} borderTopWidth="1px" borderColor="var(--panel-border)">
      <Text fontSize="sm" mb={3}>{userData.is_sudo || userData.role==="OWNER" ? "هشدار همه ادمین‌ها؛ به تفکیک حساب" : "هشدارهای خودتان و زیرمجموعه‌هایتان"} · هشدار فعال تا رفع مشکل باقی می‌ماند.</Text>
      <HStack flexWrap="wrap" mb={4}>
        <Select aria-label="وضعیت هشدار" maxW="180px" value={status} onChange={e=>{setStatus(e.target.value);setBefore(null);}}><option value="active">فعال</option><option value="resolved">رفع‌شده</option><option value="all">همه</option></Select>
        <Select aria-label="اهمیت هشدار" maxW="180px" value={severity} onChange={e=>{setSeverity(e.target.value);setBefore(null);}}><option value="">همه اهمیت‌ها</option><option value="critical">حیاتی</option><option value="warning">مهم</option></Select>
        <Input aria-label="جستجوی ادمین هشدار" placeholder="نام کاربری ادمین" maxW="220px" value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"){setUsername(draft.trim());setBefore(null);}}}/>
        <Button size="sm" onClick={()=>{setUsername(draft.trim());setBefore(null);}}>فیلتر</Button>
      </HStack>
      {query.isError && <Alert status="error"><AlertIcon />{localizedApiError(query.error)}</Alert>}
      {query.isLoading && <Text>در حال دریافت…</Text>}
      {query.isSuccess && query.data?.items.length===0 && <Text>هشداری با این فیلتر وجود ندارد.</Text>}
      <Stack spacing={4} maxH={{base:"55vh",md:"500px"}} overflowY="auto">
        {[...groups].map(([name,items])=><Box key={name}><Text fontWeight="850" mb={2} dir="ltr">{name}</Text><Stack spacing={2}>{items.map(item=><Box key={item.id} borderWidth="1px" borderRadius="10px" p={3} borderColor={item.severity==="critical" && !item.resolved_at ? "var(--panel-danger-border)":"var(--panel-border)"}>
          <HStack justify="space-between" flexWrap="wrap"><Text fontWeight="750">{labels[item.resource] || item.resource} · {states[item.state] || item.state}</Text><Badge colorScheme={item.resolved_at?"green":item.severity==="critical"?"red":"orange"}>{item.resolved_at?"رفع‌شده":item.severity==="critical"?"حیاتی":"مهم"}</Badge></HStack>
          <Box my={2}><Details item={item}/></Box>
          <HStack flexWrap="wrap"><Button size="xs" isDisabled={item.seen} isLoading={busy===item.id} onClick={()=>markSeen(item)}>{item.seen?"دیده شده؛ وضعیت همچنان ثبت است":"دیده شد"}</Button><Text fontSize="xs" color="var(--panel-text-muted)">{new Date(item.opened_at+"Z").toLocaleString("fa-IR")}</Text></HStack>
        </Box>)}</Stack></Box>)}
      </Stack>
      <HStack mt={3}><Button size="sm" onClick={()=>setBefore(null)} isDisabled={before===null}>جدیدترین</Button><Button size="sm" isDisabled={!query.data?.next_before} onClick={()=>setBefore(query.data?.next_before || null)}>موارد قدیمی‌تر</Button></HStack>
    </Box></Collapse>
  </Box>;
}
