/* eslint-disable @typescript-eslint/no-require-imports -- Node loads the actual TSX components. */
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
for (const name of ["window", "document", "navigator", "HTMLElement", "Event", "MouseEvent", "MutationObserver"]) Object.defineProperty(global, name, { configurable: true, value: dom.window[name] });
global.IS_REACT_ACT_ENVIRONMENT = true;
const calls = [];
let portfolioResult;
let visibilityResult;
const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/link") return { default: function Link({ href, children, ...props }) { return require("react").createElement("a", { href, ...props }, children); } };
  if (request === "../../api" && parent?.filename.endsWith("public-hackathon-portfolio.tsx")) return { getPublicHackathonPortfolio: (...args) => { calls.push(["portfolio", ...args]); return portfolioResult(...args); } };
  if (request === "../api" && parent?.filename.endsWith("visibility-control.tsx")) return { hackathonApi: {
    projectVisibility: (...args) => { calls.push(["project", ...args]); return visibilityResult(...args); },
    participationVisibility: (...args) => { calls.push(["participation", ...args]); return visibilityResult(...args); },
  } };
  if (request === "sonner") return { toast: { success: () => {}, error: () => {} } };
  return originalLoad.call(this, request, parent, ...rest);
};
const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { renderToStaticMarkup } = require("react-dom/server");
const { VisibilityControl } = require("../src/features/hackathons/components/visibility-control.tsx");
const { PublicHackathonPortfolio, PublicHackathonPortfolioContent } = require("../src/features/profile/components/hackathons/public-hackathon-portfolio.tsx");

function portfolio() {
  const page = (results) => ({ count: results.length, results, next: null, previous: null });
  return {
    summary: { published_projects: 1, public_participations: 1, public_achievements: 2, verified_achievements: 1 },
    projects: page([{ id: 1, title: "Public project", description: "A useful project", technologies: ["Python"], source: "devpost", associations: [{ event_id: 3, event_name: "Public event", event_url: "https://public.devpost.com/" }], project_url: "https://devpost.com/software/public", repository_url: "https://github.com/me/public", demo_url: "https://example.com/demo", video_url: null, image_url: null }]),
    participations: page([{ id: 2, event: { id: 3, name: "Public event", organizer: "Organizer", start_date: "2026-01-01", end_date: null, format: "online", event_url: "https://public.devpost.com/" }, status: "submitted", team_name: "Team", role: "Builder" }]),
    achievements: page([{ id: 4, participation_id: 2, project_id: null, achievement_type: "award", title: "Community award", rank: null, total_participants: null, description: "", verification_status: "self_reported" }, { id: 5, participation_id: 2, project_id: 1, achievement_type: "placement", title: "First place", rank: 1, total_participants: 10, description: "", verification_status: "verified" }]),
    submissions: page([{ id: 6, project_id: 1, project_title: "Public project", event_id: 3, event_name: "Public event", submission_url: "https://example.com/submission" }]),
  };
}
function reset() { calls.length = 0; document.body.innerHTML = "<div id='root'></div>"; portfolioResult = async () => portfolio(); visibilityResult = async (id, isPublic) => ({ id, is_public: isPublic }); }
async function mount(element) { const root = createRoot(document.getElementById("root")); await act(async () => root.render(element)); return root; }
async function click(label) { const button = [...document.querySelectorAll("button")].find((item) => item.textContent.includes(label)); assert.ok(button, label); await act(async () => button.dispatchEvent(new MouseEvent("click", { bubbles: true }))); return button; }
const pages = { projects: 1, participations: 1, achievements: 1, submissions: 1 };

test("public cards show approved data, safe links, and accurate verification", () => {
  reset();
  const html = renderToStaticMarkup(React.createElement(PublicHackathonPortfolioContent, { portfolio: portfolio(), pages, username: "portfolio", onPage: () => {} }));
  for (const value of ["Published projects", "Public project", "Python", "Devpost project", "Repository", "Live demo", "Public event", "Team", "Community award", "Self-reported", "First place", "Verified", "Rank 1", "Submitted work"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes("Secret project"));
  assert.ok(html.includes('rel="noopener noreferrer"'));
  assert.ok(!html.includes("<img"));
});

test("empty and evidence-provided presentations are accurate", () => {
  reset(); const empty = portfolio();
  empty.summary = { published_projects: 0, public_participations: 0, public_achievements: 0, verified_achievements: 0 };
  for (const name of ["projects", "participations", "achievements", "submissions"]) empty[name] = { count: 0, results: [], next: null, previous: null };
  assert.match(renderToStaticMarkup(React.createElement(PublicHackathonPortfolioContent, { portfolio: empty, pages, username: "portfolio", onPage: () => {} })), /No Hackathon work has been published yet/);
  const evidence = portfolio(); evidence.achievements.results[0].verification_status = "evidence_provided";
  assert.match(renderToStaticMarkup(React.createElement(PublicHackathonPortfolioContent, { portfolio: evidence, pages, username: "portfolio", onPage: () => {} })), /Evidence provided/);
  const unsafe = portfolio(); unsafe.projects.results[0].project_url = "javascript:alert(1)";
  const unsafeHtml = renderToStaticMarkup(React.createElement(PublicHackathonPortfolioContent, { portfolio: unsafe, pages, username: "portfolio", onPage: () => {} }));
  assert.ok(!unsafeHtml.includes('href="javascript:'));
});

test("visibility controls wait for the server, prevent repeats, and show failures", async () => {
  reset(); let resolve;
  visibilityResult = () => new Promise((done) => { resolve = done; });
  let refreshed = 0;
  const root = await mount(React.createElement(VisibilityControl, { kind: "project", id: 11, isPublic: false, onSaved: async () => { refreshed++; } }));
  await click("Publish to profile");
  const saving = [...document.querySelectorAll("button")].find((item) => item.textContent.includes("Saving visibility"));
  assert.equal(saving.disabled, true);
  await click("Saving visibility");
  assert.equal(calls.filter(([name]) => name === "project").length, 1);
  await act(async () => resolve({ id: 11, is_public: true }));
  await act(async () => Promise.resolve());
  assert.equal(refreshed, 1);
  await act(async () => root.unmount());
  reset(); visibilityResult = async () => { throw new Error("Publish failed"); };
  const failed = await mount(React.createElement(VisibilityControl, { kind: "participation", id: 12, isPublic: true, onSaved: async () => { refreshed++; } }));
  await click("Remove from profile");
  assert.match(document.querySelector('[role="alert"]').textContent, /Publish failed/);
  assert.equal(refreshed, 1);
  assert.deepEqual(calls.find(([name]) => name === "participation").slice(1), [12, false]);
  await act(async () => failed.unmount());
});

test("portfolio loading, retry, and pagination call the public API", async () => {
  reset(); let fail = true;
  portfolioResult = async () => { if (fail) throw new Error("Portfolio unavailable"); const result = portfolio(); result.projects.next = "next"; result.projects.count = 13; return result; };
  const root = await mount(React.createElement(PublicHackathonPortfolio, { username: "portfolio" }));
  await act(async () => Promise.resolve());
  assert.match(document.querySelector('[role="alert"]').textContent, /Portfolio unavailable/);
  fail = false;
  await click("Retry portfolio");
  await act(async () => Promise.resolve());
  assert.match(document.body.textContent, /Public project/);
  await click("Next");
  await act(async () => Promise.resolve());
  assert.equal(calls.at(-1)[2].projects, 2);
  assert.match(document.body.textContent, /Page 2/);
  await act(async () => root.unmount());
});

test("a late response for a previous profile cannot replace the current portfolio", async () => {
  reset(); let resolveOld;
  portfolioResult = (username) => username === "old" ? new Promise((resolve) => { resolveOld = resolve; }) : Promise.resolve({ ...portfolio(), projects: { ...portfolio().projects, results: [{ ...portfolio().projects.results[0], title: "New profile project" }] } });
  const root = await mount(React.createElement(PublicHackathonPortfolio, { username: "old" }));
  await act(async () => root.render(React.createElement(PublicHackathonPortfolio, { username: "new" })));
  await act(async () => Promise.resolve());
  assert.match(document.body.textContent, /New profile project/);
  await act(async () => resolveOld(portfolio()));
  assert.match(document.body.textContent, /New profile project/);
  assert.ok(![...document.querySelectorAll("h3")].some((heading) => heading.textContent === "Public project"));
  await act(async () => root.unmount());
});
