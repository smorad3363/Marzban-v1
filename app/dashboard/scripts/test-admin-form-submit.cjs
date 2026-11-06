const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const React = require("react");
const { create, act } = require("react-test-renderer");
const chakra = require("@chakra-ui/react");
const { QueryClient, QueryClientProvider, setLogger } = require("react-query");

// Exercise the real form, mutation/cache hooks and Chakra loading button.
// Only the portal/layout and the API transport are replaced for Node rendering.
const componentPath = path.resolve(__dirname, "../src/components/AdminFormDrawer.tsx");
const requests = [];
const toasts = [];
const capabilities = { hierarchy_enabled: true, allowed_child_billing_modes: ["ALLOCATED_TRAFFIC"] };
const account = { role: "OWNER", user_creation_mode: "BOTH" };
const inbounds = new Map();
const translations = { "admins.create": "Create Admin", save: "Save changes", cancel: "Cancel" };
const layoutTags = { Modal: "mock-modal", ModalContent: "form", ModalFooter: "footer", Input: "input" };
const layout = (name) => React.forwardRef(({ children, ...props }, ref) =>
  name === "Modal" && !props.isOpen ? null : React.createElement(layoutTags[name] || "div", { ...props, ref }, children)
);
const mockChakra = { Button: chakra.Button, useToast: () => (message) => toasts.push(message) };
for (const name of ["Alert", "AlertIcon", "Badge", "Box", "Checkbox", "Code", "Flex", "FormControl", "FormHelperText", "FormLabel", "HStack", "Input", "Modal", "ModalBody", "ModalCloseButton", "ModalContent", "ModalFooter", "ModalHeader", "ModalOverlay", "SimpleGrid", "Skeleton", "Stack", "Switch", "Tag", "TagCloseButton", "TagLabel", "Text"]) {
  mockChakra[name] = layout(name);
}
const fetch = (url, options) => {
  if (options?.method) return new Promise((resolve, reject) => requests.push({ url, options, resolve, reject }));
  if (url === "/admin/capabilities") return Promise.resolve(capabilities);
  if (url === "/account/summary") return Promise.resolve(account);
  if (url === "/plan-categories") return Promise.resolve([]);
  throw new Error(`Unexpected request: ${url}`);
};
const originalLoad = Module._load;
Module._load = function (name, parent, ...rest) {
  if (parent?.filename === componentPath) {
    if (name === "@chakra-ui/react") return mockChakra;
    if (name === "contexts/DashboardContext") return { useDashboard: () => ({ inbounds }) };
    if (name === "react-i18next") return { useTranslation: () => ({ t: (key) => translations[key] || key, i18n: { dir: () => "rtl" } }) };
    if (name === "service/http") return { fetch };
    if (name === "utils/apiError") return { localizedApiError: (error) => error.message };
  }
  return originalLoad.call(this, name, parent, ...rest);
};
const compiled = ts.transpileModule(fs.readFileSync(componentPath, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2020 },
}).outputText;
const componentModule = new Module(componentPath, module);
componentModule.filename = componentPath;
componentModule.paths = Module._nodeModulePaths(path.dirname(componentPath));
componentModule._compile(compiled, componentPath);
const { AdminFormDrawer } = componentModule.exports;
Module._load = originalLoad;

const text = (node) => typeof node === "string" ? node : node.children.map(text).join("");
const flush = () => new Promise((resolve) => setTimeout(resolve, 10));
setLogger({ log() {}, warn() {}, error() {} });

(async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, cacheTime: Infinity }, mutations: { retry: false } } });
  client.setQueryData("admin-capabilities", capabilities);
  client.setQueryData("account-summary", account);
  client.setQueryData("plan-categories", []);
  client.setQueryData(["admin-management", 0, "", "", ""], { admins: [], total: 0 });
  let closes = 0;
  let renderer;
  await act(async () => {
    renderer = create(React.createElement(chakra.ThemeProvider, { theme: chakra.theme },
      React.createElement(chakra.LightMode, null, React.createElement(QueryClientProvider, { client }, React.createElement(AdminFormDrawer, { isOpen: true, admin: null, onClose: () => closes++ })))
    ));
  });
  const submitButton = () => renderer.root.findAllByType("button").find((node) => node.props.type === "submit");
  const click = (label) => renderer.root.findAllByType("button").find((node) => text(node).includes(label)).props.onClick();
  const change = (match, value) => renderer.root.findAllByType("input").find(match).props.onChange({ target: { value } });
  const submit = () => renderer.root.findByType("form").props.onSubmit({ preventDefault() {} });

  await act(async () => {
    change((node) => node.props.maxLength === 34, "diagnostic_admin");
    change((node) => node.props.type === "password", "diagnostic-only");
    click("بر اساس حجم ساخته‌شده");
    click("فقط فرم دلخواه");
  });
  assert.equal(text(submitButton()), "Create Admin");
  await act(async () => { submit(); submit(); await flush(); });
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, "/admin-management");
  assert.equal(requests[0].options.body.username, "diagnostic_admin");
  assert.match(text(submitButton()), /در حال ساخت/);
  assert.equal(submitButton().props.disabled, true);
  assert.equal(closes, 0);
  await act(async () => {
    submit();
    renderer.root.findByType("mock-modal").props.onClose();
  });
  assert.equal(requests.length, 1, "pending submits must not create another request");
  assert.equal(closes, 0, "pending save must retain the form");

  await act(async () => { requests[0].reject(new Error("Diagnostic conflict")); await flush(); });
  assert.equal(closes, 0);
  assert.match(text(renderer.root.findByType("footer")), /Diagnostic conflict/);
  assert.equal(text(submitButton()), "Create Admin");
  assert.equal(submitButton().props.disabled, false);
  assert.equal(renderer.root.findAllByType("input").find((node) => node.props.maxLength === 34).props.value, "diagnostic_admin");

  await act(async () => { submit(); await flush(); });
  assert.equal(requests.length, 2, "the failed form must allow a deliberate retry");
  await act(async () => { requests[1].resolve({ id: 99, username: "diagnostic_admin" }); await flush(); });
  assert.equal(closes, 1, "only a successful response may close the form");
  assert.equal(client.getQueryState(["admin-management", 0, "", "", ""]).isInvalidated, true);
  assert(toasts.some((toast) => toast.status === "success"));
  await act(async () => { renderer.unmount(); });
  client.clear();
  console.log("Admin form submission: pending, error, retry and success passed");
})().catch((error) => { console.error(error); process.exitCode = 1; });
