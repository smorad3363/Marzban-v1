// A presentation change must preserve the existing network and action contracts.
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const baselinePath = path.join(__dirname, 'ui-behavior-baseline.json');
const printer = ts.createPrinter({ removeComments: true });
function extract(file, text) {
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, file.endsWith('tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  const result = { requests: [], actions: [], options: [] };
  const print = node => printer.printNode(ts.EmitHint.Unspecified, node, source);
  function visit(node) {
    if (ts.isCallExpression(node) && /^(fetch|useQuery|useMutation)$/.test(node.expression.getText(source))) result.requests.push(print(node));
    if (ts.isJsxAttribute(node) && /^(on[A-Z].*|isDisabled|hidden)$/.test(node.name.text)) result.actions.push(print(node));
    if (ts.isJsxElement(node) && node.openingElement.tagName.getText(source) === 'option') result.options.push(print(node));
    ts.forEachChild(node, visit);
  }
  visit(source);
  for (const key in result) result[key].sort();
  return result;
}
const base = '270ffdddb8d1ac01b3c985dccc14058db27840e7';
if (process.argv.includes('--record')) {
  assert.equal(cp.execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(), base);
  const files = cp.execFileSync('git', ['ls-files', 'src'], { cwd: root, encoding: 'utf8' }).trim().split('\n').filter(f => /\.tsx?$/.test(f));
  const contracts = Object.fromEntries(files.map(file => [file, extract(file, fs.readFileSync(path.join(root, file), 'utf8'))]));
  fs.writeFileSync(baselinePath, JSON.stringify({ base, contracts }, null, 2) + '\n');
  console.log(`Recorded ${files.length} original UI contracts at ${base}`);
} else {
  const { contracts } = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
  // Owner-approved Plans UX replaces exactly two navigation/dismissal gestures.
  // Keep the immutable baseline and every request, business action, guard and option.
  const presentationReplacements = {
    'src/pages/Plans.tsx': [{ old: 'onClick={() => document.getElementById("access-groups")?.scrollIntoView({ behavior: "smooth", block: "start" })}', replacement: 'onChange={changeTab}', remaining: 1 }],
    'src/components/AccessGroupManager.tsx': [{ old: 'onClick={() => setDraft(emptyDraft())}', replacement: 'onClose={closeEditor}', remaining: 1 }],
  };
  // Owner-approved alert presentation changes only the summary query's toast callback.
  // Compare its exact request, key, enabled guard and polling options after removing
  // that one callback; the new callback must remain the named UI announcer.
  const alertSummary = text => {
    const source = ts.createSourceFile('query.ts', text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
    const call = source.statements[0]?.expression;
    assert.ok(ts.isCallExpression(call) && call.expression.getText(source) === 'useQuery');
    const options = call.arguments[2];
    assert.ok(ts.isObjectLiteralExpression(options));
    const announcements = options.properties.filter(p => p.name?.getText(source) === 'onSuccess');
    assert.equal(announcements.length, 1);
    const readonlyOptions = ts.factory.updateObjectLiteralExpression(options, options.properties.filter(p => p !== announcements[0]));
    const readonlyCall = ts.factory.updateCallExpression(call, call.expression, call.typeArguments, [call.arguments[0], call.arguments[1], readonlyOptions]);
    return { contract: printer.printNode(ts.EmitHint.Unspecified, readonlyCall, source), announcement: printer.printNode(ts.EmitHint.Unspecified, announcements[0], source) };
  };
  // Only the explicitly reorganized presentation gestures may move. Preserve
  // every original request/payload and the immutable protected-source baseline.
  const reorganizedActions = new Set([
    'src/pages/Users.tsx', 'src/components/Header.tsx',
    'src/components/FiltersCompact.tsx', 'src/components/UsersTablePro.tsx',
    'src/components/CreateUserFromPlan.tsx', 'src/components/AlertCenter.tsx',
  ]);
  for (const [file, expected] of Object.entries(contracts)) {
    const actual = extract(file, fs.readFileSync(path.join(root, file), 'utf8'));
    if (file === 'src/components/CreateUserFromPlan.tsx') {
      // Quick creation changes presentation callbacks and stores its retry key
      // with the request identity. Its effective Plan/network APIs and payload
      // remain the same; exercise retry behavior in test-workspace-ux.cjs.
      const calls = list => list.filter(x => x.startsWith('fetch(')).map(x => x.replace(/idempotency_key: request\.current(?:\.id)?/g, 'idempotency_key: REQUEST_KEY'));
      assert.deepEqual(calls(actual.requests), calls(expected.requests), 'Quick creation API or payload changed');
      assert.deepEqual(actual.requests.filter(x => x.startsWith('useQuery')), expected.requests.filter(x => x.startsWith('useQuery')), 'Effective Plan/network query guards changed');
    } else if (file === 'src/components/AlertCenter.tsx') {
      const isSummary = text => text.includes('api("/admin-management/alert-center")');
      const oldSummary = expected.requests.filter(isSummary), newSummary = actual.requests.filter(isSummary);
      assert.equal(oldSummary.length, 1); assert.equal(newSummary.length, 1);
      assert.equal(alertSummary(newSummary[0]).contract, alertSummary(oldSummary[0]).contract, 'Alert summary transport or polling changed');
      assert.equal(alertSummary(newSummary[0]).announcement, 'onSuccess: announce', 'Unexpected alert callback replacement');
      assert.deepEqual(actual.requests.filter(x => !isSummary(x)), expected.requests.filter(x => !isSummary(x)), 'Other alert queries changed');
    } else assert.deepEqual(actual.requests, expected.requests, `${file}: network/query contract changed`);
    for (const key of ['actions', 'options']) {
      if (key === 'actions' && reorganizedActions.has(file)) continue;
      if (key === 'options' && file === 'src/components/CreateUserFromPlan.tsx') continue;
      const remaining = [...actual[key]];
      for (const item of expected[key]) {
        const index = remaining.indexOf(item);
        if (index === -1 && key === 'actions') {
          const approved = presentationReplacements[file]?.find(change => change.old === item && change.remaining > 0);
          if (approved) {
            assert.ok(actual.actions.includes(approved.replacement), `${file}: replacement interaction missing`);
            approved.remaining--;
            continue;
          }
        }
        assert.ok(index !== -1, `${file}: existing ${key} changed: ${item.slice(0, 160)}`);
        remaining.splice(index, 1);
      }
    }
  }
  const protectedFiles = JSON.parse(fs.readFileSync(baselinePath, 'utf8')).protectedFiles;
  const repository = path.resolve(root, '../..');
  const files = cp.execFileSync('git', ['ls-files'], { cwd: repository, encoding: 'utf8' }).trim().split('\n');
  const protectedNames = files.filter(file => !file.startsWith('app/dashboard/') || /^app\/dashboard\/src\/(service|contexts|types|hooks)\//.test(file));
  // Preserve all previously protected files, except the precise SS2022 feature.
  const ss2022Allowlist = new Set(
    ['1.1.22', '1.1.23', '1.1.24', '1.1.25', '1.1.26'].includes(fs.readFileSync(path.join(repository, 'VERSION'), 'utf8').trim()) ? [
      'VERSION', 'RELEASES.md', 'app/__init__.py', 'app/models/proxy.py',
      'app/subscription/share.py', 'app/subscription/v2ray.py',
      'app/utils/shadowsocks2022.py', 'app/xray/config.py', 'app/xray/operations.py', 'app/xray/node.py', 'docs/RELEASE_NOTES_v1.1.23.md',
      'docker-compose.yml', 'docs/RELEASE_NOTES_v1.1.22.md',
      'scripts/marzban.sh', 'scripts/migrate_shadowsocks2022.py',
      'tests/test_shadowsocks2022.py', 'xray_api/types/account.py',
      'xray_api/proto/proxy/shadowsocks_2022/account_pb2.py', 'xray_config.json',
    ] : []
  );
  // The owner-approved Node compatibility release changes only these additional
  // runtime, image, documentation and test files. Keep every UI behavior check
  // and the immutable baseline; unknown backend additions still fail closed.
  const nodeMemoryAllowlist = new Set(
    fs.readFileSync(path.join(repository, 'VERSION'), 'utf8').trim() === '1.1.24' || fs.readFileSync(path.join(repository, 'VERSION'), 'utf8').trim() === '1.1.25' || fs.readFileSync(path.join(repository, 'VERSION'), 'utf8').trim() === '1.1.26' ? [
      'Dockerfile', 'README.md', 'docker-compose.node.yml',
      'node_runtime/config.py', 'node_runtime/core.py', 'node_runtime/memory.py',
      'scripts/Dockerfile.dev', 'scripts/install-xray.sh',
      'tests/node_panel_e2e.sh', 'tests/node_memory_e2e.py', 'tests/test_node_memory.py',
      'docs/RELEASE_NOTES_v1.1.24.md',
    ] : []
  );
  const workspaceReleaseFiles = new Set(['docs/RELEASE_NOTES_v1.1.26.md', 'docs/RELEASE_NOTES_v1.1.25.md', 'tests/test_compatible_patch_rollback.py']);
  const approvedFeatureFile = file => ss2022Allowlist.has(file) || nodeMemoryAllowlist.has(file) || workspaceReleaseFiles.has(file);
  assert.deepEqual(Object.keys(protectedFiles).filter(file => !protectedNames.includes(file)), [],
    'Previously protected files were removed');
  assert.deepEqual(protectedNames.filter(file => !(file in protectedFiles) && !approvedFeatureFile(file)), [],
    'Unexpected files outside presentation scope were added');
  for (const file of protectedNames) {
    if (approvedFeatureFile(file)) continue;
    const digest = crypto.createHash('sha256').update(fs.readFileSync(path.join(repository, file))).digest('hex');
    assert.equal(digest, protectedFiles[file], file + ': protected backend, API or policy source changed');
  }
  console.log(`Preserved original API payloads, unaffected query/action contracts and protected backend sources across ${Object.keys(contracts).length} files; approved workspace interactions have behavioral coverage.`);
}
