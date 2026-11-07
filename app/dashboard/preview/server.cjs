/** Isolated UI review server. It has no production API, database or proxy access. */
const fs = require('node:fs');
const path = require('node:path');
const https = require('node:https');
const http = require('node:http');
const root = path.resolve(process.env.UI_BUILD_DIR || path.join(__dirname, '../build'));
const now = () => new Date().toISOString().replace(/Z$/, '');
const gib = 1024 ** 3;
const sessions = new Map();
const roles = ['owner', 'manager', 'form', 'plan', 'suspended'];
const modes = ['demo', 'worst', 'empty', 'one', 'huge', 'loading', 'error', 'escalated'];
const branding = { panel_name: 'Marzban · نسخه آزمایشی', login_title: 'به فضای کاری خود وارد شوید', description: 'محیط آزمایشی طراحی با اطلاعات ساختگی', logo_url: null, favicon_url: null };
function fixtures(session) {
  const { role, mode } = session;
  const owner = role === 'owner', manager = owner || role === 'manager', planOnly = role === 'plan';
  const count = mode === 'empty' ? 0 : mode === 'one' ? 1 : mode === 'huge' ? 1000000 : 48;
  const username = owner ? 'preview_owner' : 'preview_admin';
  const quota = { current_users: count, lifetime_consumed_traffic: 7.4 * 1024 * gib, lifetime_created_traffic: 12 * 1024 * gib, max_users: 5000, remaining_user_slots: 5000-count, credit_limit: 8000*gib, credit_used: 4000*gib, credit_remaining: 4000*gib, credit_usage_percent: 50, credit_calculation_mode: 'used_traffic', operation_allowance_remaining: 50, admin_warning_percent: 80, sudo_warning_percent: 90, admin_warning_active: false, sudo_warning_active: false };
  const policy = { billing_mode: planOnly ? 'USER_CREDIT' : 'USED_TRAFFIC', money_billing_enabled: true, money_balance_toman: mode === 'worst' ? -125000000 : 24500000, last_positive_charge_toman: 50000000, financial_limits_enabled: true, financial_freeze_percent: 10, financial_disable_percent: 20, used_traffic_price_per_gib_toman: 850, total_traffic: 8000*gib, expiry_date: '2027-02-01', user_limit: 5000, max_users: 5000, device_capacity_limit: null, admin_traffic_warning_percent: 80, sudo_traffic_warning_percent: 90, all_inbounds: true, allowed_inbounds: ['VLESS-TLS'], all_user_limits: true, allowed_user_limits: [1,2,3,5], allowed_subscription_modes: ['limited_traffic_limited_devices','limited_traffic_unlimited_devices'], view_full_client_ip: true, max_user_duration_days: 365, calculate_volume: 'used_traffic', prevent_user_creation: false, prevent_user_deletion: false, prevent_user_reset: false, prevent_revoke_subscription: false, prevent_unlimited_traffic: false };
  const account = { ...policy, username, user_namespace_prefix: 'preview', role: owner ? 'OWNER' : 'ADMIN', account_status: role === 'suspended' ? 'SUSPENDED' : 'ACTIVE', suspended_reason: role === 'suspended' ? 'محدودیت آزمایشی حساب' : null, suspended_at: null, own_users: count, subtree_users: count, delegated_traffic: 500*gib, own_spend: 250*gib, available_traffic: 7500*gib, renewal_enabled: true, renewal_remaining: 100, user_creation_mode: planOnly ? 'PLAN_ONLY' : 'FREE_FORM', can_manage_plans: manager, trial_quota: 20, trials_used: 3, can_create_admins: manager, can_delegate_admin_creation: owner, can_create_allocated_children: owner, admin_creation_limit: 20, admin_creations_used: 4, delegated_admin_creation_limit: 5, admin_creation_remaining: 11 };
  const capabilities = { hierarchy_enabled: true, all_inbounds: true, allowed_inbounds: ['VLESS-TLS'], all_user_limits: true, allowed_user_limits: [1,2,3,5], allowed_subscription_modes: policy.allowed_subscription_modes, allowed_form_duration_days: [15,20,30,60,90,180,365], view_full_client_ip: true, capacity_used: count, capacity_limit: 5000, capacity_remaining: 5000-count, quota, can_manage_admins: manager, can_create_admins: manager, can_delegate_admin_creation: owner, can_create_allocated_children: owner, admin_creation_limit: 20, admin_creations_used: 4, delegated_admin_creation_limit: 5, admin_creation_remaining: 11, allowed_child_roles: ['ADMIN'], allowed_child_billing_modes: ['USED_TRAFFIC','ALLOCATED_TRAFFIC','USER_CREDIT'], allowed_child_user_creation_modes: ['FREE_FORM','PLAN_ONLY'], can_delegate_plan_management: owner };
  const admins = Array.from({length: count ? Math.min(count,6) : 0},(_,i) => ({...account,id:i+2,username: ['reza_preview','sales_tehran','support_team','agency_north','mohammad_preview','sub_admin'][i], role:'ADMIN',is_sudo:false,parent_admin_id:1,parent_username:username,external_api_enabled:false,telegram_id:null,phone:null,discord_webhook:null,users_usage:500*gib,user_count:23+i*7,capacity_used:30+i*5,policy:{...policy,billing_mode:['USED_TRAFFIC','ALLOCATED_TRAFFIC','USER_CREDIT'][i%3]},quota,plan_category_ids:[1],plan_prices:[],dashboard_theme:'heisenberg',logo_url:null,account_status:['ACTIVE','ACTIVE','SUSPENDED','DISABLED','ACTIVE','ACTIVE'][i],active_owner_freeze_event_id:i===2?9:null,trial_quota_limit:20}));
  const users = Array.from({length: Math.min(count,50)},(_,i)=>({id:i+1,username:mode==='worst' && i===0?'preview_'+ 'very_long_technical_username_'.repeat(3):['sajad_preview','mohammad_preview','agency_user','tehran_demo','customer_005','north_demo'][i%6]+(i>5?'_'+i:''),status:['active','active','expired','on_hold','limited','disabled'][i%6],proxies:{vless:{id:'00000000-0000-4000-8000-000000000001'}},inbounds:{vless:['VLESS-TLS']},expire:Math.floor(Date.now()/1000)+(i%6===2?-86400:86400*(i%29+1)),data_limit:i%7===6?null:50*gib,used_traffic:(i%50+1)*gib,lifetime_used_traffic:150*gib,data_limit_reset_strategy:'no_reset',on_hold_expire_duration:30*86400,links:['vless://00000000-0000-4000-8000-000000000001@example.invalid:443?security=tls#Preview'],subscription_url:'https://example.invalid/sub/preview',note:mode==='worst'?'توضیحات طولانی فارسی برای بررسی خوانایی و شکست متن در رابط کاربری. '.repeat(8):'حساب آزمایشی؛ اطلاعات ساختگی',online_at:i%3?now():null,created_at:now(),sub_updated_at:now(),sub_last_user_agent:'Hiddify/3.0 (Android)',admin:{username:admins[0]?.username||username},next_plan:null,reset_history:[],concurrent_user_limit:2}));
  users.unshift(...session.users);
  const categories = count ? [{id:1,owner_admin_id:1,name:mode==='worst'?'اشتراک ویژهٔ نمایندگان با عنوان طولانی برای بررسی نمایش در صفحات کوچک':'اشتراک استاندارد',description:'طرح‌های ماهانه',archived_at:null,plan_count:3}] : [];
  const plans = count ? Array.from({length:mode==='huge'?60:3},(_,i)=>({id:i+1,owner_admin_id:1,name:['نقره‌ای · ۳۰ روزه','طلایی · ۶۰ روزه','آزمایشی'][i%3]+(i>2?' · '+(i+1):''),description:mode==='worst'?'توضیحات پلن و شرایط استفاده با متن طولانی و اعداد 192.0.2.1 برای بررسی چیدمان. '.repeat(5):'ترافیک، زمان و دسترسی مشخص برای هر اشتراک',category_id:1,category_name:categories[0].name,current_version_id:i+1,version_number:1,archived_at:null,version:{price_toman:49000*(i+1),data_limit:50*(i+1)*gib,duration_days:30*(i+1),concurrent_user_limit:2,reset_strategy:'no_reset',renewal_volume_strategy:'replace',renewal_time_strategy:'extend_max'},allowed_admin_ids:[],include_subtree:true,is_trial:i%3===2,effective_price_toman:49000*(i+1),base_price_toman:49000*(i+1),price_toman:49000*(i+1),duration_days:30*(i+1),data_limit:50*(i+1)*gib,concurrent_user_limit:2})) : [];
  const groups = count ? [{id:1,owner_admin_id:1,name:'شبکهٔ اصلی اروپا',description:mode==='worst'?'توضیحات گروه دسترسی شامل اینباندهای منتخب و مسیرهای مجاز. '.repeat(8):'مسیرهای منتخب اشتراک استاندارد',node_ids:[],inbounds:['VLESS-TLS'],hosts:{'VLESS-TLS':[1]},allowed_admin_ids:[],admin_access_restricted:false,archived_at:null,active_user_count:count}] : [];
  if (groups.length) {
   groups[0].admin_access_restricted = false;
   groups.push({...groups[0],id:2,name:'شبکهٔ خصوصی مالک',allowed_admin_ids:[],admin_access_restricted:true,active_user_count:0});
   groups.push({...groups[0],id:3,name:'شبکهٔ نمایندگان',allowed_admin_ids:[2,3],admin_access_restricted:true,active_user_count:4});
  }
  const logs = users.slice(0,6).map((u,i)=>({id:i+1,admin_id:1,admin_username:username,action:['user.create','admin.update','credit.grant'][i%3],target_type:'user',target_id:String(i+1),target_name:u.username,description:'فعالیت آزمایشی',ip_address:'2001:db8:85a3::8a2e:370:7334',created_at:now(),previous_value:{status:'disabled'},new_value:{status:'active'},details:{request_id:'6f986b18-14e6-4dda-a7ba-88b8d2eef475',note:u.note}}));
  const device = { enabled:true,enforcement_mode:'hybrid',device_slots_enabled:true,ip_detection_enabled:true,client_fingerprint_enabled:true,check_interval_seconds:60,active_window_seconds:120,hit_threshold:3,min_successful_connections:2,handoff_grace_seconds:90,warning_auto_delete_seconds:86400,strike_reset_seconds:86400,full_ip_retention_days:7,incident_retention_days:30,audit_retention_days:90,auto_delete_enabled:false,updated_at:now() };
  const alertNames = owner ? ['reza_preview','sales_tehran','support_team'] : role === 'manager' ? [username,'sub_admin'] : [username];
  const incidents = Array.from({length:mode==='empty'?0:mode==='one'?1:mode==='huge'?65:6},(_,i)=>({
    id:1000-i,admin_id:i%alertNames.length+2,admin_username:mode==='worst' && i===0 ? 'admin_'+'long_name_'.repeat(18) : alertNames[i%alertNames.length],
    resource:['financial','expiry','traffic'][i%3],state:i%3===0?(mode==='escalated'?'disabled':'frozen'):i%3===1?'near_limit':'exhausted',
    severity:i%3===1?'warning':'critical',revision:mode==='escalated'?3:2,seen:session.alertReceipts?.[1000-i]===(mode==='escalated'?3:2),
    opened_at:'2026-11-07T07:00:00',resolved_at:i===5?'2026-11-07T07:30:00':null,
    details:i%3===0?{balance_toman:-125000,basis_toman:1000000,debt_percent:12.5,freeze_percent:10,cutoff_percent:40,remaining_to_freeze_toman:0,remaining_to_cutoff_toman:275000}:i%3===1?{remaining_days:3,expiry_date:'2026-11-10'}:{used:1024*gib,limit:1024*gib,remaining:0,percent:100,unit:'bytes'}
  }));
  return { owner,manager,username,count,quota,policy,account,capabilities,admins,users,categories,plans,groups,logs,device,incidents };

}
async function body(req) { let value='';for await(const chunk of req){value+=chunk;if(value.length>1000000)throw Error('request too large');}try{return JSON.parse(value)}catch{return Object.fromEntries(new URLSearchParams(value))} }
function json(res,value,status=200){res.writeHead(status,{'content-type':'application/json','cache-control':'no-store'});res.end(JSON.stringify(value));}
function toolbar(session) {
 const options = (values,selected)=>values.map(v=>`<option${v===selected?' selected':''}>${v}</option>`).join('');
 return `<aside dir="ltr" id="preview-tools" style="position:fixed;bottom:8px;left:8px;z-index:1200;max-width:calc(100vw - 16px);font:12px system-ui;color:#fff;background:#183b30;border:1px solid #6cb49a;border-radius:10px;box-shadow:0 4px 24px #0003"><details><summary style="padding:10px;cursor:pointer">UI PREVIEW · synthetic data · ${session.role} / ${session.mode}</summary><form action="/__preview/state" method="post" style="padding:12px;display:flex;gap:8px;flex-wrap:wrap"><label>Role <select name="role" aria-label="Preview role">${options(roles,session.role)}</select></label><label>Data <select name="mode" aria-label="Preview data">${options(modes,session.mode)}</select></label><button type="submit">Apply & reload</button><button type="submit" name="reset" value="1">Reset data</button></form></details></aside>`;
}
async function handler(req,res) {
 try {
  const url = new URL(req.url,'http://preview');
  let sid = /(?:^|; )ui-preview=([a-z0-9-]+)/.exec(req.headers.cookie||'')?.[1];
  if(!sid||!sessions.has(sid)){sid=require('node:crypto').randomUUID();sessions.set(sid,{role:'owner',mode:'demo',users:[],requests:[]});res.setHeader('set-cookie',`ui-preview=${sid}; HttpOnly; SameSite=Strict; Path=/`);}
  const session=sessions.get(sid),f=fixtures(session),p=url.pathname.replace(/^\/api/,'');
  if(url.pathname==='/__preview/state'&&req.method==='POST'){const data=await body(req);session.role=roles.includes(data.role)?data.role:'owner';session.mode=modes.includes(data.mode)?data.mode:'demo';if(data.reset)session.users=[];res.writeHead(303,{location:'/dashboard/'});return res.end();}
  if(url.pathname==='/__preview/requests')return json(res,session.requests);
  if(url.pathname==='/__preview/canvas') {
   const width = [320,375,768,1024,1440].includes(+url.searchParams.get('width')) ? +url.searchParams.get('width') : 375;
   const route = ['/','/users/','/admins/','/plans/','/device-limits/','/audit-logs/','/settings/','/login/'].includes(url.searchParams.get('route')) ? url.searchParams.get('route') : '/';
   res.setHeader('content-type','text/html; charset=utf-8');res.setHeader('x-robots-tag','noindex');
   return res.end(`<!doctype html><html><head><title>Marzban responsive review</title><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:0;background:#344039;font:14px system-ui;color:white"><form style="padding:12px;display:flex;gap:12px;flex-wrap:wrap"><label>Viewport <select name="width" aria-label="Review width">${[320,375,768,1024,1440].map(w=>`<option value="${w}"${w===width?' selected':''}>${w}</option>`).join('')}</select></label><label>Page <select name="route" aria-label="Review page">${['/','/users/','/admins/','/plans/','/device-limits/','/audit-logs/','/settings/','/login/'].map(r=>`<option value="${r}"${r===route?' selected':''}>${r}</option>`).join('')}</select></label><button>Review layout</button><span>Synthetic UI review · ${width}px</span></form><div style="padding:12px;overflow:auto"><iframe title="Responsive console" src="/dashboard/#${route}" style="display:block;margin:auto;width:${width}px;height:900px;border:1px solid #718a7c;border-radius:12px;background:white"></iframe></div></body></html>`);
  }
  if(url.pathname==='/__preview/health')return json(res,{ok:true,synthetic:true});
  if(url.pathname.startsWith('/api/')) {
   session.requests.push({path:p,method:req.method,time:now()});if(session.requests.length>1000)session.requests.shift();
   if(p==='/branding/public')return json(res,branding);
   if(p==='/admin/token')return json(res,{access_token:'synthetic-preview-token',token_type:'bearer'});
   if(p==='/admin')return json(res,{...f.account,id:1,is_sudo:f.owner,telegram_id:null,discord_webook:null,logo_url:null});
   if(p==='/admin/logout')return json(res,{ok:true});
   if(p==='/admin-management/alert-events'){res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache'});res.write(': UI fixture stream\n\n');const timer=setInterval(()=>res.write(': keep-alive\n\n'),20000);res.on('close',()=>clearInterval(timer));return;}
   if(session.mode==='loading')await new Promise(r=>setTimeout(r,4500));
   if(session.mode==='error' && ['/dashboard/overview','/users/management','/admin-management','/audit-logs','/user-plans','/device-limit/settings','/admin-management/alert-center'].includes(p))return json(res,{detail:'UI preview: simulated service failure'},503);
   if(req.method!=='GET') {
    const data=await body(req);
    session.requests[session.requests.length-1].body=data;
    const receipt=/^\/admin-management\/alert-center\/(\d+)\/seen$/.exec(p);
    if(receipt){
     if(session.mode==='worst')return json(res,{detail:'ثبت مشاهده انجام نشد؛ نمونهٔ خطای آزمایشی'},503);
     session.alertReceipts ||= {};session.alertReceipts[+receipt[1]]=+url.searchParams.get('revision');return json(res,{ok:true});
    }
    if(p==='/admin-management'&&req.method==='POST'){
     if(session.mode==='worst')return json(res,{detail:'نام کاربری از قبل وجود دارد؛ نمونهٔ خطای آزمایشی'},409);
     return json(res,{...f.admins[0],...data,id:99,username:data.username,account_status:'ACTIVE'});
    }
    if(p==='/user'||p==='/users/from-plan'){const user={...f.users[0],...data,id:1000+session.users.length};session.users.unshift(user);return json(res,user);}
    if(p==='/hosts/impact')return json(res,{affected_access_group_count:1,active_user_count:f.count,affected_access_group_ids:[1],invalid_access_group_ids:[],changed_host_ids:[1],removed_host_ids:[]});
    if(p.startsWith('/owner/backups'))return json(res,{message:'Preview only',filename:'synthetic-backup.tar.gz'});
    return json(res,data && Object.keys(data).length ? data : {ok:true});
   }
   if(p==='/admin/capabilities')return json(res,f.capabilities);
   if(p==='/account/summary')return json(res,f.account);
   if(p==='/dashboard/overview')return json(res,{generated_at:now(),timezone_offset_minutes:210,current_week_start:now(),previous_week_start:now(),role:f.owner?'OWNER':'ADMIN',online_window_seconds:60,traffic_range:url.searchParams.get('traffic_range')||'24h',total_users:f.count,active_users:Math.round(f.count*.72),online_users:Math.round(f.count*.35),disabled_users:Math.round(f.count*.06),expired_users:Math.round(f.count*.12),limited_users:Math.round(f.count*.06),on_hold_users:Math.round(f.count*.04),current_used_traffic:3648*gib,allocated_quota:8000*gib,today_traffic:246*gib,traffic_history_available:!!f.count,traffic_history:f.count?Array.from({length:24},(_,i)=>({timestamp:new Date(Date.now()-(23-i)*3600000).toISOString(),total_traffic:(12+Math.sin(i*.5)*8+i*.7)*gib})):[],attention_count:f.count?4:0,attention_users:f.users.slice(0,4).map((u,i)=>({...u,priority:i?'high':'critical',reason_code:i?'expires_soon':'traffic_near_limit',usage_percent:96})),top_consumers:f.users.slice(0,5),recent_users:f.users.slice(0,5),node_summary:f.owner?{total:3,healthy:2,reconnecting:1,error:0,disabled:0}:null,admin_summary:f.owner?{total:6,active:4,suspended:1,disabled:1}:null,new_users:{current:12,previous:8,change_percent:50},billing_modes:[]});
   if(p==='/users/summary')return json(res,{total_users:f.count,online_users:Math.round(f.count*.35),expiring_users:f.count?7:0,high_usage_users:f.count?4:0,online_window_hours:24,expiring_within_days:3,high_usage_threshold_percent:80});
   if(p==='/users/management'||p==='/users'){const search=url.searchParams.get('search')||url.searchParams.get('username')||'',offset=+(url.searchParams.get('offset')||0),limit=+(url.searchParams.get('limit')||10);const all=f.users.filter(u=>u.username.includes(search)&&(!url.searchParams.get('status')||u.status===url.searchParams.get('status')));const total=search?all.length:f.count;return json(res,{users:all.slice(offset,offset+limit),total,page:Math.floor(offset/limit)+1,page_size:limit,pages:Math.max(1,Math.ceil(total/limit)),plan_meta:Object.fromEntries(all.map(u=>[u.username,{plan_id:1,plan_name:'نقره‌ای · ۳۰ روزه',version_id:1,version_number:1,is_trial:false,operation_type:'create',assigned_at:now()}]))});}
   if(p==='/admin-management')return json(res,{admins:f.admins,total:f.admins.length,offset:0,limit:20});
   if(p==='/admins')return json(res,[{username:f.username,is_sudo:f.owner},...f.admins]);
   if((p==='/admin-management/requests-alerts'||p==='/admin-management/refund-requests'))return json(res,{requests:[],alerts:[],actor_id:1});
   if(p==='/admin-management/alert-center'){
    const active=f.incidents.filter(i=>!i.resolved_at),status=url.searchParams.get('status')||'active',severity=url.searchParams.get('severity'),username=url.searchParams.get('username'),before=+url.searchParams.get('before');
    const items=f.incidents.filter(i=>(status==='all'||(status==='resolved'?!!i.resolved_at:!i.resolved_at))&&(!severity||i.severity===severity)&&(!username||i.admin_username.includes(username))&&(!before||i.id<before));
    const page=items.slice(0,50);return json(res,{items:page,counts:{critical:active.filter(i=>i.severity==='critical').length,warning:active.filter(i=>i.severity==='warning').length},checked_at:now(),next_before:items.length>50?page[page.length-1].id:null,inherited_restriction:session.role==='suspended'});
   }
   if(p==='/admin-management/tree')return json(res,[]);
   if(p==='/plan-categories')return json(res,f.categories);
   if(p==='/user-plans'||p==='/available-user-plans')return json(res,f.plans);
   if(p==='/access-groups')return json(res,f.groups);
   if(p==='/access-group-network-options')return json(res,[{tag:'VLESS-TLS',protocol:'vless',network:'tcp',tls:'tls',port:443,hosts:[{id:1,remark:'Europe · primary'}]}]);
   if(p==='/audit-logs/options')return json(res,{admins:[f.username,...f.admins.map(a=>a.username)],actions:['user.create','admin.update','credit.grant'],target_types:['user','admin']});
   if(p==='/audit-logs')return json(res,{logs:f.logs,total:f.logs.length,offset:0,limit:25});
   if(p==='/device-limit/settings')return json(res,f.device);
   if(p==='/device-limit/penalty-stages')return json(res,[{id:1,violation_count:1,action:'warn',duration_seconds:null,enabled:true},{id:2,violation_count:3,action:'temporary_disable',duration_seconds:300,enabled:true}]);
   if(p==='/device-limit/incidents')return json(res,{incidents:[],total:0,offset:0,limit:20});
   if(p.startsWith('/device-limit/users/'))return json(res,{username:p.split('/').pop(),configured_limit:2,enabled:true,live_active_ip_count:1,live_ip_addresses:['192.0.2.24'],live_source_nodes:['Europe'],state:{violation_count:0,current_stage:0,penalty_status:'clear',blocked_until:null,last_violation_at:null,last_seen_at:now(),active_ip_count:1,last_reason:null,pending_handoff_started_at:null,pending_ip_addresses:[],pending_source_nodes:[],pending_risk_score:null},slots:[],user_client_observations:[]});
   if(p==='/owner/pricing')return json(res,{price_per_gib_toman:850,duration_pricing_mode:'CAPPED_DAILY',duration_base_days:30,duration_cap_days:365,duration_max_multiplier:2,duration_examples:[15,30,60,90,180,365].map(d=>({duration_days:d,multiplier:1+(d-30)*.002}))});
   if(p==='/owner/backups/settings')return json(res,{enabled:true,destination:'LOCAL',schedule:'24h',retention_count:7,smtp_use_tls:true,telegram_configured:false,smtp_configured:false});
   if(p==='/inbounds')return json(res,{vless:[{tag:'VLESS-TLS',protocol:'vless',network:'tcp',tls:'tls',port:443}],vmess:[],trojan:[],shadowsocks:[]});
   if(p==='/hosts')return json(res,{'VLESS-TLS':[{id:1,remark:'Europe · primary',address:'edge.example.invalid',port:443,path:null,sni:'edge.example.invalid',host:null}]});
   if(p==='/nodes')return json(res,[]);
   if(p==='/nodes/bandwidth'||p==='/nodes/operations')return json(res,{nodes:[],generated_at:now(),total_incoming_bps:0,total_outgoing_bps:0});
   if(p==='/node/settings')return json(res,{local_node_enabled:true,local_xray_enabled:true,ip_source_mode:'direct',trusted_proxy_cidrs:[]});
   if(p==='/node/watchdog/settings')return json(res,{enabled:true,telegram_bot_token_configured:false,telegram_chat_id:null,check_interval:60,backoff_cap:300,remind_every:3600});
   if(p==='/core')return json(res,{version:'26.3.27',started:true,local_enabled:true,logs_websocket:null});
   if(p==='/core/config')return json(res,{log:{loglevel:'warning'},inbounds:[],outbounds:[{protocol:'freedom'}]});
   if(p==='/system')return json(res,{version:'1.1.21',mem_total:4*gib,mem_used:1.2*gib,cpu_usage:24,total_user:48,users_active:32,incoming_bandwidth_speed:21e6,outgoing_bandwidth_speed:24e6,incoming_bandwidth:500*gib,outgoing_bandwidth:1000*gib});
   if(p.startsWith('/user/'))return json(res,f.users.find(u=>u.username===decodeURIComponent(p.split('/')[2]))||f.users[0]);
   if(p.endsWith('/usage'))return json(res,{usages:[],total:0});
   console.error('UNHANDLED_FIXTURE',req.method,p);return json(res,{detail:'No UI fixture for '+p},501);
  }
  const relative = url.pathname.startsWith('/statics/') ? url.pathname.slice(1) : 'index.html';
  const file=path.resolve(root,relative);if(!file.startsWith(root+path.sep))return json(res,{detail:'Invalid path'},400);
  if(!fs.existsSync(file))return json(res,{detail:'Static asset missing'},404);
  const ext=path.extname(file);const type={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2'}[ext]||'application/octet-stream';
  res.setHeader('content-type',type);res.setHeader('cache-control','no-store');res.setHeader('x-robots-tag','noindex, nofollow');
  if(ext==='.html')return res.end(fs.readFileSync(file,'utf8').replace('</body>',toolbar(session)+'</body>'));
  if(/\.(js|css|json|svg)$/.test(file) && /gzip/.test(req.headers['accept-encoding']||'')){res.setHeader('content-encoding','gzip');return res.end(require('node:zlib').gzipSync(fs.readFileSync(file)));}
  fs.createReadStream(file).pipe(res);
 }catch(error){console.error(error.stack);if(!res.headersSent)json(res,{detail:'Preview fixture failure'},500);else res.end();}
}
const server = process.env.UI_TLS_CERT && process.env.UI_TLS_KEY ? https.createServer({cert:fs.readFileSync(process.env.UI_TLS_CERT),key:fs.readFileSync(process.env.UI_TLS_KEY)},handler) : http.createServer(handler);
server.listen(+(process.env.PORT||3000),process.env.UI_LISTEN||'127.0.0.1',()=>console.log('Isolated frontend preview ready'));
