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
  for (const [file, expected] of Object.entries(contracts)) {
    const actual = extract(file, fs.readFileSync(path.join(root, file), 'utf8'));
    assert.deepEqual(actual.requests, expected.requests, `${file}: network/query contract changed`);
    for (const key of ['actions', 'options']) {
      const remaining = [...actual[key]];
      for (const item of expected[key]) {
        const index = remaining.indexOf(item);
        assert.ok(index !== -1, `${file}: existing ${key} changed: ${item.slice(0, 160)}`);
        remaining.splice(index, 1);
      }
    }
  }
  const protectedFiles = JSON.parse(fs.readFileSync(baselinePath, 'utf8')).protectedFiles;
  const repository = path.resolve(root, '../..');
  const files = cp.execFileSync('git', ['ls-files'], { cwd: repository, encoding: 'utf8' }).trim().split('\n');
  const protectedNames = files.filter(file => !file.startsWith('app/dashboard/') || /^app\/dashboard\/src\/(service|contexts|types|hooks)\//.test(file));
  assert.deepEqual(protectedNames.sort(), Object.keys(protectedFiles).sort(), 'Files outside the presentation scope were added or removed');
  for (const file of protectedNames) {
    const digest = crypto.createHash('sha256').update(fs.readFileSync(path.join(repository, file))).digest('hex');
    assert.equal(digest, protectedFiles[file], `${file}: protected backend, API or policy source changed`);
  }
  console.log(`Preserved network calls, query configuration, existing actions and options in ${Object.keys(contracts).length} files; backend unchanged.`);
}
