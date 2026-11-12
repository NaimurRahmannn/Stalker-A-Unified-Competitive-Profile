/* eslint-disable @typescript-eslint/no-require-imports -- Node loads the actual TypeScript modules. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const test = require("node:test");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

for (const extension of [".ts", ".tsx"]) require.extensions[extension] = (module, filename) => {
  const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  }, fileName: filename });
  module._compile(compiled.outputText, filename);
};

const originalResolve = Module._resolveFilename;
const originalLoad = Module._load;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request.startsWith("@/")) request = path.join(__dirname, "../src", request.slice(2));
  return originalResolve.call(this, request, parent, ...rest);
};
Module._load = function (request, parent, ...rest) {
  if (request === "next/link") return { default: ({ href, children, ...props }) => React.createElement("a", { href, ...props }, children) };
  if (request === "next/image") return { default: ({ src, alt, ...props }) => React.createElement("img", { src, alt, ...props }) };
  return originalLoad.call(this, request, parent, ...rest);
};

const { buildDashboardViewModel } = require("../src/features/dashboard/view-model.ts");
const { TechnicalJourneySection } = require("../src/features/dashboard/components/technical-journey-section.tsx");
const { ConnectedPlatformsSection } = require("../src/features/dashboard/components/connected-platforms-section.tsx");
const { ProfilePlatformLogo } = require("../src/features/profile/components/profile-platform-logo.tsx");

function dashboard(hackathons, platforms = []) {
  return {
    user: { username: "owner", full_name: "Owner", avatar: null, bio: null, country: null,
      institution: null, github_url: null, linkedin_url: null },
    platforms,
    competitive_programming: { summary: { active_platforms: 0, solved_count: 0,
      solved_count_complete: true, contest_count: 0, contest_count_complete: true,
      accepted_submission_count: 0, accepted_submission_count_complete: true }, platforms: [] },
    hackathons,
  };
}

test("dashboard shows real Hackathon totals and opens management", () => {
  const model = buildDashboardViewModel(dashboard({
    hackathons_attended: 2, projects_submitted: 3,
    achievements_recorded: 4, placements_recorded: 1,
  }));
  const item = model.journeyItems.find((row) => row.title === "Hackathon");
  assert.equal(item.value, "2");
  assert.equal(item.label, "Hackathons attended");
  assert.deepEqual(item.stats.map((row) => [row.label, row.value]), [
    ["Projects submitted", "3"], ["Achievements recorded", "4"], ["Placements recorded", "1"],
  ]);
  const html = renderToStaticMarkup(React.createElement(TechnicalJourneySection, { items: [item] }));
  assert.match(html, /href="\/hackathon"/);
  assert.match(html, /devpost-logo\.png/);
  assert.match(html, />Manual</);
  assert.doesNotMatch(html, /Coming Soon|Backend support pending|Planned/);
});

test("empty Hackathon data still gives a working action", () => {
  const model = buildDashboardViewModel(dashboard({
    hackathons_attended: 0, projects_submitted: 0,
    achievements_recorded: 0, placements_recorded: 0,
  }));
  const item = model.journeyItems.find((row) => row.title === "Hackathon");
  assert.equal(item.value, "0");
  assert.equal(item.actionLabel, "Add Hackathon");
  assert.equal(item.actionHref, "/hackathon");
  assert.notEqual(item.isActionDisabled, true);
  const datathon = model.journeyItems.find((row) => row.title === "Datathon / Data Science");
  assert.equal(datathon.actionHref, "/datathon");
  assert.equal(datathon.value, "Not connected");
});

test("linked Hackathon accounts appear without being called verified", () => {
  const accounts = ["devpost", "dorahacks"].map((platform, index) => ({
    id: index + 1, platform, handle: `user${index}`, profile_url: `https://example.com/user${index}`,
    handle_validated: false, is_verified: false, stats: null,
  }));
  const model = buildDashboardViewModel(dashboard({
    hackathons_attended: 0, projects_submitted: 0,
    achievements_recorded: 0, placements_recorded: 0,
  }, accounts));
  assert.deepEqual(model.connectedPlatforms.map((row) => [row.name, row.status, row.mark]), [
    ["Devpost", "Linked", "devpost"], ["DoraHacks", "Linked", null],
  ]);
  assert.equal(model.platformSummary, "Tracking 2 connected platforms with 0 validated accounts.");
  const connectedHtml = renderToStaticMarkup(React.createElement(ConnectedPlatformsSection, { platforms: model.connectedPlatforms }));
  const profileHtml = renderToStaticMarkup(React.createElement(ProfilePlatformLogo, { mark: "devpost", slug: "devpost", name: "Devpost" }));
  assert.match(connectedHtml, /devpost-logo\.png/);
  assert.match(profileHtml, /devpost-logo\.png/);
});
