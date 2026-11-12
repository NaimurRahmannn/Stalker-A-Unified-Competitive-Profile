/* eslint-disable @typescript-eslint/no-require-imports -- Node loads the feature's TypeScript modules. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const test = require("node:test");
const ts = require("typescript");
const { JSDOM } = require("jsdom");

for (const extension of [".ts", ".tsx"]) require.extensions[extension] = (module, filename) => {
  const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  }, fileName: filename });
  module._compile(compiled.outputText, filename);
};
const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>", { url: "http://localhost/" });
for (const name of ["window", "document", "navigator", "HTMLElement", "Event", "MouseEvent", "KeyboardEvent", "MutationObserver"]) {
  Object.defineProperty(global, name, { configurable: true, value: dom.window[name] });
}
global.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { renderToStaticMarkup } = require("react-dom/server");

const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
let accounts = [];
let overview;
let ability = { collection_enabled: false, provider_available: false, can_request_sync: false, reason: "provider_disabled" };
let run = { status: "not_started", run_id: null, username: "example_user" };
let overviewRequest = () => Promise.resolve(overview);
let statusRequest = () => Promise.resolve(run);
let syncRequest = () => Promise.resolve({ run_id: 4, status: "queued", username: "example_user", deduplicated: false, queued_at: "2026-01-01T00:00:00Z" });
const calls = [];
const messages = [];
const owner = { id: 1, username: "owner" };
let auth = { user: owner, isLoading: false };
let route = null;
let releaseConnect;
const dashboardRouter = { replace: (value) => { route = value; } };
const mockLogout = () => { auth = { user: null, isLoading: false }; };
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/navigation") return { useRouter: () => dashboardRouter };
  if (request === "next/image") return { default: ({ src, alt, ...props }) => React.createElement("img", { src, alt, ...props }) };
  if (request === "next/link") return { default: ({ href, children, ...props }) => React.createElement("a", { href, ...props }, children) };
  if (request === "@/hooks/use-auth") return { useAuth: () => ({ ...auth, logout: mockLogout }) };
  if (request === "@/components/layout/dashboard-sidebar") return { DashboardSidebar: ({ activeItem }) => React.createElement("nav", { "data-sidebar-active": activeItem }) };
  if (request === "@/components/layout/dashboard-mobile-nav") return { DashboardMobileNav: ({ activeItem }) => React.createElement("nav", { "data-mobile-active": activeItem }) };
  if (request === "sonner") return { toast: { success: (value) => messages.push(["success", value]), info: (value) => messages.push(["info", value]), error: (value) => messages.push(["error", value]) } };
  if (request === "@/features/platforms/api") return {
    listPlatformAccounts: async () => { calls.push("list"); return [...accounts]; },
    connectPlatformAccount: async ({ platform, handle }) => { calls.push(["connect", platform, handle]); if (handle === "invalid_name") throw new (require("axios").AxiosError)("invalid", "ERR_BAD_REQUEST", {}, {}, { status: 400, data: { handle: ["Invalid Kaggle username."] } }); if (handle === "pending_name") return new Promise((resolve) => { releaseConnect = () => { const item = account(handle); accounts = [item]; overview = emptyOverview(handle); resolve(item); }; }); const item = account(handle); accounts = [item]; overview = emptyOverview(handle); return item; },
    updatePlatformAccount: async (id, handle) => { calls.push(["update", id, handle]); const item = account(handle); accounts = [item]; overview = emptyOverview(handle); return item; },
    deletePlatformAccount: async (id) => { calls.push(["delete", id]); accounts = []; overview = emptyOverview(null); },
  };
  if (request === "../api" && parent?.filename.endsWith("datathon-page-content.tsx")) return {
    getKaggleCapabilities: async () => ability,
    getKaggleOverview: () => { calls.push("overview"); return overviewRequest(); },
    getKaggleSyncStatus: () => { calls.push("status"); return statusRequest(); },
    requestKaggleSync: () => { calls.push("sync"); return syncRequest(); },
  };
  return originalLoad.call(this, request, parent, ...rest);
};

const { formatRank, formatNumber, formatPoints, formatTier } = require("../src/features/datathons/formatters.ts");
const { KaggleTrackCard } = require("../src/features/datathons/components/kaggle-track-card.tsx");
const { DatathonPageContent, KaggleRunPanel, syncErrorMessage } = require("../src/features/datathons/components/datathon-page-content.tsx");

function account(handle = "example_user") { return { id: 7, platform: "kaggle", handle, profile_url: `https://www.kaggle.com/${handle}` }; }
function track(values = {}) { return { rank_status: "unknown", global_rank: null, highest_rank: null, tier: null, points: null, gold_medals: null, silver_medals: null, bronze_medals: null, source: null, data_collected_at: null, ...values }; }
function emptyOverview(handle) { return { linked: !!handle, username: handle, profile_url: handle ? `https://www.kaggle.com/${handle}` : null, collection_status: "not_collected", last_attempted_at: null, last_successful_at: null, tracks: { competitions: track(), code: track(), datasets: track() } }; }
function reset() {
  document.body.innerHTML = "<div id='root'></div>";
  accounts = []; overview = emptyOverview(null); ability = { collection_enabled: false, provider_available: false, can_request_sync: false, reason: "provider_disabled" };
  run = { status: "not_started", run_id: null, username: "example_user" }; overviewRequest = () => Promise.resolve(overview); statusRequest = () => Promise.resolve(run); syncRequest = () => Promise.resolve({ run_id: 4, status: "queued", username: "example_user", deduplicated: false, queued_at: "2026-01-01T00:00:00Z" });
  calls.length = 0; messages.length = 0; auth = { user: owner, isLoading: false }; route = null; releaseConnect = undefined; window.confirm = () => true;
}
async function mount() { const root = createRoot(document.getElementById("root")); await act(async () => root.render(React.createElement(DatathonPageContent))); await settle(); return root; }
async function settle() { await act(async () => new Promise((resolve) => setTimeout(resolve, 5))); }
async function click(label) { const node = [...document.querySelectorAll("button")].find((item) => item.textContent.includes(label)); assert.ok(node, label); await act(async () => node.dispatchEvent(new MouseEvent("click", { bubbles: true }))); }
async function type(value) { const node = document.getElementById("kaggle-handle"); await act(async () => { Object.getOwnPropertyDescriptor(node.constructor.prototype, "value").set.call(node, value); node.dispatchEvent(new Event("input", { bubbles: true })); node.dispatchEvent(new Event("change", { bubbles: true })); }); }
async function submit() { const form = document.querySelector("form"); await act(async () => form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }))); await settle(); }

test("rank and medal formatters preserve unknown, unranked, and known zero", () => {
  assert.equal(formatRank(1250, "ranked", true), "#1,250");
  assert.equal(formatRank(null, "unranked", true), "Unranked");
  assert.equal(formatRank(null, "unknown", true), "Not available");
  assert.equal(formatRank(null, "unknown", false), "Not collected");
  assert.equal(formatNumber(0), "0");
  assert.equal(formatNumber(null), "Not available");
  assert.equal(formatPoints("1234.2500"), "1,234.25");
  assert.equal(formatTier("grandmaster"), "Grandmaster");
});

test("three track cards show independent ranks, highest rank, points, tiers, and medals", () => {
  const rows = [track({ rank_status: "ranked", global_rank: 1250, highest_rank: 800, tier: "expert", points: "1200.5000", gold_medals: 0, silver_medals: 2, bronze_medals: null }), track({ rank_status: "unranked", gold_medals: 0 }), track()];
  const html = renderToStaticMarkup(React.createElement("div", null, ...["competitions", "code", "datasets"].map((name, index) => React.createElement(KaggleTrackCard, { key: name, track: name, statistics: rows[index], collected: true }))));
  for (const label of ["Competitions", "Code", "Datasets", "#1,250", "#800", "Expert", "1,200.5", "Unranked", "Not available", "Medals in this track"]) assert.match(html, new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(html, />0<\/p>/);
  assert.match(html, />—<\/p>/);
});

test("run panel distinguishes disabled, queued, running, retrying, success, failure, and cancellation", () => {
  const statuses = { queued: "Waiting for collection worker", running: "Collecting profile statistics", retrying: "A retry is scheduled", succeeded: "Statistics collection completed", failed: "Collection failed", cancelled: "Collection was cancelled" };
  for (const [status, text] of Object.entries(statuses)) {
    const html = renderToStaticMarkup(React.createElement(KaggleRunPanel, { capabilities: { can_request_sync: true }, run: { status, run_id: 1, username: "example_user" }, account: account(), syncing: false, pollError: null, onSync: () => {} }));
    assert.match(html, new RegExp(text));
    if (["queued", "running", "retrying"].includes(status)) assert.match(html, /disabled=""/);
  }
  const disabled = renderToStaticMarkup(React.createElement(KaggleRunPanel, { capabilities: ability, run: null, account: account(), syncing: false, pollError: null, onSync: () => {} }));
  assert.match(disabled, /synchronization is not available yet/);
  assert.doesNotMatch(disabled, /Sync Kaggle Statistics/);
});

test("unlinked page renders connection form, active navigation, and working tabs", async () => {
  reset(); const root = await mount();
  assert.equal(document.querySelector("[data-sidebar-active]").getAttribute("data-sidebar-active"), "datathon");
  assert.equal(document.querySelector("[data-mobile-active]").getAttribute("data-mobile-active"), "datathon");
  assert.match(document.body.textContent, /Connect your Kaggle username/);
  assert.equal(document.querySelector("#datathon-tab-overview").getAttribute("aria-selected"), "true");
  await click("Kaggle");
  assert.equal(document.querySelector("#datathon-tab-kaggle").getAttribute("aria-selected"), "true");
  await act(async () => root.unmount());
  assert.match(fs.readFileSync(path.join(__dirname, "../src/components/layout/dashboard-sidebar.tsx"), "utf8"), /id: "datathon",[\s\S]*?href: "\/datathon"/);
});

test("unauthenticated users are redirected after auth loading", async () => {
  reset(); auth = { user: null, isLoading: false };
  const root = await mount();
  assert.equal(route, "/login");
  assert.equal(calls.length, 0);
  await act(async () => root.unmount());
});

test("empty username is rejected and backend validation errors are shown", async () => {
  reset(); const root = await mount();
  await submit();
  assert.match(document.body.textContent, /Handle is required/);
  assert.equal(calls.filter((item) => Array.isArray(item) && item[0] === "connect").length, 0);
  await type("invalid_name"); await submit();
  assert.match(document.body.textContent, /Invalid Kaggle username/);
  assert.equal(accounts.length, 0);
  await act(async () => root.unmount());
});

test("duplicate form submissions create only one account request", async () => {
  reset(); const root = await mount();
  await type("pending_name");
  const form = document.querySelector("form");
  await act(async () => { form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })); form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })); });
  assert.equal(calls.filter((item) => Array.isArray(item) && item[0] === "connect").length, 1);
  await act(async () => releaseConnect()); await settle();
  await act(async () => root.unmount());
});

test("an auth identity change hides the previous user's cached rankings", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user"); overview.last_successful_at = "2026-01-01T00:00:00Z"; overview.tracks.competitions = track({ rank_status: "ranked", global_rank: 999 });
  const root = await mount(); assert.match(document.body.textContent, /#999/);
  auth = { user: { id: 2, username: "other" }, isLoading: false }; accounts = []; overview = emptyOverview(null);
  await act(async () => root.render(React.createElement(DatathonPageContent)));
  assert.doesNotMatch(document.body.textContent, /#999|@example_user/);
  await settle();
  assert.match(document.body.textContent, /Connect your Kaggle username/);
  await act(async () => root.unmount());
});

test("an expired API session redirects to login instead of presenting cached account data", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user");
  const { AxiosError } = require("axios");
  overviewRequest = async () => { throw new AxiosError("unauthorized", "ERR_BAD_RESPONSE", {}, {}, { status: 401, data: { detail: "expired" } }); };
  const root = await mount();
  assert.equal(route, "/login");
  assert.equal(auth.user, null);
  await act(async () => root.unmount());
});

test("connect trims username, change clears previous rankings, and unlink returns to empty state", async () => {
  reset(); const root = await mount();
  await type("  example_user  "); await submit();
  assert.deepEqual(calls.find((item) => Array.isArray(item) && item[0] === "connect"), ["connect", "kaggle", "example_user"]);
  assert.match(document.body.textContent, /@example_user/);
  assert.match(document.body.textContent, /Ownership not verified/);
  await type("second_user"); await submit();
  assert.deepEqual(calls.find((item) => Array.isArray(item) && item[0] === "update"), ["update", 7, "second_user"]);
  assert.doesNotMatch(document.body.textContent, /@example_user/);
  await click("Disconnect Kaggle account"); await settle();
  assert.deepEqual(calls.find((item) => Array.isArray(item) && item[0] === "delete"), ["delete", 7]);
  assert.match(document.body.textContent, /Connect your Kaggle username/);
  await act(async () => root.unmount());
});

test("cached partial rankings survive failed collection and tabs do not refetch", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user");
  overview.collection_status = "failed"; overview.last_successful_at = "2026-01-02T00:00:00Z";
  overview.tracks.competitions = track({ rank_status: "ranked", global_rank: 1200, tier: "master" });
  const root = await mount();
  assert.match(document.body.textContent, /#1,200/);
  assert.match(document.body.textContent, /latest collection attempt failed/);
  const before = calls.filter((item) => item === "overview").length;
  await click("Kaggle");
  assert.match(document.body.textContent, /Competitions/);
  assert.match(document.body.textContent, /Code/);
  assert.match(document.body.textContent, /Datasets/);
  assert.equal(calls.filter((item) => item === "overview").length, before, JSON.stringify(calls));
  await act(async () => root.unmount());
});

test("sync 202 stays queued and a later status success refreshes cached data", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user"); ability = { collection_enabled: true, provider_available: true, can_request_sync: true, reason: null };
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
  const originalTimeout = window.setTimeout;
  window.setTimeout = (callback, delay, ...args) => originalTimeout(callback, delay === 5000 ? 2 : delay, ...args);
  let polls = 0; syncRequest = async () => { statusRequest = async () => { polls++; return polls < 2 ? { run_id: 4, status: "running", username: "example_user" } : { run_id: 4, status: "succeeded", username: "example_user" }; }; return { run_id: 4, status: "queued", username: "example_user", deduplicated: false, queued_at: "2026-01-01T00:00:00Z" }; };
  const root = await mount(); await click("Kaggle"); await click("Sync Kaggle Statistics"); await settle();
  assert.ok(messages.some(([kind, value]) => kind === "info" && /queued/.test(value)), JSON.stringify({ messages, calls, content: document.body.textContent }));
  assert.ok(!messages.some(([kind]) => kind === "success"));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 30)));
  assert.match(document.body.textContent, /Statistics collection completed/);
  assert.equal(polls, 2);
  await act(async () => root.unmount()); window.setTimeout = originalTimeout;
});

test("polling keeps one status request in flight and stops after unmount", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user"); ability = { collection_enabled: true, provider_available: true, can_request_sync: true, reason: null };
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
  const originalTimeout = window.setTimeout;
  window.setTimeout = (callback, delay, ...args) => originalTimeout(callback, delay === 5000 ? 2 : delay, ...args);
  let releaseStatus;
  let polls = 0;
  syncRequest = async () => {
    statusRequest = () => { polls++; return new Promise((resolve) => { releaseStatus = resolve; }); };
    return { run_id: 5, status: "queued", username: "example_user", deduplicated: false, queued_at: "2026-01-01T00:00:00Z" };
  };
  const root = await mount(); await click("Kaggle"); await click("Sync Kaggle Statistics");
  await act(async () => new Promise((resolve) => setTimeout(resolve, 25)));
  assert.equal(polls, 1);
  await act(async () => root.unmount());
  await act(async () => releaseStatus({ run_id: 5, status: "succeeded", username: "example_user" }));
  await new Promise((resolve) => setTimeout(resolve, 15));
  assert.equal(polls, 1);
  window.setTimeout = originalTimeout;
});

test("changing the linked username ignores a previous run's late poll response", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user"); ability = { collection_enabled: true, provider_available: true, can_request_sync: true, reason: null };
  Object.defineProperty(document, "hidden", { configurable: true, value: false });
  const originalTimeout = window.setTimeout;
  window.setTimeout = (callback, delay, ...args) => originalTimeout(callback, delay === 5000 ? 2 : delay, ...args);
  let releaseOldStatus;
  syncRequest = async () => {
    statusRequest = () => new Promise((resolve) => { releaseOldStatus = resolve; });
    return { run_id: 9, status: "queued", username: "example_user", deduplicated: false, queued_at: "2026-01-01T00:00:00Z" };
  };
  const root = await mount(); await click("Kaggle"); await click("Sync Kaggle Statistics");
  await act(async () => new Promise((resolve) => setTimeout(resolve, 20)));
  assert.equal(typeof releaseOldStatus, "function");
  statusRequest = async () => ({ status: "not_started", run_id: null, username: "second_user" });
  await type("second_user"); await submit();
  await act(async () => releaseOldStatus({ status: "succeeded", run_id: 9, username: "example_user" }));
  assert.match(document.body.textContent, /@second_user/);
  assert.doesNotMatch(document.body.textContent, /Statistics collection completed/);
  await act(async () => root.unmount()); window.setTimeout = originalTimeout;
});

test("late overview response cannot restore an account after unlink", async () => {
  reset(); accounts = [account()]; overview = emptyOverview("example_user");
  statusRequest = async () => { throw new Error("status unavailable"); };
  const root = await mount();
  let resolveLate;
  overviewRequest = () => new Promise((resolve) => { resolveLate = resolve; });
  statusRequest = async () => run;
  await click("Retry"); await settle();
  assert.equal(typeof resolveLate, "function");
  await click("Disconnect Kaggle account"); await settle();
  await act(async () => resolveLate({ ...emptyOverview("example_user"), last_successful_at: "2026-01-02T00:00:00Z" }));
  assert.doesNotMatch(document.body.textContent, /@example_user/);
  await act(async () => root.unmount());
});

test("sync errors are safe and cooldown is specific", () => {
  const { AxiosError } = require("axios");
  const error = (status, data) => new AxiosError("request failed", "ERR_BAD_RESPONSE", {}, {}, { status, data });
  assert.match(syncErrorMessage(error(429, { retry_after_seconds: 17 })), /17 seconds/);
  assert.match(syncErrorMessage(error(503, { detail: "secret stack trace" })), /unavailable/);
  assert.doesNotMatch(syncErrorMessage(error(503, { detail: "secret stack trace" })), /secret/);
});
