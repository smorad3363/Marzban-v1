const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const products = read("src/pages/Products.tsx");
const router = read("src/pages/Router.tsx");
const header = read("src/components/Header.tsx");

assert.ok(router.includes('path: "/products/"'), "Products must have a dedicated route");
assert.ok(router.includes("<OwnerOnly><Products /></OwnerOnly>"), "Product editor must be Owner-only");
assert.equal((header.match(/to="\/products\/"/g) || []).length, 2, "mobile and desktop navigation must expose Products to Owner");

for (const required of [
  'fetch<Product[]>("/products?include_archived=true")',
  'fetch<Product>(draft.id ? `/products/${draft.id}` : "/products"',
  "traffic_price_multiplier: draft.multiplier.trim()",
  "inbounds: normalizeAccessGroupInboundTags(draft.inbounds)",
  "hosts: normalizeAccessGroupHostScope(draft.hosts)",
  'fetch(`/products/${product.id}`, { method: "DELETE" })',
  'fetch(`/products/${product.id}/restore`, { method: "POST" })',
]) {
  assert.ok(products.includes(required), `Product UI contract is missing: ${required}`);
}

for (const forbidden of [
  "price_toman",
  "data_limit",
  "duration_days",
  "concurrent_user_limit",
  "node_ids",
  "access_group_id",
  "/user-plans",
]) {
  assert.ok(!products.includes(forbidden), `Product editor must not expose legacy field/path: ${forbidden}`);
}

assert.ok(products.includes("ضریب قیمت ترافیک"), "Product editor must expose the positive multiplier");
assert.ok(products.includes("اینباند و هاست"), "Product editor must expose Owner network selection");
assert.ok(products.includes("این صفحه حجم، مدت، تعداد دستگاه یا قیمت ثابت را مدیریت نمی‌کند"), "Product UI must explain commercial-field separation");

console.log("product UI contracts: assertions passed");
