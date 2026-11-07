const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { create, act } = require('react-test-renderer');
const { QueryClient, QueryClientProvider, setLogger } = require('react-query');
const root = path.resolve(__dirname, '../src');
const requests = [];
const GIB = 1024 ** 3;
const plan = { id: 8, name: 'Silver', description: 'Example', category_id: 1, category_name: 'Standard', version_number: 1, is_trial: false, effective_price_toman: 49000, allowed_admin_ids: [], include_subtree: false, version: { data_limit: 50 * GIB, price_toman: 49000, duration_days: 30, concurrent_user_limit: 2, reset_strategy: 'no_reset' } };
const group = { id: 1, name: 'Owner network', description: '', node_ids: [], inbounds: ['alpha'], hosts: { alpha: [1] }, admin_access_restricted: true, allowed_admin_ids: [], active_user_count: 2 };
const fixtures = {
  '/account/summary': { role: 'OWNER', account_status: 'ACTIVE', can_manage_plans: true },
  '/user-plans': [plan], '/plan-categories': [{ id: 1, name: 'Standard', description: null, plan_count: 1 }],
  '/access-groups': [group, { ...group, id: 2, name: 'Legacy network', admin_access_restricted: false, active_user_count: 0 }],
  '/access-group-network-options': [{ tag: 'alpha', protocol: 'vless', network: 'tcp', hosts: [{ id: 1, remark: 'First' }] }, { tag: 'beta', protocol: 'vless', network: 'ws', hosts: [{ id: 7, remark: 'Second' }] }],
  '/nodes': [], '/admin-management?offset=0&limit=100': { admins: [{ id: 3, username: 'reseller_one', role: 'ADMIN', account_status: 'ACTIVE' }, { id: 4, username: 'reseller_two', role: 'ADMIN', account_status: 'ACTIVE' }], total: 2 },
};
const fetch = (url, options) => options?.method
  ? new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }))
  : Promise.resolve(fixtures[url] ?? (() => { throw Error(`Unexpected GET ${url}`); })());
const layoutNames = ['Alert', 'AlertIcon', 'Badge', 'Box', 'Button', 'Card', 'Checkbox', 'Flex', 'FormControl', 'FormHelperText', 'FormLabel', 'HStack', 'Icon', 'Input', 'Modal', 'ModalBody', 'ModalCloseButton', 'ModalContent', 'ModalFooter', 'ModalHeader', 'ModalOverlay', 'Select', 'SimpleGrid', 'Skeleton', 'Stack', 'Text', 'Textarea', 'Menu', 'MenuButton', 'MenuList', 'MenuItem', 'Table', 'Tbody', 'Td', 'Th', 'Thead', 'Tr', 'Tabs', 'TabList', 'Tab', 'TabPanels', 'TabPanel', 'AlertDialog', 'AlertDialogOverlay', 'AlertDialogContent', 'AlertDialogHeader', 'AlertDialogBody', 'AlertDialogFooter'];
layoutNames.push('Portal');
const native = { Input: 'input', Textarea: 'textarea', Select: 'select', Button: 'button', MenuButton: 'button', MenuItem: 'button', Checkbox: 'mock-checkbox', FormControl: 'mock-field', FormLabel: 'label', ModalFooter: 'footer' };
const mockChakra = {
  useToast: () => () => {},
  useDisclosure: () => { const [isOpen, setOpen] = React.useState(false); return { isOpen, onOpen: React.useCallback(() => setOpen(true), []), onClose: React.useCallback(() => setOpen(false), []) }; },
};
for (const name of layoutNames) mockChakra[name] = React.forwardRef(({ children, ...props }, ref) => {
  if ((name === 'Modal' || name === 'AlertDialog') && !props.isOpen) return null;
  const tag = typeof props.as === 'string' ? props.as : native[name] || 'div';
  return React.createElement(tag, { ...props, ref, disabled: props.isDisabled || props.isLoading || props.disabled }, children);
});
const cache = new Map();
const originalLoad = Module._load;
function loadSource(file) {
  if (cache.has(file)) return cache.get(file).exports;
  const m = new Module(file, module); m.filename = file; m.paths = Module._nodeModulePaths(path.dirname(file)); cache.set(file, m);
  m._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2020 } }).outputText, file);
  return m.exports;
}
Module._load = function (name, parent, ...rest) {
  if (parent?.filename.startsWith(root)) {
    if (name === '@chakra-ui/react') return mockChakra;
    if (name === 'service/http') return { fetch };
    if (name === 'hooks/useGetUser') return { default: () => ({ getUserIsPending: false }) };
    if (name === 'components/AppShell') return { AppShell: ({ children }) => children };
    if (name === 'design-system/Console') return Object.fromEntries(['PageHeader', 'Surface', 'SectionHeader', 'EmptyState'].map(n => [n, ({ children, title, description, text, actions }) => React.createElement('div', {}, title || text, description, actions, children)]));
    if (name === 'components/AccessGroupManager') return { AccessGroupManager: () => React.createElement('group-workspace') };
    if (name === 'react-router-dom') return { useSearchParams: () => React.useState(new URLSearchParams()) };
    if (name === 'utils/apiError') return { localizedApiError: error => error?.message || 'Failure' };
    if (name === 'utils/formatByte') return { formatBytes: value => `${value / GIB} GB` };
    if (name.startsWith('components/plans/') || name === 'utils/accessGroupScope') return loadSource(path.join(root, name + (name.endsWith('CatalogPager') ? '.tsx' : '.ts')));
  }
  return originalLoad.call(this, name, parent, ...rest);
};
const { Plans } = loadSource(path.join(root, 'pages/Plans.tsx'));
const { AccessGroupManager } = loadSource(path.join(root, 'components/AccessGroupManager.tsx'));
const helpers = loadSource(path.join(root, 'components/plans/presentation.ts'));
Module._load = originalLoad;
setLogger({ log() {}, warn() {}, error() {} });
const text = node => typeof node === 'string' ? node : Array.isArray(node) ? node.map(text).join('') : (node?.children || []).map(text).join('');
const flush = () => new Promise(resolve => setTimeout(resolve, 15));
const click = (renderer, label) => {
  const node = renderer.root.findAllByType('button').find(n => text(n) === label);
  assert.ok(node, `Missing button ${label}`); assert.ok(!node.props.disabled, `Disabled button ${label}`); node.props.onClick();
};
const checkbox = (renderer, label) => renderer.root.findAllByType('mock-checkbox').find(n => text(n).includes(label));
async function mount(Component, account) {
  if (account) fixtures['/account/summary'] = account;
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, cacheTime: Infinity, staleTime: Infinity }, mutations: { retry: false } } });
  let renderer; await act(async () => { renderer = create(React.createElement(QueryClientProvider, { client }, React.createElement(Component))); await flush(); });
  return { renderer, client };
}
(async () => {
  assert.equal(helpers.accessGroupPermissionLabel(group), 'فقط مالک');
  assert.equal(helpers.accessGroupPermissionLabel({ ...group, admin_access_restricted: false }), 'همهٔ ادمین‌ها');
  assert.equal(helpers.accessGroupPermissionLabel({ ...group, allowed_admin_ids: [3] }), '۱ ادمین مجاز');
  assert.equal(helpers.filterPlans([{ ...plan, name: 'پلن ترکیبی' }], 'تركيبي', '').length, 1);
  assert.equal(helpers.filterPlans([plan], '', '2').length, 0);
  assert.deepEqual(helpers.catalogPage(Array.from({ length: 25 }, (_, i) => i), 100).items, [24]);
  const selected = ['alpha']; assert.equal(helpers.filterNetworkOptions(fixtures['/access-group-network-options'], 'Second', selected, false)[0].tag, 'beta'); assert.deepEqual(selected, ['alpha']);

  const groups = await mount(AccessGroupManager); const g = groups.renderer;
  assert.equal(g.root.findAllByType('form').length, 0, 'Group form must start closed');
  assert.ok(text(g.toJSON()).includes('فقط مالک'), 'Restricted empty group must have the correct badge');
  await act(async () => { click(g, 'گروه دسترسی جدید'); await flush(); });
  await act(async () => {
    g.root.findAllByType('input').find(n => n.props.maxLength === 128).props.onChange({ target: { value: 'New network' } });
    checkbox(g, 'alpha').props.onChange({ target: { checked: true } });
  });
  await act(async () => { checkbox(g, '#1').props.onChange({ target: { checked: true } }); checkbox(g, 'reseller_one').props.onChange({ target: { checked: true } }); });
  await act(async () => { g.root.findAllByType('input').find(n => n.props['aria-label'] === 'جستجوی اینباند یا هاست').props.onChange({ target: { value: 'beta' } }); g.root.findAllByType('input').find(n => n.props['aria-label'] === 'جستجوی ادمین مجاز').props.onChange({ target: { value: 'reseller_two' } }); });
  await act(async () => { checkbox(g, 'beta').props.onChange({ target: { checked: true } }); });
  await act(async () => { checkbox(g, '#7').props.onChange({ target: { checked: true } }); });
  const submitGroup = () => g.root.findByType('form').props.onSubmit({ preventDefault() {} });
  await act(async () => { submitGroup(); submitGroup(); await flush(); });
  assert.equal(requests.length, 1, 'Repeated submit must not dispatch twice');
  assert.deepEqual(requests[0].options.body, { name: 'New network', description: null, node_ids: [], inbounds: ['alpha', 'beta'], hosts: { alpha: [1], beta: [7] }, allowed_admin_ids: [3] });
  await act(async () => { requests[0].reject(new Error('Simulated group error')); await flush(); });
  assert.ok(text(g.toJSON()).includes('Simulated group error'));
  assert.equal(g.root.findAllByType('input').find(n => n.props.maxLength === 128).props.value, 'New network');
  await act(async () => { submitGroup(); await flush(); });
  assert.deepEqual(requests[1].options.body, requests[0].options.body, 'Retry must retain hidden selections and values');
  await act(async () => { requests[1].resolve({ ...group, name: 'New network' }); await flush(); });
  assert.equal(g.root.findAllByType('form').length, 0, 'Successful group save must close the editor');
  g.unmount(); groups.client.clear(); requests.length = 0;

  const plans = await mount(Plans, { role: 'OWNER', account_status: 'ACTIVE', can_manage_plans: true }); const p = plans.renderer;
  assert.equal(p.root.findAllByType('input').some(n => n.props.placeholder === 'username'), false, 'Quick user fields must not be repeated on the plan list');
  await act(async () => { click(p, 'ساخت کاربر'); await flush(); });
  await act(async () => { p.root.findAllByType('input').find(n => n.props.placeholder === 'username').props.onChange({ target: { value: 'customer_one' } }); p.root.findAllByType('select').find(n => n.children.some(child => typeof child !== 'string' && child.type === 'option' && text(child) === 'انتخاب دسترسی شبکه')).props.onChange({ target: { value: '1' } }); });
  await act(async () => { const button = p.root.findAllByType('button').filter(n => text(n) === 'ساخت کاربر').find(n => n.props.isLoading !== undefined); assert.ok(!button.props.disabled); button.props.onClick(); await flush(); });
  assert.equal(requests[0].url, '/users/from-plan');
  assert.deepEqual({ ...requests[0].options.body, idempotency_key: undefined }, { plan_id: 8, access_group_id: 1, username: 'customer_one', status: 'active', idempotency_key: undefined });
  await act(async () => { requests[0].reject(new Error('Simulated user error')); await flush(); });
  assert.equal(p.root.findAllByType('input').find(n => n.props.placeholder === 'username').props.value, 'customer_one');
  assert.ok(text(p.toJSON()).includes('Simulated user error'));
  await act(async () => { p.root.findAllByType('button').find(n => n.props.loadingText === 'در حال ساخت').props.onClick(); await flush(); });
  await act(async () => { requests[1].resolve({ username: 'customer_one' }); await flush(); });
  assert.equal(p.root.findAllByType('input').some(n => n.props.placeholder === 'username'), false, 'Successful create must close the quick form');
  p.unmount(); plans.client.clear();
  const delegated = await mount(Plans, { role: 'ADMIN', account_status: 'ACTIVE', can_manage_plans: true });
  assert.equal(delegated.renderer.root.findAllByType('group-workspace').length, 0, 'Delegated manager must not mount Owner network management');
  delegated.renderer.unmount(); delegated.client.clear();
  console.log('Plans/Access UX: scopes, filtering, closed forms, hidden selections, payloads, pending, error/retry and success passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
