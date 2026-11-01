/* eslint-disable @typescript-eslint/no-require-imports -- Node's CJS test runner loads the actual TSX component. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const test = require("node:test");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) {
  require.extensions[extension] = (module, filename) => {
    const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
      fileName: filename,
    });
    module._compile(compiled.outputText, filename);
  };
}

const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "http://localhost/" });
for (const name of ["window", "document", "navigator", "HTMLElement", "HTMLInputElement", "File", "FileList", "MutationObserver", "Event", "MouseEvent"]) {
  Object.defineProperty(global, name, { configurable: true, value: dom.window[name] });
}
global.IS_REACT_ACT_ENVIRONMENT = true;

const state = { account: null, preview: null, applied: null, history: [], errors: {}, calls: [], refreshes: 0 };
const account = (handle = "example_user") => ({ id: 7, platform: "devpost", handle, profile_url: `https://devpost.com/${handle}`, ownership_verified: false });
const page = (number) => ({ count: state.history.length, results: state.history.slice((number - 1) * 1, number), previous: number > 1 ? "previous" : null, next: number < state.history.length ? "next" : null });
const invoke = async (name, ...args) => {
  state.calls.push([name, ...args]);
  if (state.errors[name]) throw state.errors[name];
  if (name === "listPlatformAccounts") return state.account ? [state.account] : [];
  if (name === "connectPlatformAccount") { state.account = account(args[0].handle); return state.account; }
  if (name === "updatePlatformAccount") { state.account = account(args[1]); return state.account; }
  if (name === "deletePlatformAccount") { state.account = null; return; }
  if (name === "devpostHistory") return page(args[0]);
  if (name === "previewDevpost") return state.preview;
  if (name === "applyDevpost") return state.applied;
};
const platformApi = Object.fromEntries(["listPlatformAccounts", "connectPlatformAccount", "updatePlatformAccount", "deletePlatformAccount"].map((name) => [name, (...args) => invoke(name, ...args)]));
const hackathonApi = Object.fromEntries(["devpostHistory", "previewDevpost", "applyDevpost"].map((name) => [name, (...args) => invoke(name, ...args)]));
const originalLoad = Module._load;
const originalResolve = Module._resolveFilename;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "@/features/platforms/api") return platformApi;
  if (request === "../api" && parent?.filename.endsWith("devpost-integration.tsx")) return { hackathonApi };
  if (request === "sonner") return { toast: { success: () => {} } };
  return originalLoad.call(this, request, parent, ...rest);
};

const React = require("react");
const { AxiosError } = require("axios");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { DevpostIntegration } = require("../src/features/hackathons/components/devpost-integration.tsx");
const { exampleDocument, hasExamplePlaceholders, DEVPOST_REQUEST_LIMIT } = require("../src/features/hackathons/devpost-example.ts");

function resetState() {
  Object.assign(state, { account: account(), preview: null, applied: null, history: [], errors: {}, calls: [], refreshes: 0 });
  document.body.innerHTML = "<div id='root'></div>";
  window.confirm = () => true;
}
async function render() {
  const root = createRoot(document.getElementById("root"));
  await act(async () => { root.render(React.createElement(DevpostIntegration, { onImported: async () => { state.refreshes++; } })); });
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 5)); });
  return root;
}
async function click(label) {
  const button = [...document.querySelectorAll("button")].find((node) => node.textContent.includes(label));
  assert.ok(button, `Missing button: ${label}`);
  await act(async () => { button.dispatchEvent(new MouseEvent("click", { bubbles: true })); });
  return button;
}
async function type(node, value) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(node.constructor.prototype, "value").set.call(node, value);
    node.dispatchEvent(new Event("input", { bubbles: true }));
    node.dispatchEvent(new Event("change", { bubbles: true }));
  });
}
function validDocument() {
  const value = exampleDocument("example_user");
  value.projects[0].project_url = "https://devpost.com/software/my-real-project";
  value.projects[0].title = "My Real Project";
  value.projects[0].description = "My project description";
  value.projects[0].repository_url = "https://github.com/me/my-real-project";
  value.projects[0].technologies = ["Python"];
  value.projects[0].submissions[0].hackathon_name = "My Hackathon";
  value.projects[0].submissions[0].hackathon_url = "https://my-hackathon.devpost.com/";
  return value;
}
function preview() {
  return { preview_token: "signed-token", projects_detected: 1, hackathons_detected: 1, participations_detected: 1, submissions_detected: 1,
    new_records: 4, existing_matches: 0, protected_records: 0, potential_manual_duplicates: 0, conflicts: [],
    projects: [{ project_url: "https://devpost.com/software/my-real-project", title: "My Real Project", action: "create", possible_manual_project_ids: [],
      submissions: [{ event_url: "https://my-hackathon.devpost.com/", event_name: "My Hackathon", event_action: "create", participation_action: "create", action: "create", possible_manual_event_ids: [] }] }] };
}
function apiError(status, detail) {
  const error = new AxiosError(`HTTP ${status}`);
  error.response = { status, data: { detail } };
  return error;
}

test("schema example is visibly fake and cannot be previewed unchanged", async () => {
  resetState(); const root = await render();
  assert.equal(hasExamplePlaceholders(exampleDocument("example_user")), true);
  assert.equal(hasExamplePlaceholders(JSON.parse(fs.readFileSync(path.join(__dirname, "../../examples/devpost_import_v1.json"), "utf8"))), true);
  assert.match(document.body.textContent, /demonstration data/i);
  await click("Load schema example");
  await click("Preview import");
  assert.match(document.querySelector("[role=alert]").textContent, /Replace every example/i);
  assert.equal(state.calls.some(([name]) => name === "previewDevpost"), false);
  await act(async () => root.unmount());
});

test("link, change, and unlink preserve confirmations", async () => {
  resetState(); state.account = null; const root = await render();
  assert.ok(document.body.textContent.includes("Link profile"));
  await type(document.getElementById("devpost-reference"), "example_user");
  await click("Link profile");
  assert.equal(state.account.handle, "example_user");
  await type(document.getElementById("devpost-reference"), "new_user");
  await click("Change profile");
  assert.equal(state.account.handle, "new_user");
  await click("Unlink");
  assert.equal(state.account, null);
  await act(async () => root.unmount());
});

test("file selection, preview, confirmation, apply, refresh, and paged history", async () => {
  resetState(); state.preview = preview(); state.applied = { id: 9, created_count: 4, updated_count: 0, skipped_count: 0, result: { events_created: 1, participations_created: 1, submissions_created: 1 } };
  state.history = [{ id: 9, status: "completed", profile_handle: "example_user", started_at: "2026-01-01T00:00:00Z", projects_processed: 1, created_count: 4, updated_count: 0, skipped_count: 0, error_count: 0, result: {} },
    { id: 8, status: "completed", profile_handle: "example_user", started_at: "2026-01-02T00:00:00Z", projects_processed: 1, created_count: 1, updated_count: 0, skipped_count: 0, error_count: 0, result: {} }];
  const root = await render();
  const fileInput = document.querySelector('input[type="file"]');
  Object.defineProperty(fileInput, "files", { configurable: true, value: [{ size: 100, text: async () => JSON.stringify(validDocument()) }] });
  await act(async () => { fileInput.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.match(document.getElementById("devpost-json").value, /My Real Project/);
  await click("Preview import");
  assert.match(document.body.textContent, /4 new/);
  const confirmButton = [...document.querySelectorAll("button")].find((node) => node.textContent.includes("Confirm import"));
  assert.equal(confirmButton.disabled, true);
  await act(async () => { const checkbox = document.querySelector('input[type="checkbox"]'); checkbox.click(); });
  assert.equal(confirmButton.disabled, false);
  await click("Confirm import");
  assert.equal(state.refreshes, 1);
  assert.match(document.body.textContent, /Import completed/);
  await click("Next");
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 5)); });
  assert.match(document.body.textContent, /Page 2/);
  assert.equal(state.calls.filter(([name]) => name === "applyDevpost").length, 1);
  await act(async () => root.unmount());
});

test("invalid JSON, oversized files, failed preview, and failed apply show errors", async () => {
  resetState(); state.preview = preview(); const root = await render();
  const input = document.getElementById("devpost-json");
  await type(input, "{broken"); await click("Preview import");
  assert.match(document.querySelector("[role=alert]").textContent, /valid JSON/i);
  await type(input, JSON.stringify({ ...validDocument(), format_version: 2 })); await click("Preview import");
  assert.ok(document.querySelector("[role=alert]"));
  const fileInput = document.querySelector('input[type="file"]');
  Object.defineProperty(fileInput, "files", { configurable: true, value: [{ size: DEVPOST_REQUEST_LIMIT + 1, text: async () => "" }] });
  await act(async () => { fileInput.dispatchEvent(new Event("change", { bubbles: true })); });
  assert.match(document.querySelector("[role=alert]").textContent, /formatting allowance/i);
  for (const status of [403, 409, 413, 500]) {
    state.errors.previewDevpost = apiError(status, `Preview error ${status}`);
    await type(input, JSON.stringify(validDocument())); await click("Preview import");
    assert.match(document.querySelector("[role=alert]").textContent, new RegExp(String(status)));
  }
  delete state.errors.previewDevpost;
  await click("Preview import");
  for (const status of [403, 409, 413, 500]) {
    state.errors.applyDevpost = apiError(status, `Apply error ${status}`);
    await act(async () => document.querySelector('input[type="checkbox"]').click());
    await click("Confirm import");
    assert.match(document.querySelector("[role=alert]").textContent, new RegExp(String(status)));
    assert.equal(document.body.textContent.includes("Confirm import"), false);
    if (status !== 500) await click("Preview import");
  }
  await act(async () => root.unmount());
});

test("loading controls block repeated preview and apply requests", async () => {
  resetState();
  const root = createRoot(document.getElementById("root"));
  act(() => { root.render(React.createElement(DevpostIntegration, { onImported: async () => { state.refreshes++; } })); });
  assert.match(document.querySelector('[role="status"]').textContent, /Loading Devpost integration/);
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 5)); });
  let resolvePreview;
  state.preview = new Promise((resolve) => { resolvePreview = resolve; });
  await type(document.getElementById("devpost-json"), JSON.stringify(validDocument()));
  await click("Preview import");
  const working = [...document.querySelectorAll("button")].find((button) => button.textContent.includes("Working"));
  assert.equal(working.disabled, true);
  await click("Working");
  assert.equal(state.calls.filter(([name]) => name === "previewDevpost").length, 1);
  await act(async () => { resolvePreview(preview()); });
  await act(async () => { await Promise.resolve(); });
  await act(async () => document.querySelector('input[type="checkbox"]').click());
  let resolveApply;
  state.applied = new Promise((resolve) => { resolveApply = resolve; });
  await click("Confirm import");
  const confirm = [...document.querySelectorAll("button")].find((button) => button.textContent.includes("Confirm import"));
  assert.equal(confirm.disabled, true);
  await click("Confirm import");
  assert.equal(state.calls.filter(([name]) => name === "applyDevpost").length, 1);
  await act(async () => { resolveApply({ id: 1, created_count: 4, updated_count: 0, skipped_count: 0, result: {} }); });
  await act(async () => { await Promise.resolve(); });
  assert.equal(state.refreshes, 1);
  await act(async () => root.unmount());
});
