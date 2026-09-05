const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

const read = (relative) => fs.readFileSync(path.resolve(__dirname, "..", relative), "utf8");
const source = read("src/utils/accessGroupScope.ts");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    strict: true,
  },
});
const loaded = { exports: {} };
new Function("exports", "module", "require", compiled.outputText)(
  loaded.exports,
  loaded,
  require
);

const {
  missingAccessGroupHostIds,
  missingAccessGroupInboundTags,
  normalizeAccessGroupHostScope,
  normalizeAccessGroupInboundTags,
  toggleAccessGroupHostId,
  toggleAccessGroupInboundTag,
} = loaded.exports;
const options = [
  { tag: "vless-reality", hosts: [{ id: 1 }, { id: 2 }] },
  { tag: "vmess-ws", hosts: [{ id: 7 }] },
];

let selected = toggleAccessGroupInboundTag([], "vmess-ws", true);
selected = toggleAccessGroupInboundTag(selected, "vless-reality", true);
assert.deepEqual(selected, ["vless-reality", "vmess-ws"]);
assert.deepEqual(normalizeAccessGroupInboundTags(["vmess-ws", "vmess-ws"]), ["vmess-ws"]);
assert.deepEqual(missingAccessGroupInboundTags([...selected, "legacy"], options), ["legacy"]);

let hosts = normalizeAccessGroupHostScope({ "vless-reality": [2, 1, 2] });
assert.deepEqual(hosts, { "vless-reality": [1, 2] });
hosts = toggleAccessGroupHostId(hosts, "vless-reality", 3, true);
assert.deepEqual(missingAccessGroupHostIds(hosts, options), [3]);
hosts = toggleAccessGroupHostId(hosts, "vless-reality", 3, false);
assert.deepEqual(hosts, { "vless-reality": [1, 2] });

const manager = read("src/components/AccessGroupManager.tsx");
const plans = read("src/pages/Plans.tsx");
const planModal = read("src/components/PlanCreateModal.tsx");
const userModal = read("src/components/CreateUserFromPlan.tsx");
assert.ok(manager.includes('fetch("/access-group-network-options")'));
assert.ok(manager.includes('method: draft.id ? "PUT" : "POST"'));
assert.ok(manager.includes('fetch(`/access-groups/${group.id}`, { method: "DELETE" })'));
assert.ok(manager.includes("node_ids: draft.nodeIds"));
assert.ok(manager.includes("inbounds: normalizeAccessGroupInboundTags"));
assert.ok(manager.includes("hosts: normalizeAccessGroupHostScope"));
assert.equal(plans.includes("plan-network-options"), false);
assert.equal(planModal.includes("plan-network-options"), false);
assert.equal(/version:\s*\{[\s\S]*?inbounds:/.test(planModal), false);
assert.ok(userModal.includes("access_group_id: Number(groupId)"));
assert.equal(userModal.includes("Use Plan network"), false);

console.log("Access Group UI contract: assertions passed");
