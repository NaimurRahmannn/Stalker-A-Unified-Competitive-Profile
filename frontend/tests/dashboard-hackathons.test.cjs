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
const { buildPublicProfileViewModel } = require("../src/features/profile/view-model.ts");
const { DomainProfileCards } = require("../src/features/profile/components/domain-profile-cards.tsx");

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

test("linked Kaggle account and datathon overview populate dashboard journey item and platform card", () => {
  const accounts = [{
    id: 9, platform: "kaggle", handle: "kaggler", profile_url: "https://www.kaggle.com/kaggler",
    handle_validated: false, is_verified: false, stats: null,
  }];
  const datathons = {
    linked: true, username: "kaggler", profile_url: "https://www.kaggle.com/kaggler",
    collection_status: "not_collected", last_attempted_at: null, last_successful_at: null,
    tracks: { competitions: null, code: null, datasets: null },
    manual_tracks: {
      competitions: { track: "competitions", rank_status: "ranked", global_rank: 1200, highest_rank: 800, tier: "expert", points: "1500", gold_medals: 0, silver_medals: 2, bronze_medals: 1, updated_at: "2026-01-01" },
      code: null, datasets: null,
    },
    summary: { competitions_rank: 1200, competitions_tier: "expert", code_rank: null, code_tier: null, datasets_rank: null, datasets_tier: null, total_medals: 3, gold_medals: 0, silver_medals: 2, bronze_medals: 1, has_data: true },
  };
  const dashData = dashboard({ hackathons_attended: 0, projects_submitted: 0, achievements_recorded: 0, placements_recorded: 0 }, accounts);
  dashData.datathons = datathons;
  const model = buildDashboardViewModel(dashData);

  assert.deepEqual(model.connectedPlatforms.find((p) => p.mark === "kaggle"), {
    id: 9, name: "Kaggle", handle: "@kaggler", status: "Linked", mark: "kaggle", profileUrl: "https://www.kaggle.com/kaggler",
  });
  const datathonItem = model.journeyItems.find((row) => row.title === "Datathon / Data Science");
  assert.equal(datathonItem.value, "Expert");
  assert.equal(datathonItem.label, "Competitions Rank #1,200");
  assert.equal(datathonItem.actionHref, "/datathon");
  assert.equal(datathonItem.isPlaceholder, false);
  assert.deepEqual(datathonItem.stats.map((s) => [s.label, s.value]), [
    ["Competitions (Expert)", "#1,200"],
    ["Code", "Unranked"],
    ["Datasets", "Unranked"],
    ["Medals (0G · 2S · 1B)", "3"],
  ]);
});

test("public profile connects Kaggle account and datathon domain card metrics", () => {
  const accounts = [{
    id: 9, platform: "kaggle", handle: "kaggler", profile_url: "https://www.kaggle.com/kaggler",
    handle_validated: false, is_verified: false, last_synced_at: null, created_at: "2026-01-01",
    stats: { competitions_rank: 1200, competitions_tier: "Expert", code_rank: null, code_tier: null, datasets_rank: null, datasets_tier: null, total_medals: 3, has_data: true },
  }];
  const datathons = {
    linked: true, username: "kaggler", profile_url: "https://www.kaggle.com/kaggler",
    collection_status: "not_collected", last_attempted_at: null, last_successful_at: null,
    tracks: { competitions: null, code: null, datasets: null },
    manual_tracks: { competitions: null, code: null, datasets: null },
    summary: { competitions_rank: 1200, competitions_tier: "Expert", code_rank: null, code_tier: null, datasets_rank: null, datasets_tier: null, total_medals: 3, gold_medals: 0, silver_medals: 2, bronze_medals: 1, has_data: true },
  };
  const profileModel = buildPublicProfileViewModel({
    user: { username: "kaggler", full_name: "Kaggle User", avatar: null, bio: null, country: null, institution: null, github_url: null, linkedin_url: null },
    platforms: accounts,
    competitive_programming: { summary: { solved_count: 0, solved_count_complete: true, accepted_submission_count: 0, accepted_submission_count_complete: true, contest_count: 0, active_platforms: 0 }, platforms: [] },
    hackathons: { published_projects: 0, public_participations: 0, public_achievements: 0, verified_achievements: 0 },
    datathons,
  });

  const datathonCard = profileModel.domainCards.find((c) => c.key === "datathon");
  assert.ok(datathonCard);
  assert.equal(datathonCard.accounts.length, 1);
  assert.equal(datathonCard.accounts[0].name, "Kaggle");
  assert.equal(datathonCard.accounts[0].handle, "@kaggler");
  assert.deepEqual(datathonCard.metrics, [
    { label: "Best Tier", value: "Expert" },
    { label: "Comp Rank", value: "#1,200" },
    { label: "Medals", value: "3" },
  ]);

  const kagglePlatform = profileModel.platforms.find((p) => p.slug === "kaggle");
  assert.equal(kagglePlatform.rating, "Expert");
  assert.equal(kagglePlatform.ratingLabel, "Tier");
  assert.equal(kagglePlatform.rank, "#1,200 Comp");
  assert.equal(kagglePlatform.solved, "3 medals");

  const cardsHtml = renderToStaticMarkup(React.createElement(DomainProfileCards, { cards: profileModel.domainCards }));
  assert.match(cardsHtml, /kaggle_logo\.png/);
  assert.match(cardsHtml, /View Kaggle Profile/);
  assert.match(cardsHtml, /href="https:\/\/www\.kaggle\.com\/kaggler"/);
});

test("dashboard and profile display code track stats without userid in datathon card", () => {
  const accounts = [{
    id: 9, platform: "kaggle", handle: "seifmohmed", profile_url: "https://www.kaggle.com/seifmohmed",
    handle_validated: false, is_verified: false, last_synced_at: null, created_at: "2026-01-01",
    stats: { competitions_rank: null, competitions_tier: null, code_rank: 9725, code_tier: "Expert", datasets_rank: null, datasets_tier: null, total_medals: 0, has_data: true },
  }];
  const datathons = {
    linked: true, username: "seifmohmed", profile_url: "https://www.kaggle.com/seifmohmed",
    collection_status: "not_collected", last_attempted_at: null, last_successful_at: null,
    tracks: { competitions: null, code: null, datasets: null },
    manual_tracks: {
      competitions: null,
      code: { track: "code", rank_status: "ranked", global_rank: 9725, highest_rank: 9725, tier: "Expert", points: null, gold_medals: null, silver_medals: null, bronze_medals: null, updated_at: "2026-11-13" },
      datasets: null,
    },
    summary: { competitions_rank: null, competitions_tier: null, code_rank: 9725, code_tier: "Expert", datasets_rank: null, datasets_tier: null, total_medals: 0, gold_medals: 0, silver_medals: 0, bronze_medals: 0, has_data: true },
  };

  const dashData = dashboard({ hackathons_attended: 0, projects_submitted: 0, achievements_recorded: 0, placements_recorded: 0 }, accounts);
  dashData.datathons = datathons;
  const model = buildDashboardViewModel(dashData);

  const datathonItem = model.journeyItems.find((row) => row.title === "Datathon / Data Science");
  assert.equal(datathonItem.value, "Expert");
  assert.equal(datathonItem.label, "Code Rank #9,725");
  assert.equal(datathonItem.isPlaceholder, false);
  assert.doesNotMatch(datathonItem.value, /seifmohmed/);
  assert.doesNotMatch(datathonItem.label, /seifmohmed/);
  assert.deepEqual(datathonItem.stats.map((s) => [s.label, s.value]), [
    ["Competitions", "Unranked"],
    ["Code (Expert)", "#9,725"],
    ["Datasets", "Unranked"],
    ["Total medals", "0"],
  ]);

  const profileModel = buildPublicProfileViewModel({
    user: { username: "seifmohmed", full_name: "Seif", avatar: null, bio: null, country: null, institution: null, github_url: null, linkedin_url: null },
    platforms: accounts,
    competitive_programming: { summary: { solved_count: 0, solved_count_complete: true, accepted_submission_count: 0, accepted_submission_count_complete: true, contest_count: 0, active_platforms: 0 }, platforms: [] },
    hackathons: { published_projects: 0, public_participations: 0, public_achievements: 0, verified_achievements: 0 },
    datathons,
  });

  const datathonCard = profileModel.domainCards.find((c) => c.key === "datathon");
  assert.deepEqual(datathonCard.metrics, [
    { label: "Best Tier", value: "Expert" },
    { label: "Code Rank", value: "#9,725" },
    { label: "Medals", value: "0" },
  ]);

  const kagglePlatform = profileModel.platforms.find((p) => p.slug === "kaggle");
  assert.equal(kagglePlatform.rating, "Expert");
  assert.equal(kagglePlatform.ratingLabel, "Tier");
  assert.equal(kagglePlatform.rank, "#9,725 Code");
  assert.equal(kagglePlatform.solved, "1 track active");
  assert.equal(kagglePlatform.hasDetailedStats, true);
});
