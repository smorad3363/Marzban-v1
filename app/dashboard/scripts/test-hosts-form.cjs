const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const read = name => fs.readFileSync(path.join(__dirname, '../src/', name), 'utf8');
const compiled = ts.transpileModule(read('utils/hostsForm.ts'), {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020}});
const loaded = {exports: {}};
new Function('exports', 'module', 'require', compiled.outputText)(loaded.exports, loaded, require);
const {hostsSchema, duplicateHostValues} = loaded.exports;
const host = {id: 7, remark: 'Default', address: '{SERVER_IP}', port: null, path: null, sni: null, host: null, security: 'inbound_default', alpn: '', fingerprint: '', fragment_setting: null, noise_setting: null};
const parse = value => hostsSchema.parse({'Shadowsocks TCP': [value]})['Shadowsocks TCP'][0];
assert.equal(parse(host).id, 7);
assert.equal(parse({...host, id: null}).id, undefined);
assert.equal(parse({...host, id: undefined}).is_disabled, false);
const clone = duplicateHostValues(host);
assert.equal(parse(clone).id, undefined);
assert.equal(clone.address, host.address);
assert.equal(host.id, 7);
assert.equal(hostsSchema.safeParse({'Shadowsocks TCP': [{...host, remark: '', address: ''}]}).success, false);
const dialog = read('components/HostsDialog.tsx');
assert.ok(dialog.includes('keyName: "_formKey"'));
assert.ok(dialog.includes('Promise.all([fetchHosts(), fetchInbounds()])'));
assert.ok(dialog.includes('queryClient.invalidateQueries("access-group-network-options")'));
assert.ok(dialog.includes('form.handleSubmit(handleFormSubmit, '));
assert.equal(dialog.includes('inbound.port'), false);
console.log('Host form regressions: passed');

// Reproduce browser native validation with real Chakra rendered markup. A
// required group must not make every optional Inbound/Host checkbox required.
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const { ChakraProvider } = require('@chakra-ui/react');
const { QueryClient, QueryClientProvider } = require('react-query');
const draft = {id: 1, name: 'Test group', description: '', nodeIds: [], inbounds: ['Shadowsocks TCP'], hosts: {'Shadowsocks TCP': [1]}, allowedAdminIds: []};
function loadComponent(name, overrides = {}) {
  const output = ts.transpileModule(read(name), {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX}}).outputText;
  const module = {exports: {}};
  new Function('exports', 'module', 'require', output)(module.exports, module, name => overrides[name] || require(name));
  return module.exports;
}
const scopes = loadComponent('utils/accessGroupScope.ts');
// Keep real Chakra inputs/checkboxes; render the now-on-demand dialog inline
// because portals do not emit their body in server-rendered markup.
const chakra = require('@chakra-ui/react');
const inline = ({children}) => React.createElement('div', null, children);
let firstBoolean = true;
const { AccessGroupManager } = loadComponent('components/AccessGroupManager.tsx', {
  react: {...React, useState: (initial) => {
    if (typeof initial === 'function') return React.useState(draft);
    if (typeof initial === 'boolean' && firstBoolean) { firstBoolean = false; return React.useState(true); }
    return React.useState(initial);
  }},
  '@chakra-ui/react': {...chakra, Modal: inline, ModalBody: inline, ModalHeader: inline, ModalFooter: inline,
    ModalOverlay: () => null, ModalCloseButton: () => null,
    ModalContent: ({children, onSubmit}) => React.createElement('form', {onSubmit}, children)},
  'design-system/Console': {EmptyState: inline, Surface: inline},
  'components/plans/CatalogPager': loadComponent('components/plans/CatalogPager.tsx'),
  'components/plans/presentation': loadComponent('components/plans/presentation.ts'),
  'service/http': {fetch: () => Promise.resolve([])},
  'utils/apiError': {localizedApiError: () => 'error'},
  'utils/accessGroupScope': scopes,
});
const client = new QueryClient({defaultOptions: {queries: {staleTime: Infinity, cacheTime: Infinity}}});
client.setQueryData('access-groups', []);
client.setQueryData('access-group-node-options', []);
client.setQueryData('access-group-admin-options', []);
client.setQueryData('access-group-network-options', [
  {tag: 'Shadowsocks TCP', protocol: 'shadowsocks', network: 'tcp', hosts: [{id: 1, remark: 'Selected'}]},
  {tag: 'TROJAN + WS', protocol: 'trojan', network: 'ws', hosts: [{id: 2, remark: 'Optional'}]},
]);
const html = renderToStaticMarkup(React.createElement(ChakraProvider, null, React.createElement(QueryClientProvider, {client}, React.createElement(AccessGroupManager))));
const checkboxes = html.match(/<input\b[^>]*type="checkbox"[^>]*>/g) || [];
assert.ok(checkboxes.length >= 3, 'must exercise selected Host plus an unchecked Inbound');
assert.ok(checkboxes.every(input => !/\srequired(?:=|\s|>)/.test(input)), 'optional network choices must not trigger browser required validation');
assert.ok(html.includes('required=""'), 'the group name must still be required');
const searches = html.match(/<input\b[^>]*type="search"[^>]*>/g) || [];
assert.ok(searches.length >= 2, 'must exercise network and Admin searches');
assert.ok(searches.every(input => !/\srequired(?:=|\s|>)/.test(input)), 'search fields must not become required choices');
const inputIds = [...html.matchAll(/<input\b[^>]*\bid="([^"]+)"/g)].map(match => match[1]);
assert.equal(new Set(inputIds).size, inputIds.length, 'searches and optional choices must have distinct label targets');

client.clear();
console.log('Access Group checkbox native validation: passed');
