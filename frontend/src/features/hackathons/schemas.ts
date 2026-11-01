import { z } from "zod";

const optionalUrl = z.string().refine((value) => !value || /^https?:\/\//i.test(value) && (() => { try { new URL(value); return true; } catch { return false; } })(), "Enter a valid http(s) URL.");
const positiveOptional = z.string().refine((value) => !value || /^\d+$/.test(value) && Number(value) > 0, "Enter a positive whole number.");
const optionalDate = z.string().refine((value) => !value || /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00`)), "Enter a valid date.");
const optionalDateTime = z.string().refine((value) => !value || !Number.isNaN(Date.parse(value)), "Enter a valid date and time.");

export const achievementSchema = z.object({
  achievement_type: z.enum(["placement", "award", "finalist", "participation", "other"]),
  title: z.string().trim().min(1, "Achievement title is required."),
  rank: positiveOptional,
  total_participants: positiveOptional,
  description: z.string(),
  evidence_url: optionalUrl,
  link_submission: z.boolean(),
}).refine((value) => !value.rank || !value.total_participants || Number(value.rank) <= Number(value.total_participants), { path: ["rank"], message: "Rank cannot exceed total participants." });

const newEventSchema = z.object({
  name: z.string().trim().min(1, "Hackathon name is required."),
  event_url: optionalUrl,
  start_date: optionalDate,
  end_date: optionalDate,
  format: z.enum(["online", "in_person", "hybrid", "unknown"]),
}).refine((value) => !value.start_date || !value.end_date || value.end_date >= value.start_date, { path: ["end_date"], message: "End date cannot precede start date." });

const newProjectSchema = z.object({
  title: z.string().trim().min(1, "Project title is required."),
  repository_url: optionalUrl,
  demo_url: optionalUrl,
  video_url: optionalUrl,
  image_url: optionalUrl,
});

const submissionSchema = z.object({ submission_status: z.enum(["draft", "submitted", "withdrawn"]), submission_url: optionalUrl, submitted_at: optionalDateTime });
const selectedIdSchema = z.string().regex(/^[1-9]\d*$/, "Select a record.");

export const entrySchema = z.object({
  eventMode: z.enum(["new", "existing"]), eventId: z.string(),
  name: z.string(), organizer: z.string(), description: z.string(), event_url: z.string(),
  start_date: z.string(), end_date: z.string(), format: z.string(),
  status: z.enum(["registered", "attended", "submitted"]), team_name: z.string(), role: z.string(),
  projectMode: z.enum(["none", "new", "existing"]), projectId: z.string(), title: z.string(), project_description: z.string(),
  repository_url: z.string(), demo_url: z.string(), video_url: z.string(), image_url: z.string(), technologies: z.string(),
  submission_status: z.string(), submission_url: z.string(), submitted_at: z.string(),
  achievements: z.array(achievementSchema),
}).superRefine((value, context) => {
  const check = (schema: z.ZodType, path?: string) => {
    const result = schema.safeParse(path ? value[path as "eventId" | "projectId"] : value);
    if (!result.success) for (const issue of result.error.issues) context.addIssue({ code: "custom", path: path ? [path] : issue.path, message: issue.message });
  };
  if (value.eventMode === "new") check(newEventSchema);
  else check(selectedIdSchema, "eventId");
  if (value.projectMode === "new") check(newProjectSchema);
  if (value.projectMode === "existing") check(selectedIdSchema, "projectId");
  if (value.projectMode !== "none") check(submissionSchema);
});

export type EntryFormValues = z.input<typeof entrySchema>;
export type AchievementFormValues = z.input<typeof achievementSchema>;
export const blankAchievement = (): AchievementFormValues => ({ achievement_type: "award", title: "", rank: "", total_participants: "", description: "", evidence_url: "", link_submission: false });

const devpostUrl = (value: string, kind: "profile" | "project" | "event") => {
  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.port || url.search || url.hash) return false;
    const host = url.hostname.toLowerCase();
    if (kind === "event") return /^[a-z0-9_-]+\.devpost\.com$/.test(host) && url.pathname === "/" && host !== "www.devpost.com";
    if (!["devpost.com", "www.devpost.com"].includes(host)) return false;
    return kind === "profile" ? /^\/[a-z0-9_-]+\/?$/i.test(url.pathname) : /^\/software\/[a-z0-9_-]+\/?$/i.test(url.pathname);
  } catch { return false; }
};

export const devpostAccountSchema = z.string().trim().min(1).max(255).refine((value) =>
  /^[a-z0-9_-]{1,64}$/i.test(value) || devpostUrl(value, "profile"), "Enter a Devpost username or profile URL.");
const importUrl = z.string().trim().max(500).refine((value) => {
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password; }
  catch { return false; }
}, "Enter an HTTP(S) URL.");
const optionalImportUrl = importUrl.optional();
const dateText = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional();
const devpostSubmissionSchema = z.object({
  hackathon_name: z.string().trim().min(1).max(500),
  hackathon_url: z.string().refine((value) => devpostUrl(value, "event"), "Enter a Devpost hackathon subdomain URL."),
  organizer: z.string().max(255).optional(), start_date: dateText, end_date: dateText,
  format: z.enum(["online", "in_person", "hybrid", "unknown"]).optional(),
  status: z.enum(["draft", "submitted", "withdrawn"]), submission_url: optionalImportUrl,
}).strict();
export const devpostImportSchema = z.object({
  format_version: z.literal(1),
  profile_url: z.string().refine((value) => devpostUrl(value, "profile"), "Enter the linked Devpost profile URL."),
  projects: z.array(z.object({
    project_url: z.string().refine((value) => devpostUrl(value, "project"), "Enter a Devpost software project URL."),
    title: z.string().trim().min(1).max(500), description: z.string().max(5000).optional(),
    repository_url: optionalImportUrl, demo_url: optionalImportUrl,
    technologies: z.array(z.string().trim().min(1).max(100)).max(30).optional(),
    submissions: z.array(devpostSubmissionSchema).max(20).optional(),
  }).strict()).max(100),
}).strict();
export const blankEntry = (): EntryFormValues => ({ eventMode: "new", eventId: "", name: "", organizer: "", description: "", event_url: "", start_date: "", end_date: "", format: "unknown", status: "registered", team_name: "", role: "", projectMode: "none", projectId: "", title: "", project_description: "", repository_url: "", demo_url: "", video_url: "", image_url: "", technologies: "", submission_status: "draft", submission_url: "", submitted_at: "", achievements: [] });
export const achievementPayload = (value: AchievementFormValues) => ({ achievement_type: value.achievement_type, title: value.title.trim(), rank: value.rank ? Number(value.rank) : null, total_participants: value.total_participants ? Number(value.total_participants) : null, description: value.description, evidence_url: value.evidence_url });
