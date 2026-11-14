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

let fetchEvents = () => Promise.resolve({ status: "ready", events: [], source: "CLIST", updated_at: "2026-11-14T00:00:00Z" });
const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/image") return { default: ({ src, alt, ...props }) => React.createElement("img", { src, alt, ...props }) };
  if (request === "../api" && parent?.filename.endsWith("clist-events-card.tsx")) return { getDashboardEvents: () => fetchEvents() };
  return originalLoad.call(this, request, parent, ...rest);
};

const { RightWidgetsPanel } = require("../src/features/dashboard/components/right-widgets-panel.tsx");

async function mount() {
  document.body.innerHTML = "<div id='root'></div>";
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(RightWidgetsPanel)));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  return root;
}

test("right sidebar shows CLIST contests and preserves streak and image cards", async () => {
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", events: [
    { id: 4, title: "Weekend Challenge", platform: "example.org", start: "2026-11-15T10:00:00Z", end: "2026-11-15T12:00:00Z", url: "https://example.org/contest", ongoing: false },
  ] });
  const root = await mount();
  assert.match(document.body.textContent, /Live & upcoming contests/);
  assert.match(document.body.textContent, /Weekend Challenge/);
  assert.match(document.body.textContent, /Streak Summary/);
  assert.doesNotMatch(document.body.textContent, /Profile Completion|Next Steps/);
  assert.equal(document.querySelector("a[href='https://example.org/contest']").getAttribute("rel"), "noopener noreferrer");
  assert.ok(document.querySelector("img[src='/images/stalker_right_bg.png']"));
  await act(async () => root.unmount());
});

test("CLIST failure offers retry without hiding the other cards", async () => {
  fetchEvents = () => Promise.reject(new Error("provider offline"));
  const root = await mount();
  assert.match(document.body.textContent, /Contests are unavailable right now/);
  assert.match(document.body.textContent, /Streak Summary/);
  fetchEvents = () => Promise.resolve({ status: "ready", source: "CLIST", updated_at: "2026-11-14T00:00:00Z", events: [] });
  const retry = [...document.querySelectorAll("button")].find((button) => button.textContent === "Try again");
  assert.ok(retry);
  await act(async () => retry.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.match(document.body.textContent, /No upcoming contests found/);
  await act(async () => root.unmount());
});
