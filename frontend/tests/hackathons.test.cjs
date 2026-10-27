/* eslint-disable @typescript-eslint/no-require-imports -- Node's CJS test loader transpiles the TypeScript feature modules. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const ts = require("typescript");

// Exercise the actual TypeScript modules without adding a test framework.
require.extensions[".ts"] = (module, filename) => {
  const source = fs.readFileSync(filename, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    fileName: filename,
  });
  module._compile(compiled.outputText, filename);
};

const { blankAchievement, blankEntry, entrySchema } = require("../src/features/hackathons/schemas.ts");
const { buildEntryPayload } = require("../src/features/hackathons/payload.ts");
const { fromLocalDateTimeInput, toLocalDateTimeInput } = require("../src/features/hackathons/datetime.ts");

const valid = (changes) => entrySchema.safeParse({ ...blankEntry(), name: "New event", ...changes }).success;

test("hidden new-event URL does not block an existing event", () => {
  const entry = { ...blankEntry(), eventMode: "existing", eventId: "45", event_url: "invalid" };
  assert.equal(entrySchema.safeParse(entry).success, true);
  assert.equal(buildEntryPayload(entry).event_id, 45);
  assert.equal("event" in buildEntryPayload(entry), false);
});

test("hidden project URL does not block an event without a project", () => {
  const entry = { ...blankEntry(), name: "Event", repository_url: "invalid" };
  assert.equal(entrySchema.safeParse(entry).success, true);
  assert.equal("project" in buildEntryPayload(entry), false);
  assert.equal("submission" in buildEntryPayload(entry), false);
});

test("hidden new-project fields do not block an existing project", () => {
  const entry = { ...blankEntry(), name: "Event", projectMode: "existing", projectId: "87", title: "", repository_url: "invalid" };
  assert.equal(entrySchema.safeParse(entry).success, true);
  assert.equal(buildEntryPayload(entry).project_id, 87);
  assert.equal("project" in buildEntryPayload(entry), false);
});

test("active URLs and dates remain validated", () => {
  assert.equal(valid({ event_url: "invalid" }), false);
  assert.equal(valid({ event_url: "ftp://example.com" }), false);
  assert.equal(valid({ start_date: "2026-11-02", end_date: "2026-11-01" }), false);
  assert.equal(valid({ projectMode: "new", title: "Project", repository_url: "invalid" }), false);
  assert.equal(valid({ projectMode: "existing", projectId: "8", submission_url: "invalid" }), false);
  assert.equal(valid({ projectMode: "none", submission_url: "invalid" }), true);
  assert.equal(valid({ projectMode: "none", submission_status: "invalid" }), true);
  assert.equal(valid({ projectMode: "new", title: "Project", submission_status: "invalid" }), false);
  assert.equal(valid({ eventMode: "existing", eventId: "3", format: "invalid" }), true);
  assert.equal(valid({ format: "invalid" }), false);
});

test("award without a project or rank keeps a null rank", () => {
  const entry = { ...blankEntry(), name: "Event", achievements: [{ ...blankAchievement(), title: "Best AI" }] };
  assert.equal(entrySchema.safeParse(entry).success, true);
  const achievement = buildEntryPayload(entry).achievements[0];
  assert.equal(achievement.rank, null);
  assert.equal(achievement.link_submission, false);
});

test("date input displays the browser clock and round trips an offset instant", () => {
  const source = "2026-10-28T07:30:45+06:00";
  const local = toLocalDateTimeInput(source);
  const parsed = new Date(source);
  assert.equal(local.slice(11, 13), String(parsed.getHours()).padStart(2, "0"));
  assert.equal(local.slice(14, 16), String(parsed.getMinutes()).padStart(2, "0"));
  assert.equal(new Date(fromLocalDateTimeInput(local)).getTime(), parsed.getTime());
  assert.equal(toLocalDateTimeInput(null), "");
  assert.equal(fromLocalDateTimeInput(""), null);
});
