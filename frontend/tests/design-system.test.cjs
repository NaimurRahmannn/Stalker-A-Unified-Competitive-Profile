/* eslint-disable @typescript-eslint/no-require-imports -- Node loads the shared TypeScript components. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const { JSDOM } = require("jsdom");
const ts = require("typescript");

for (const extension of [".ts", ".tsx"]) require.extensions[extension] = (module, filename) => {
  const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  }, fileName: filename });
  module._compile(compiled.outputText, filename);
};

const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>");
for (const name of ["window", "document", "HTMLElement", "Event", "MouseEvent"]) {
  Object.defineProperty(global, name, { configurable: true, value: dom.window[name] });
}
global.IS_REACT_ACT_ENVIRONMENT = true;
const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { Button } = require("../src/components/ui/button.tsx");
const { Card } = require("../src/components/ui/card.tsx");
const { StatusBadge } = require("../src/components/ui/status-badge.tsx");

test("shared buttons expose variants and block interaction while loading", async () => {
  const root = createRoot(document.getElementById("root"));
  let clicks = 0;
  await act(async () => root.render(React.createElement(Button, { variant: "destructive", loading: true, onClick: () => clicks++ }, "Delete")));
  const button = document.querySelector("button");
  assert.match(button.className, /ui-button-destructive/);
  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute("aria-busy"), "true");
  button.click();
  assert.equal(clicks, 0);
  await act(async () => root.render(React.createElement(Button, { variant: "secondary", onClick: () => clicks++ }, "Retry")));
  assert.equal(button.disabled, false);
  assert.equal(button.hasAttribute("aria-busy"), false);
  button.click();
  assert.equal(clicks, 1);
  await act(async () => root.unmount());
});

test("shared cards and status badges keep their selected visual roles", async () => {
  const root = createRoot(document.getElementById("root"));
  await act(async () => root.render(React.createElement(Card, { variant: "subtle" }, React.createElement(StatusBadge, { tone: "warning" }, "Not verified"))));
  assert.match(document.querySelector(".ui-card").className, /ui-card-subtle/);
  assert.equal(document.querySelector(".ui-badge-warning").textContent, "Not verified");
  await act(async () => root.unmount());
});
