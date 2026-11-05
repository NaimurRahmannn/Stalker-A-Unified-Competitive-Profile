/* eslint-disable @typescript-eslint/no-require-imports -- Test runner loads production TSX. */
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
const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
let reviewsResult;
let reviewChanges;
let projectResult;
let dashboardProjects;
const dashboardCalls = [];
const dashboardUser = { username: "owner" };
const dashboardRouter = { replace: () => {} };
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/navigation") return { useRouter: () => dashboardRouter };
  if (request === "@/hooks/use-auth") return { useAuth: () => ({ user: dashboardUser, isLoading: false }) };
  if (request === "@/components/layout/dashboard-sidebar") return { DashboardSidebar: () => null };
  if (request === "@/components/layout/dashboard-mobile-nav") return { DashboardMobileNav: () => null };
  if (request === "sonner") return { toast: { success: () => {}, error: () => {} } };
  if (request === "next/link") return { default: function Link({ href, children, ...props }) { return require("react").createElement("a", { href, ...props }, children); } };
  if (request === "./visibility-control" && parent?.filename.endsWith("project-management-card.tsx")) return { VisibilityControl: () => require("react").createElement("span", null, "Publish to profile") };
  if (request === "../api" && parent?.filename.endsWith("duplicate-review-panel.tsx")) return { hackathonApi: {
    duplicateReviews: async () => reviewsResult,
    createDuplicateReview: async (payload) => { reviewChanges.push(payload); reviewsResult.candidates[0].id = 9; reviewsResult.candidates[0].decision = payload.decision; },
    updateDuplicateReview: async (id, decision) => { reviewChanges.push({ id, decision }); reviewsResult.candidates[0].decision = decision; },
  } };
  if (request === "../../api" && parent?.filename.endsWith("public-project-detail.tsx")) return { getPublicHackathonProject: (...args) => projectResult(...args) };
  if (parent?.filename.endsWith("hackathon-page-content.tsx")) {
    if (request === "../api") return { hackathonApi: {
      overview: async () => ({ hackathons_attended: 0, projects_submitted: 0, achievements_recorded: 0, placements_recorded: 0 }),
      events: async (page, name, filters) => { dashboardCalls.push(["events", page, filters]); return { count: 0, next: null, previous: null, results: [] }; },
      projects: (page, size, title, filters) => { dashboardCalls.push(["projects", page, filters]); return dashboardProjects(page, filters); },
    } };
    if (request === "./devpost-integration") return { DevpostIntegration: () => null };
    if (request === "./hackathon-entry-form") return { HackathonEntryForm: () => null };
    if (request === "./hackathon-detail") return { HackathonDetail: () => null, Editor: () => null };
    if (request === "./project-management-card") return { ProjectManagementCard: ({ project }) => require("react").createElement("div", { "data-project": project.title }, project.title) };
  }
  return originalLoad.call(this, request, parent, ...rest);
};

const React = require("react");
const { act } = React;
const { createRoot } = require("react-dom/client");
const { renderToStaticMarkup } = require("react-dom/server");
const { verificationLabel } = require("../src/features/hackathons/verification.ts");
const { ProjectDiscoveryFilters, EventDiscoveryFilters, initialProjectFilters, initialEventFilters } = require("../src/features/hackathons/components/discovery-filters.tsx");
const { ProjectManagementCard } = require("../src/features/hackathons/components/project-management-card.tsx");
const { ImportPreviewDetails } = require("../src/features/hackathons/components/import-preview-details.tsx");
const { DuplicateReviewPanel } = require("../src/features/hackathons/components/duplicate-review-panel.tsx");
const { PublicProjectDetail, PublicProjectDetailContent } = require("../src/features/profile/components/hackathons/public-project-detail.tsx");
const { buildPublicProfileViewModel } = require("../src/features/profile/view-model.ts");
const { HackathonPageContent } = require("../src/features/hackathons/components/hackathon-page-content.tsx");

function reset() { document.body.innerHTML = "<div id='root'></div>"; reviewChanges = []; }
async function mount(element) { const root = createRoot(document.getElementById("root")); await act(async () => root.render(element)); return root; }
async function click(label) { const button = [...document.querySelectorAll("button")].find((item) => item.textContent.includes(label)); assert.ok(button, label); await act(async () => button.dispatchEvent(new MouseEvent("click", { bubbles: true }))); }
async function type(node, value) { await act(async () => { Object.getOwnPropertyDescriptor(node.constructor.prototype, "value").set.call(node, value); node.dispatchEvent(new Event("input", { bubbles: true })); node.dispatchEvent(new Event("change", { bubbles: true })); }); }
function projectDetail() {
  return { project: { id: 4, title: "Shared build", description: "Full description", technologies: ["Python", "React"], source: "devpost",
    associations: [], project_url: "https://devpost.com/software/shared", repository_url: "https://github.com/me/shared", demo_url: "javascript:bad()", video_url: null, image_url: null },
  submission_count: 1, submissions: [{ id: 2, project_id: 4, project_title: "Shared build", event_id: 3, event_name: "Public event", event_url: "https://event.devpost.com/", submission_url: "https://example.com/submission" }],
  achievement_count: 2, achievements: [{ id: 5, participation_id: 6, project_id: 4, achievement_type: "award", title: "Community award", rank: null, total_participants: null, description: "", verification_status: "self_reported" },
    { id: 6, participation_id: 6, project_id: 4, achievement_type: "placement", title: "First place", rank: 1, total_participants: 10, description: "", verification_status: "verified" }] };
}

test("all verification statuses have accurate labels", () => {
  assert.deepEqual(verificationLabel, { verified: "Verified", evidence_provided: "Evidence provided", self_reported: "Self-reported" });
});

test("public profile includes Devpost and DoraHacks accounts without changing competitive metrics", () => {
  const platform = (platform, id) => ({ id, platform, handle: `${platform}_user`, profile_url: `https://example.com/${platform}`,
    handle_validated: false, last_synced_at: null, created_at: "2026-01-01", stats: null });
  const model = buildPublicProfileViewModel({ user: { username: "test", full_name: "", avatar: null, bio: null, country: null, institution: null, github_url: null, linkedin_url: null },
    platforms: [platform("codeforces", 1), platform("devpost", 2), platform("dorahacks", 3)],
    competitive_programming: { summary: { solved_count: 42, solved_count_complete: true, accepted_submission_count: 50,
      accepted_submission_count_complete: true, contest_count: 3, active_platforms: 1 }, platforms: [] },
    hackathons: { published_projects: 2, public_participations: 1, public_achievements: 0, verified_achievements: 0 } });
  assert.deepEqual(model.domainCards.find((item) => item.key === "hackathon").accounts.map((item) => item.id), [2, 3]);
  assert.deepEqual(model.competitivePlatforms.map((item) => item.id), [1]);
  assert.equal(model.competitiveMetrics[0].value, "42");
});

test("project and event filter controls expose all options and reset", async () => {
  reset(); const changes = [];
  const root = await mount(React.createElement(ProjectDiscoveryFilters, { filters: initialProjectFilters, onChange: (value) => changes.push(value), onReset: () => changes.push("reset") }));
  assert.match(document.body.textContent, /All sources/);
  assert.match(document.body.textContent, /Title Z–A/);
  await click("Reset project filters");
  assert.equal(changes.at(-1), "reset");
  await act(async () => root.unmount());
  const eventHtml = renderToStaticMarkup(React.createElement(EventDiscoveryFilters, { filters: initialEventFilters, onChange: () => {}, onReset: () => {} }));
  for (const label of ["Participation status", "Event year", "Event format", "Event source", "Event date newest"]) assert.ok(eventHtml.includes(label));
});

test("dashboard filters reset pagination and ignore late search responses", async () => {
  reset(); dashboardCalls.length = 0;
  let resolveFirst;
  let resolveSecond;
  dashboardProjects = (page, filters) => {
    if (filters.search === "first") return new Promise((resolve) => { resolveFirst = resolve; });
    if (filters.search === "second") return new Promise((resolve) => { resolveSecond = resolve; });
    return Promise.resolve({ count: 21, results: [{ id: page, title: `Page ${page}` }], next: page === 1 ? "next" : null, previous: page === 2 ? "previous" : null });
  };
  const root = await mount(React.createElement(HackathonPageContent));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 10)));
  const nextProject = [...document.querySelectorAll("button")].filter((item) => item.textContent === "Next").at(-1);
  await act(async () => nextProject.dispatchEvent(new MouseEvent("click", { bubbles: true })));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 10)));
  assert.ok(dashboardCalls.some(([name, page]) => name === "projects" && page === 2));
  const search = [...document.querySelectorAll("input")].find((item) => item.placeholder === "Title or description");
  await type(search, "first");
  await act(async () => new Promise((resolve) => setTimeout(resolve, 10)));
  assert.ok(dashboardCalls.some(([name, page, filters]) => name === "projects" && page === 1 && filters.search === "first"));
  await type(search, "second");
  await act(async () => new Promise((resolve) => setTimeout(resolve, 10)));
  await act(async () => resolveSecond({ count: 1, results: [{ id: 9, title: "Second result" }], next: null, previous: null }));
  assert.match(document.body.textContent, /Second result/);
  await act(async () => resolveFirst({ count: 1, results: [{ id: 8, title: "First result" }], next: null, previous: null }));
  assert.match(document.body.textContent, /Second result/);
  assert.ok(!document.querySelector('[data-project="First result"]'));
  await click("Reset project filters");
  await act(async () => new Promise((resolve) => setTimeout(resolve, 10)));
  assert.equal(dashboardCalls.at(-1)[2].search, "");
  await act(async () => root.unmount());
});

test("management card shows data and protects imported metadata controls", () => {
  const item = { id: 1, title: "Imported project", description: "Description", technologies: ["Python"], source: "devpost", is_public: true,
    project_url: "https://devpost.com/software/example", repository_url: "https://github.com/example", demo_url: "https://example.com/demo", updated_at: "2026-01-01T00:00:00Z", related_hackathon_count: 2 };
  const html = renderToStaticMarkup(React.createElement(ProjectManagementCard, { project: item, onSaved: async () => {}, onEdit: () => {}, onDelete: () => {}, deleting: false }));
  for (const text of ["Imported project", "Devpost import", "Published", "2 related hackathons", "Repository", "Live demo"]) assert.ok(html.includes(text));
  assert.match(html, /disabled=""/);
});

test("import preview shows bounded field changes, protection, and candidates", () => {
  const change = { field: "title", before: "Old title", after: "New title", truncated: false };
  const plan = { projects_detected: 1, hackathons_detected: 1, submissions_detected: 1, potential_manual_duplicates: 1,
    action_counts: { create: 0, update: 0, unchanged: 0, protected: 1, conflict: 1 }, conflicts: [{ project_url: "https://devpost.com/software/shared", event_url: "" }],
    projects: [{ title: "New title", project_url: "https://devpost.com/software/shared", action: "protected", reason: "A verified achievement protects this record.", changes: [change],
      possible_manual_projects: [{ id: 4, title: "Manual title", project_url: "", repository_url: "https://github.com/example", demo_url: "", reason: "Matching repository URL" }],
      submissions: [{ event_name: "Public event", event_url: "https://event.devpost.com", event_action: "unchanged", participation_action: "unchanged", action: "unchanged", reason: "", changes: [], event_changes: [], possible_manual_events: [] }] }] };
  const html = renderToStaticMarkup(React.createElement(ImportPreviewDetails, { preview: plan }));
  for (const text of ["Old title", "New title", "protected", "conflicts", "Possible manual project", "Manual title"]) assert.ok(html.includes(text));
});

test("duplicate review changes decisions without a merge action", async () => {
  reset(); reviewsResult = { candidates: [{ id: null, record_type: "project", manual: { id: 1, title: "Manual", repository_url: "https://github.com/shared", source: "manual", is_public: false },
    imported: { id: 2, title: "Imported", repository_url: "https://github.com/shared", source: "devpost", is_public: true }, reason: "Matching repository URL", decision: "unresolved" }],
    reviews: { count: 0, results: [], next: null, previous: null } };
  const root = await mount(React.createElement(DuplicateReviewPanel));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  assert.match(document.body.textContent, /does not merge/);
  await click("Mark related");
  assert.equal(reviewChanges[0].decision, "related");
  await click("Mark distinct");
  assert.deepEqual(reviewChanges[1], { id: 9, decision: "distinct" });
  await act(async () => root.unmount());
});

test("public project detail renders eligible data, fallbacks, safe links, loading and 404", async () => {
  reset(); const detail = projectDetail();
  const html = renderToStaticMarkup(React.createElement(PublicProjectDetailContent, { detail, username: "owner" }));
  for (const text of ["Shared build", "Full description", "Python", "Public event", "Community award", "Self-reported", "First place", "Verified"]) assert.ok(html.includes(text));
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes('href="javascript:'));
  assert.ok(html.includes("/profile/owner"));
  let resolve;
  projectResult = () => new Promise((done) => { resolve = done; });
  const root = await mount(React.createElement(PublicProjectDetail, { username: "owner", projectId: 4 }));
  assert.match(document.body.textContent, /Loading project/);
  await act(async () => resolve(detail));
  assert.match(document.body.textContent, /Shared build/);
  await act(async () => root.unmount());
  reset(); projectResult = async () => { const error = new (require("axios").AxiosError)("missing"); error.response = { status: 404, data: {} }; throw error; };
  const missing = await mount(React.createElement(PublicProjectDetail, { username: "owner", projectId: 4 }));
  await act(async () => Promise.resolve());
  assert.match(document.body.textContent, /Project not found/);
  await act(async () => missing.unmount());
});
