const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const input = read("src/components/Input.tsx");
const appShell = read("src/components/AppShell.tsx");
const login = read("src/pages/Login.tsx");

assert.ok(
  input.includes('autoComplete = type === "password" ? "new-password" : "off"'),
  "shared Input must suppress credential autofill by default"
);
assert.ok(input.includes('autoComplete={autoComplete}'), "shared Input must render the resolved autocomplete value");
for (const marker of ["data-lpignore", "data-1p-ignore", "data-bwignore"]) {
  assert.ok(input.includes(marker), `shared Input must mark non-login fields for password-manager ignore: ${marker}`);
}

assert.ok(appShell.includes("MutationObserver"), "authenticated shell must cover dynamically mounted/portal inputs");
assert.ok(appShell.includes('querySelectorAll("input, textarea")'), "authenticated shell must harden direct Chakra inputs and textareas");
assert.ok(appShell.includes('element.setAttribute("autocomplete", autocomplete)'), "authenticated shell must set autocomplete suppression");
for (const marker of ["data-lpignore", "data-1p-ignore", "data-bwignore"]) {
  assert.ok(appShell.includes(marker), `authenticated shell must mark portal/direct inputs for password-manager ignore: ${marker}`);
}

assert.ok(login.includes('autoComplete="username"'), "Login username must retain browser/password-manager autofill");
assert.ok(login.includes('autoComplete="current-password"'), "Login password must retain browser/password-manager autofill");

console.log("authenticated autofill contract: assertions passed");
