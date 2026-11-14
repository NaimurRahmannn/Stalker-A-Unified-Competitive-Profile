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
for (const name of ["window", "document", "navigator", "HTMLElement", "Event", "MouseEvent", "MutationObserver"]) {
  Object.defineProperty(global, name, { configurable: true, value: dom.window[name] });
}
global.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { renderToStaticMarkup } = require("react-dom/server");

let fetchEvents = () => Promise.resolve({ status: "ready", events: [], source: "CLIST", updated_at: "2026-11-14T00:00:00Z", next_page: null });
let currentUser = { id: 1, username: "viewer", full_name: "Contest Viewer", avatar: null };
let redirectPath = null;
const mockRouter = { replace: (path) => { redirectPath = path; } };
const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/image") return { default: ({ src, alt }) => React.createElement("img", { src, alt }) };
  if (request === "next/link") return { default: ({ href, children, ...props }) => React.createElement("a", { href, ...props }, children) };
  if (request === "next/navigation") return { useRouter: () => mockRouter };
  if (request === "@/hooks/use-auth") return { useAuth: () => ({ user: currentUser, isLoading: false }) };
  if (request === "../api" && ["clist-events-card.tsx", "contests-page-content.tsx"].some((name) => parent?.filename.endsWith(name))) return { getDashboardEvents: (page) => fetchEvents(page) };
  return originalLoad.call(this, request, parent, ...rest);
};

const { RightWidgetsPanel } = require("../src/features/dashboard/components/right-widgets-panel.tsx");
const { ContestsPageContent } = require("../src/features/dashboard/components/contests-page-content.tsx");
const { DashboardSidebar } = require("../src/components/layout/dashboard-sidebar.tsx");

async function mount() {
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(RightWidgetsPanel)));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  return root;
}

test("right sidebar shows CLIST contests and preserves streak and image cards", async () => {
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", next_page: null, events: [
    { id: 4, title: "Weekend Challenge", platform: "example.org", start: "2026-11-15T10:00:00Z", end: "2026-11-15T12:00:00Z", url: "https://example.org/contest", ongoing: false },
  ] });
  const root = await mount();
  assert.match(document.body.textContent, /Live & upcoming contests/);
  assert.match(document.body.textContent, /Weekend Challenge/);
  assert.match(document.body.textContent, /Streak Summary/);
  assert.doesNotMatch(document.body.textContent, /Profile Completion|Next Steps/);
  assert.equal(document.querySelector("a[href='https://example.org/contest']").getAttribute("rel"), "noopener noreferrer");
  assert.ok(document.querySelector("a[href='/contests']"));
  assert.equal(document.querySelector("a[href='https://clist.by/']"), null);
  assert.ok(document.querySelector("img[src='/images/stalker_right_bg.png']"));
  await act(async () => root.unmount());
});

test("CLIST failure offers retry without hiding the other cards", async () => {
  fetchEvents = () => Promise.reject(new Error("provider offline"));
  const root = await mount();
  assert.match(document.body.textContent, /Contests are unavailable right now/);
  assert.match(document.body.textContent, /Streak Summary/);
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", next_page: null, events: [] });
  const retry = [...document.querySelectorAll("button")].find((button) => button.textContent === "Try again");
  assert.ok(retry);
  await act(async () => retry.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.match(document.body.textContent, /No upcoming contests found/);
  await act(async () => root.unmount());
});

test("sidebar removes Activity and Goals and opens the local contest page", () => {
  const markup = renderToStaticMarkup(React.createElement(DashboardSidebar, { activeItem: "contests" }));
  assert.match(markup, /href="\/contests"/);
  assert.doesNotMatch(markup, />Activity<|>Goals</);
});

test("contest page loads more CLIST results without leaving STALKER", async () => {
  const requestedPages = [];
  const event = (id) => ({ id, title: `Contest ${id}`, platform: "example.org", start: new Date(Date.now() + 3600_000).toISOString(), end: new Date(Date.now() + 7200_000).toISOString(), url: `https://example.org/${id}`, ongoing: false });
  fetchEvents = (page) => {
    requestedPages.push(page);
    return Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", events: [event(page)], next_page: page === 1 ? 2 : null });
  };
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(ContestsPageContent)));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.deepEqual(requestedPages, [1]);
  assert.match(document.body.textContent, /Contest 1/);
  assert.match(document.body.textContent, /Start time/);
  assert.match(document.body.textContent, /Time left/);
  assert.match(document.body.textContent, /Duration/);
  const loadMore = [...document.querySelectorAll("button")].find((button) => button.textContent.includes("Load more contests"));
  assert.ok(loadMore);
  await act(async () => loadMore.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.deepEqual(requestedPages, [1, 2]);
  assert.match(document.body.textContent, /Contest 1/);
  assert.match(document.body.textContent, /Contest 2/);
  assert.equal([...document.querySelectorAll("button")].some((button) => button.textContent.includes("Load more contests")), false);
  assert.equal(document.querySelector("a[href='https://example.org/2']").getAttribute("rel"), "noopener noreferrer");
  await act(async () => root.unmount());
});

test("contest schedule filters loaded live and upcoming rows", async () => {
  const futureStart = new Date(Date.now() + 3600_000).toISOString();
  const futureEnd = new Date(Date.now() + 7200_000).toISOString();
  const liveStart = new Date(Date.now() - 3600_000).toISOString();
  const event = (id, title, platform, start, ongoing) => ({ id, title, platform, start, end: futureEnd, url: `https://example.org/${id}`, ongoing });
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: new Date().toISOString(), next_page: null, events: [
    event(1, "Live Challenge", "codeforces.com", liveStart, true),
    event(2, "Upcoming Round", "atcoder.jp", futureStart, false),
  ] });
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(ContestsPageContent)));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.equal(document.querySelectorAll("tbody tr").length, 2);
  const liveButton = [...document.querySelectorAll("button")].find((button) => button.textContent === "live");
  await act(async () => liveButton.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  assert.equal(document.querySelectorAll("tbody tr").length, 1);
  assert.match(document.querySelector("tbody").textContent, /Live Challenge/);
  assert.doesNotMatch(document.querySelector("tbody").textContent, /Upcoming Round/);
  const upcomingButton = [...document.querySelectorAll("button")].find((button) => button.textContent === "upcoming");
  await act(async () => upcomingButton.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  assert.match(document.querySelector("tbody").textContent, /Upcoming Round/);
  assert.doesNotMatch(document.querySelector("tbody").textContent, /Live Challenge/);
  await act(async () => root.unmount());
});

test("contest page retries after a provider error", async () => {
  fetchEvents = () => Promise.reject(new Error("provider offline"));
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(ContestsPageContent)));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.match(document.body.textContent, /Contests are unavailable right now/);
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", events: [], next_page: null });
  const retry = [...document.querySelectorAll("button")].find((button) => button.textContent === "Try again");
  await act(async () => retry.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.match(document.body.textContent, /No live or upcoming contests/);
  await act(async () => root.unmount());
});

test("contest page redirects signed-out users to login", async () => {
  currentUser = null;
  redirectPath = null;
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(ContestsPageContent)));
  assert.equal(redirectPath, "/login");
  await act(async () => root.unmount());
  currentUser = { id: 1, username: "viewer", full_name: "Contest Viewer", avatar: null };
});
