import { achievementPayload, type EntryFormValues } from "./schemas";

/** Build only the sections selected in the manual-entry form. */
export function buildEntryPayload(value: EntryFormValues): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    participation: { status: value.status, team_name: value.team_name, role: value.role },
    achievements: value.achievements.map((item) => ({
      ...achievementPayload(item),
      link_submission: value.projectMode !== "none" && item.link_submission,
    })),
  };
  if (value.eventMode === "existing") payload.event_id = Number(value.eventId);
  else payload.event = {
    name: value.name.trim(), organizer: value.organizer, description: value.description,
    event_url: value.event_url, start_date: value.start_date || null,
    end_date: value.end_date || null, format: value.format,
  };
  if (value.projectMode !== "none") {
    if (value.projectMode === "existing") payload.project_id = Number(value.projectId);
    else payload.project = {
      title: value.title.trim(), description: value.project_description,
      repository_url: value.repository_url, demo_url: value.demo_url,
      video_url: value.video_url, image_url: value.image_url,
      technologies: value.technologies.split(",").map((item) => item.trim()).filter(Boolean),
    };
    payload.submission = {
      status: value.submission_status,
      submission_url: value.submission_url,
      submitted_at: value.submitted_at ? new Date(value.submitted_at).toISOString() : null,
    };
  }
  return payload;
}
