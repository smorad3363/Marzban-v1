const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const ts = require('typescript');
const React = require('react');
const { create, act } = require('react-test-renderer');
const { QueryClient, QueryClientProvider, setLogger } = require('react-query');
const root = path.resolve(__dirname, '../src');
const componentFile = path.join(root, 'components/AlertCenter.tsx');
const helperFile = path.join(root, 'components/alerts/presentation.ts');
const printer = ts.createPrinter({ removeComments: true });
const source = ts.createSourceFile(componentFile, fs.readFileSync(componentFile, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const protectedHashes = { streamEffect: 'cede1e9a79c49389ad55e5ddc6fafb50a3b635ffbd6c5f95905bc270d199864b', markSeen: 'd52f12cc619b63fccbe3e84638cab12dc322374d9782d6d144664f53b22d9179' };
const found = {};
function verifyTransport(node) {
  const key = ts.isCallExpression(node) && node.expression.getText(source) === 'useEffect' ? 'streamEffect' : ts.isVariableDeclaration(node) && node.name.getText(source) === 'markSeen' ? 'markSeen' : null;
  if (key) found[key] = crypto.createHash('sha256').update(printer.printNode(ts.EmitHint.Unspecified, node, source)).digest('hex');
  ts.forEachChild(node, verifyTransport);
}
verifyTransport(source);
assert.deepEqual(found, protectedHashes, 'Original authenticated stream, reconnect, receipt endpoint and failure behavior must remain unchanged');

const incident = (id, values = {}) => ({ id, admin_id: 2, admin_username: 'reseller_demo', resource: 'financial', state: 'frozen', severity: 'critical', revision: 2, seen: false, resolved_at: null, opened_at: '2026-11-07T07:00:00', details: { balance_toman: -10000, basis_toman: 100000, debt_percent: 10, freeze_percent: 10, cutoff_percent: 40, remaining_to_freeze_toman: 0, remaining_to_cutoff_toman: 30000 }, ...values });
const data = new Map();
const storage = { getItem: key => data.get(key) || null, setItem: (key, value) => data.set(key, value) };
let actor = { username: 'owner_test', is_sudo: true, role: 'OWNER' };
let pathname = '/plans/';
let authenticated = true;
let active = { items: [incident(105), incident(104, { severity: 'warning', state: 'low' }), incident(103, { seen: true })], counts: { critical: 2, warning: 1 }, next_before: 50, inherited_restriction: false, checked_at: new Date().toISOString().replace(/Z$/, '') };
const requests = [], pending = [], toasts = [];
const api = (url, options) => {
  requests.push({ url, options });
  if (options?.method) return new Promise((resolve, reject) => pending.push({ url, options, resolve: value => { active = { ...active, items: active.items.map(item => url.includes(`/${item.id}/seen?`) ? { ...item, seen: true } : item) }; resolve(value); }, reject }));
  if (!url.startsWith('/admin-management/alert-center')) throw Error(`Unexpected alert request: ${url}`);
  const params = new URL('https://example.invalid' + url).searchParams;
  if (params.get('status') === 'resolved') return Promise.resolve({ ...active, items: [incident(99, { resolved_at: '2026-11-07T07:01:00' })], next_before: null });
  if (params.get('before')) return Promise.resolve({ ...active, items: [incident(49, { seen: true })], next_before: null });
  return Promise.resolve(JSON.parse(JSON.stringify(active)));
};
const names = ['Alert', 'AlertIcon', 'Badge', 'Box', 'Button', 'Drawer', 'DrawerBody', 'DrawerCloseButton', 'DrawerContent', 'DrawerFooter', 'DrawerHeader', 'DrawerOverlay', 'HStack', 'Icon', 'Input', 'Select', 'Stack', 'Text', 'Tooltip'];
const chakra = { useToast: () => options => toasts.push(options), usePrefersReducedMotion: () => true };
for (const name of names) chakra[name] = React.forwardRef(({ children, ...props }, ref) => {
  if (name === 'Drawer' && !props.isOpen) return null;
  const tag = typeof props.as === 'string' ? props.as : ({ Button: 'button', DrawerCloseButton: 'button', Select: 'select', Input: 'input', Text: 'p' }[name] || 'div');
  return React.createElement(tag, { ...props, ref, disabled: props.isDisabled || props.isLoading }, children);
});
const originalLoad = Module._load;
const cache = new Map();
function load(file, fresh = false) {
  if (!fresh && cache.has(file)) return cache.get(file).exports;
  const m = new Module(file, module); m.filename = file; m.paths = Module._nodeModulePaths(path.dirname(file));
  if (!fresh) cache.set(file, m);
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2020 } }).outputText.replace(/import\.meta\.env\.VITE_BASE_API/g, '"/api/"');
  m._compile(code, file); return m.exports;
}
Module._load = function (name, parent, ...rest) {
  if (parent?.filename.startsWith(root)) {
    if (name === '@chakra-ui/react') return chakra;
    if (name === 'service/http') return { fetch: api };
    if (name === 'hooks/useGetUser') return { default: () => ({ userData: actor, getUserIsSuccess: authenticated }) };
    if (name === 'utils/authStorage') return { getAuthToken: () => 'synthetic-token' };
    if (name === 'utils/apiError') return { localizedApiError: error => error.message };
    if (name === 'react-router-dom') return { useLocation: () => ({ pathname }), Link: ({ children, to, ...props }) => React.createElement('a', { href: to, ...props }, children) };
    if (name === './AlertAccountActions') return { AlertAccountActions: () => React.createElement('div', null, 'Account actions') };
    if (name === './alerts/presentation') return load(helperFile);
  }
  return originalLoad.call(this, name, parent, ...rest);
};
const { AlertCenter } = load(componentFile);
const helpers = load(helperFile);
Module._load = originalLoad;
global.window = { localStorage: storage };
global.document = { hidden: true, addEventListener() {}, removeEventListener() {} };
setLogger({ log() {}, warn() {}, error() {} });
const text = node => typeof node === 'string' ? node : Array.isArray(node) ? node.map(text).join('') : (node?.children || []).map(text).join('');
const flush = () => new Promise(resolve => setTimeout(resolve, 15));
async function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, cacheTime: Infinity }, mutations: { retry: false } } });
  let renderer;
  await act(async () => { renderer = create(React.createElement(QueryClientProvider, { client }, React.createElement(AlertCenter, null, ({ trigger, summary }) => React.createElement('main', null, trigger, summary, React.createElement('workspace', null, 'Main content'))))); await flush(); });
  return { client, renderer, close: async () => { await act(async () => renderer.unmount()); client.clear(); } };
}
const button = (renderer, label) => {
  const node = renderer.root.findAllByType('button').find(n => text(n) === label);
  assert.ok(node, `Missing button ${label}`); assert.ok(!node.props.disabled, `Disabled button ${label}`); return node;
};
const click = async (renderer, label) => act(async () => { button(renderer, label).props.onClick(); await flush(); });
const trigger = renderer => renderer.root.findAllByType('button').find(n => n.props['aria-haspopup'] === 'dialog');

(async () => {
  const items = [incident(1), incident(2, { severity: 'warning' })];
  const original = JSON.stringify(items);
  assert.deepEqual(helpers.takeNewCriticalAlerts('receipts', items, storage).map(i => i.id), [1]);
  assert.equal(helpers.takeNewCriticalAlerts('receipts', items, storage).length, 0);
  assert.equal(load(helperFile, true).takeNewCriticalAlerts('receipts', items, storage).length, 0, 'Reload must retain presentation receipts');
  assert.equal(helpers.takeNewCriticalAlerts('another-actor', items, storage).length, 1, 'Receipts must be scoped to the viewer');
  assert.equal(helpers.takeNewCriticalAlerts('receipts', [incident(1, { seen: true, revision: 3 })], storage).length, 0);
  assert.equal(helpers.takeNewCriticalAlerts('receipts', [incident(1, { revision: 4, state: 'disabled' })], storage).length, 1, 'A newly worsened critical revision must notify');
  assert.equal(helpers.takeNewCriticalAlerts('receipts', [incident(1, { revision: 5, resolved_at: '2026-11-07' })], storage).length, 0);
  assert.equal(helpers.takeNewCriticalAlerts('receipts', [incident(1, { revision: 6, severity: 'warning' })], storage).length, 0, 'A downgrade must stay quiet');
  assert.equal(helpers.takeNewCriticalAlerts('receipts', [], storage).length, 0, 'Resolution/removal must never toast');
  assert.equal(helpers.takeNewCriticalAlerts('already-seen', [incident(8, { seen: true })], storage).length, 0);
  assert.equal(JSON.stringify(items), original, 'Presentation receipts must not mutate active/seen state');
  const broken = { getItem() { throw Error('blocked'); }, setItem() { throw Error('quota'); } };
  assert.equal(helpers.takeNewCriticalAlerts('private-mode', [incident(9)], broken).length, 1);
  assert.equal(helpers.takeNewCriticalAlerts('private-mode', [incident(9)], broken).length, 0);
  const corrupt = { getItem: () => 'not JSON', setItem() {} };
  assert.doesNotThrow(() => helpers.takeNewCriticalAlerts('corrupt', [incident(9)], corrupt));
  helpers.takeNewCriticalAlerts('bounded', Array.from({ length: 400 }, (_, n) => incident(n + 1)), storage);
  assert.equal(JSON.parse([...data].find(([key]) => key.endsWith(':bounded'))[1]).length, 256);
  assert.ok([...data.values()].every(value => !value.includes('balance') && !value.includes('synthetic-token') && !value.includes('reseller_demo')));
  assert.equal(helpers.fa(undefined), '—');
  assert.equal(helpers.alertTime('bad date'), 'زمان نامشخص');
  assert.equal(helpers.alertTime('2026-11-07T07:00:00Z'), helpers.alertTime('2026-11-07T07:00:00'));

  const first = await mount(); const r = first.renderer;
  assert.equal(r.root.findAllByType(chakra.DrawerContent).length, 0, 'Drawer must start closed on ordinary pages');
  assert.equal(r.root.findAllByType('section').length, 0, 'Ordinary pages must not receive an alert summary banner');
  assert.equal(requests.filter(x => !x.options).length, 1, 'Closed panel should load only the original summary query');
  assert.equal(toasts.length, 1); assert.equal(toasts[0].status, 'error');
  assert.ok(trigger(r).props['aria-label'].includes('۲ هشدار حیاتی'));
  await act(async () => { await first.client.refetchQueries(['alert-center', actor.username], { exact: true }); await flush(); });
  assert.equal(toasts.length, 1, 'Polling must not repeat an announced critical incident');
  await act(async () => { trigger(r).props.onClick(); await flush(); });
  assert.equal(r.root.findAllByType('article').length, 3);
  assert.ok(r.root.findByProps({ id: 'alert-center-filters' }).props.hidden);
  assert.ok(r.root.findByProps({ id: 'alert-center-diagnostics' }).props.hidden);
  assert.equal(requests.filter(x => !x.options).length, 2, 'Opening without filters must not add a details request');
  const firstCard = r.root.findAllByType('article')[0];
  await act(async () => { firstCard.findAllByType('button').find(n => text(n) === 'دیده شد').props.onClick(); await flush(); });
  assert.equal(pending[0].url, '/admin-management/alert-center/105/seen?revision=2');
  assert.deepEqual(pending[0].options, { method: 'POST' });
  await act(async () => { pending[0].reject(new Error('Receipt failed')); await flush(); });
  assert.equal(toasts.at(-1).title, 'Receipt failed');
  assert.equal(first.client.getQueryData(['alert-center', actor.username]).items.find(i => i.id === 105).seen, false, 'Failed receipt must remain retryable');
  await act(async () => { firstCard.findAllByType('button').find(n => text(n) === 'دیده شد').props.onClick(); pending[1].resolve({ ok: true }); await flush(); });
  assert.equal(first.client.getQueryData(['alert-center', actor.username]).counts.critical, 2, 'Seen must not resolve an active incident or change counts');
  assert.equal(first.client.getQueryData(['alert-center', actor.username]).items.find(i => i.id === 105).seen, true);
  await click(r, 'فیلترها');
  const status = r.root.findByProps({ 'aria-label': 'وضعیت هشدار' });
  await act(async () => { status.props.onChange({ target: { value: 'resolved' } }); await flush(); });
  assert.equal(requests.at(-1).url, '/admin-management/alert-center?status=resolved');
  await act(async () => { r.root.findByProps({ 'aria-label': 'اهمیت هشدار' }).props.onChange({ target: { value: 'critical' } }); await flush(); });
  await act(async () => { r.root.findByProps({ 'aria-label': 'جستجوی ادمین هشدار' }).props.onChange({ target: { value: ' reseller ' } }); });
  await act(async () => { r.root.findByProps({ 'aria-label': 'جستجوی ادمین هشدار' }).props.onKeyDown({ key: 'Enter' }); await flush(); });
  assert.equal(requests.at(-1).url, '/admin-management/alert-center?status=resolved&severity=critical&username=reseller');
  assert.ok(r.root.findAllByType('article').some(n => text(n).includes('رفع‌شده')));
  await act(async () => {
    status.props.onChange({ target: { value: 'active' } });
    r.root.findByProps({ 'aria-label': 'اهمیت هشدار' }).props.onChange({ target: { value: '' } });
    r.root.findByProps({ 'aria-label': 'جستجوی ادمین هشدار' }).props.onChange({ target: { value: '' } });
  });
  await click(r, 'فیلتر'); await click(r, 'موارد قدیمی‌تر');
  assert.equal(requests.at(-1).url, '/admin-management/alert-center?status=active&before=50');
  await act(async () => { r.root.findByType(chakra.Drawer).props.onClose(); await flush(); });
  const requestCount = requests.length;
  await act(async () => { await first.client.invalidateQueries(['alert-center', actor.username]); await flush(); });
  assert.equal(requests.length, requestCount + 1, 'Closed filtered views must keep only the foreground summary active');
  await first.close();

  pathname = '/'; actor = { username: 'dashboard_owner', role: 'OWNER', is_sudo: true };
  const dashboard = await mount();
  assert.equal(dashboard.renderer.root.findAllByType('section').length, 1, 'Dashboard must retain a bounded active-incident summary');
  assert.equal(dashboard.renderer.root.findAllByType(chakra.DrawerContent).length, 0, 'Dashboard must not auto-open the full list');
  await dashboard.close();
  active = { ...active, items: [], counts: { critical: 0, warning: 0 }, next_before: null };
  const empty = await mount();
  assert.equal(empty.renderer.root.findAllByType('section').length, 0, 'Healthy accounts must not get an empty banner');
  assert.ok(trigger(empty.renderer));
  await act(async () => { trigger(empty.renderer).props.onClick(); await flush(); });
  assert.ok(text(empty.renderer.toJSON()).includes('هشدار فعالی وجود ندارد'));
  await empty.close();
  actor = { username: 'delegated_test', role: 'ADMIN', is_sudo: false }; active = { ...active, inherited_restriction: true };
  const delegated = await mount();
  assert.ok(trigger(delegated.renderer).props['aria-label'].includes('حساب بالادستی محدود شده'));
  await act(async () => { trigger(delegated.renderer).props.onClick(); await flush(); });
  assert.ok(text(delegated.renderer.toJSON()).includes('هشدارهای خودتان و زیرمجموعه‌هایتان'));
  assert.ok(!text(delegated.renderer.toJSON()).includes('مدیریت حساب ادمین'));
  await delegated.close();
  authenticated = false;
  const unauthenticated = await mount();
  assert.equal(trigger(unauthenticated.renderer), undefined);
  assert.ok(text(unauthenticated.renderer.toJSON()).includes('Main content'), 'Alert loading must not hide the rest of the shell');
  await unauthenticated.close();
  console.log('Alert center: persistent critical-only notifications, reload/error receipts, unchanged transport, active counts, scoped Drawer, filters, pagination and empty states passed');
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => { delete global.window; delete global.document; });
