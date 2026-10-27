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

export const entrySchema = z.object({
  eventMode: z.enum(["new", "existing"]), eventId: z.string(),
  name: z.string(), organizer: z.string(), description: z.string(), event_url: optionalUrl,
  start_date: optionalDate, end_date: optionalDate, format: z.enum(["online", "in_person", "hybrid", "unknown"]),
  status: z.enum(["registered", "attended", "submitted"]), team_name: z.string(), role: z.string(),
  projectMode: z.enum(["none", "new", "existing"]), projectId: z.string(), title: z.string(), project_description: z.string(),
  repository_url: optionalUrl, demo_url: optionalUrl, video_url: optionalUrl, image_url: optionalUrl, technologies: z.string(),
  submission_status: z.enum(["draft", "submitted", "withdrawn"]), submission_url: optionalUrl, submitted_at: optionalDateTime,
  achievements: z.array(achievementSchema),
}).superRefine((value, context) => {
  if (value.eventMode === "new" && !value.name.trim()) context.addIssue({ code: "custom", path: ["name"], message: "Hackathon name is required." });
  if (value.eventMode === "existing" && !value.eventId) context.addIssue({ code: "custom", path: ["eventId"], message: "Select a hackathon." });
  if (value.projectMode === "new" && !value.title.trim()) context.addIssue({ code: "custom", path: ["title"], message: "Project title is required." });
  if (value.projectMode === "existing" && !value.projectId) context.addIssue({ code: "custom", path: ["projectId"], message: "Select a project." });
  if (value.start_date && value.end_date && value.end_date < value.start_date) context.addIssue({ code: "custom", path: ["end_date"], message: "End date cannot precede start date." });
});

export type EntryFormValues = z.input<typeof entrySchema>;
export type AchievementFormValues = z.input<typeof achievementSchema>;
export const blankAchievement = (): AchievementFormValues => ({ achievement_type: "award", title: "", rank: "", total_participants: "", description: "", evidence_url: "", link_submission: false });
export const blankEntry = (): EntryFormValues => ({ eventMode: "new", eventId: "", name: "", organizer: "", description: "", event_url: "", start_date: "", end_date: "", format: "unknown", status: "registered", team_name: "", role: "", projectMode: "none", projectId: "", title: "", project_description: "", repository_url: "", demo_url: "", video_url: "", image_url: "", technologies: "", submission_status: "draft", submission_url: "", submitted_at: "", achievements: [] });
export const achievementPayload = (value: AchievementFormValues) => ({ achievement_type: value.achievement_type, title: value.title.trim(), rank: value.rank ? Number(value.rank) : null, total_participants: value.total_participants ? Number(value.total_participants) : null, description: value.description, evidence_url: value.evidence_url });
