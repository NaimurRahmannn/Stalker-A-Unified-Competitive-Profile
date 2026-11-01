export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type EventFormat = "online" | "in_person" | "hybrid" | "unknown";
export type ParticipationStatus = "registered" | "attended" | "submitted";
export type SubmissionStatus = "draft" | "submitted" | "withdrawn";
export type AchievementType = "placement" | "award" | "finalist" | "participation" | "other";
export type Overview = { hackathons_attended: number; projects_submitted: number; achievements_recorded: number; placements_recorded: number };
export type Participation = { id: number; event: number; status: ParticipationStatus; team_name: string; role: string; is_public: boolean };
export type Project = { id: number; title: string; project_url: string; description: string; repository_url: string; demo_url: string; video_url: string; image_url: string; technologies: string[]; is_public: boolean; source: string };
export type Submission = { id: number; event: number; project: number; project_title: string; status: SubmissionStatus; submission_url: string; submitted_at: string | null; source: string };
export type Achievement = { id: number; participation: number; submission: number | null; achievement_type: AchievementType; title: string; rank: number | null; total_participants: number | null; description: string; evidence_url: string; verification_status: "self_reported" | "evidence_provided" | "verified" };
export type Event = { id: number; name: string; organizer: string; description: string; event_url: string; start_date: string | null; end_date: string | null; format: EventFormat; source: string; participation: Participation | null; submissions: Submission[]; achievements: Achievement[] };
export type EntryResponse = { event_id: number; participation_id: number; project_id: number | null; submission_id: number | null; achievement_ids: number[] };

export type DevpostImportDocument = {
  format_version: 1;
  profile_url: string;
  projects: Array<{
    project_url: string; title: string; description?: string; repository_url?: string; demo_url?: string;
    technologies?: string[];
    submissions?: Array<{ hackathon_name: string; hackathon_url: string; organizer?: string;
      start_date?: string; end_date?: string; format?: EventFormat; status: SubmissionStatus; submission_url?: string }>;
  }>;
};
export type DevpostPreview = {
  projects_detected: number; hackathons_detected: number; participations_detected: number; submissions_detected: number;
  new_records: number; existing_matches: number; protected_records: number; potential_manual_duplicates: number;
  conflicts: Array<{ project_url: string; event_url: string }>;
  projects: Array<{ project_url: string; title: string; action: string; possible_manual_project_ids: number[];
    submissions: Array<{ event_url: string; event_name: string; event_action: string; participation_action: string; action: string; possible_manual_event_ids: number[] }> }>;
  preview_token: string; expires_in_seconds: number;
};
export type DevpostImportRun = {
  id: number; profile_handle: string; input_method: string; status: "completed" | "failed";
  projects_processed: number; created_count: number; updated_count: number; skipped_count: number; error_count: number;
  result: { events_created?: number; participations_created?: number; projects_created?: number; submissions_created?: number; warnings?: string[]; error?: string;
    potential_manual_duplicates?: number };
  started_at: string; completed_at: string | null;
};
