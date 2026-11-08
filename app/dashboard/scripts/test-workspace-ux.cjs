const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { create, act } = require('react-test-renderer');
const { QueryClient, QueryClientProvider, setLogger } = require('react-query');
const root = path.resolve(__dirname, '../src');
const requests = [], toasts = [], cache = new Map();
let closes = 0, failure = false;
const plan = { id: 7, name: 'Plan', data_limit: 1024 ** 3, duration_days: 20, price_toman: 2333 };
const admin = { id: 2, username: 'child', role: 'ADMIN', trial_quota: 2, trial_quota_limit: 10, trials_used: 8 };
const actor = { username: 'owner', is_sudo: true, role: 'OWNER' };
const api = (url, options) => {
  if (options?.method) { requests.push({ url, options }); return failure ? Promise.reject(new Error('Synthetic failure')) : Promise.resolve({ ok: true }); }
  if (url === '/available-user-plans') return Promise.resolve([plan]);
  if (url === '/access-groups') return Promise.resolve([{ id: 4, name: 'Allowed network' }]);
  if (url === '/admin/capabilities') return Promise.resolve({ can_manage_admins: true });
  if (url.startsWith('/admin-management?')) return Promise.resolve({ admins: [admin] });
  throw Error('Unexpected query ' + url);
};
const text = node => typeof node === 'string' ? node : Array.isArray(node) ? node.map(text).join('') : (node?.children || []).map(text).join('');
const chakra = { useToast: () => toast => { toasts.push(toast); } };
for (const name of ['Alert','AlertIcon','Box','Button','FormControl','FormHelperText','FormLabel','HStack','Input','Modal','ModalBody','ModalCloseButton','ModalContent','ModalFooter','ModalHeader','ModalOverlay','Select','Stack','Text','Popover','PopoverBody','PopoverCloseButton','PopoverContent','PopoverHeader','PopoverTrigger']) {
 chakra[name] = React.forwardRef(({ children, ...props }, ref) => {
   if (name === 'Popover') return React.createElement('div', null, React.cloneElement(children[0], { onOpen:props.onOpen }), props.isOpen ? children[1] : null);
   if (name === 'PopoverTrigger') return React.cloneElement(children, { onClick:props.onOpen });
   if (name === 'Modal' && !props.isOpen) return null;
   const tag = name === 'Input' ? 'input' : name === 'Select' ? 'select' : name.includes('Button') || name === 'Button' ? 'button' : props.as === 'form' ? 'form' : 'div';
   return React.createElement(tag, { ...props, ref, disabled: props.isDisabled || props.isLoading }, children);
 });
}
let client;
const original = Module._load;
function load(file) {
 if (cache.has(file)) return cache.get(file).exports;
 const m = new Module(file, module); m.filename = file; m.paths = Module._nodeModulePaths(path.dirname(file)); cache.set(file,m);
 m._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{ compilerOptions:{ module:ts.ModuleKind.CommonJS, jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020 } }).outputText,file);
 return m.exports;
}
Module._load = function(name, parent, ...rest) {
 if (parent?.filename.startsWith(root)) {
   if (name === '@chakra-ui/react') return chakra;
   if (name === 'service/http') return { fetch:api };
   if (name === 'hooks/useGetUser') return { default:() => ({ userData:actor,getUserIsSuccess:true }) };
   if (name === 'contexts/DashboardContext') return { useDashboard:{ getState:() => ({ refetchUsers() {} }) } };
   if (name === 'utils/apiError') return { localizedApiError:error => error.message };
   if (name === 'utils/formatByte') return { formatBytes:value => `${value} B` };
   if (name === 'utils/react-query') return { get queryClient() { return client; } };
   if (name === './AdminFormDrawer') return { AdminFormDrawer:() => React.createElement('editing-admin') };
   if (name.startsWith('./')) { const file=path.resolve(path.dirname(parent.filename),name+'.tsx'); if(fs.existsSync(file)) return load(file); }
 }
 return original.call(this,name,parent,...rest);
};
const { CreateUserFromPlan } = load(path.join(root,'components/CreateUserFromPlan.tsx'));
const { AdminTrialQuota } = load(path.join(root,'components/AdminTrialQuota.tsx'));
const { AlertAccountActions } = load(path.join(root,'components/AlertAccountActions.tsx'));
Module._load = original;
global.window = { confirm:() => true };
setLogger({ log(){},warn(){},error(){} });
const flush=()=>new Promise(resolve=>setTimeout(resolve,20));
async function mount(Component,props) {
 client=new QueryClient({defaultOptions:{queries:{retry:false,cacheTime:Infinity},mutations:{retry:false}}});
 let r; await act(async()=>{r=create(React.createElement(QueryClientProvider,{client},React.createElement(Component,props)));await flush();});
 return r;
}
async function click(r,label){const b=r.root.findAllByType('button').find(n=>text(n)===label);assert(b,'Missing '+label);assert(!b.props.disabled,'Disabled '+label);await act(async()=>{b.props.onClick();await flush();});}
(async()=>{
 let r=await mount(CreateUserFromPlan,{isOpen:true,onClose:()=>closes++});
 let input=r.root.findByType('input');assert.match(input.props.value,/^u_[a-f0-9]{12}$/);
 assert.deepEqual(r.root.findAllByType('select').map(n=>n.props.value),['7','4'],'only available options should preselect');
 failure=true;
 await act(async()=>{r.root.findByType('form').props.onSubmit({preventDefault(){}});await flush();});
 assert.equal(closes,0,'failure must retain the creation form');
 const first=requests.at(-1);assert.equal(first.url,'/users/from-plan');assert.equal(first.options.body.access_group_id,4);
 failure=false;
 await act(async()=>{r.root.findByType('form').props.onSubmit({preventDefault(){}});await flush();});
 assert.equal(requests.at(-1).options.body.idempotency_key,first.options.body.idempotency_key,'retry must keep its operation key');assert.equal(closes,1);
 await act(async()=>r.unmount());client.clear();
 r=await mount(AdminTrialQuota,{admin});
 await click(r,'تست: ۲');
 await act(async()=>r.root.findByType('input').props.onChange({target:{value:'3'}}));
 assert(r.root.findAllByType('button').find(n=>text(n)==='کاهش').props.disabled,'cannot reclaim more than remaining quota');
 await click(r,'افزایش');assert.equal(requests.at(-1).url,'/admin-management/child/trial-quota/grant');assert.equal(requests.at(-1).options.body.amount,3);
 await act(async()=>r.unmount());client.clear();
 r=await mount(AlertAccountActions,{item:{admin_username:'child',resource:'financial'}});
 await act(async()=>r.root.findByType('input').props.onChange({target:{value:'2333'}}));
 await click(r,'افزایش');assert.equal(requests.at(-1).options.body.amount_toman,2333);
 await click(r,'ویرایش محدودیت‌ها');assert.equal(r.root.findAllByType('editing-admin').length,1,'edit must open in the same alert');
 await act(async()=>r.unmount());client.clear();
 console.log('Workspace UX: generated username, explicit network, failed creation/retry, idempotency, trial grant/reclaim limits, 2333-Toman alert credit and inline edit passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
