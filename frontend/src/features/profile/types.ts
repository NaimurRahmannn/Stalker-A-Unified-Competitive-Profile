import type { AtCoderRatingColor, CodeforcesStats, CTFTeamProfile } from "@/features/platforms/types";
import type { CompetitiveOverviewSummary, CompetitivePlatformSummary } from "@/features/competitive-programming/types";

export type PublicCodeforcesStats = Omit<
  CodeforcesStats,
  "created_at" | "handle"
>;

export type PublicAtCoderStats = {
  current_rating: number | null;
  max_rating: number | null;
  rating_color: AtCoderRatingColor;
  rated_contest_count: number;
  solved_count: number;
  attempted_count: number;
  accepted_submission_count: number;
  indexed_submission_count: number;
  submission_stats_complete: boolean;
  updated_at: string;
};

export type PublicLeetCodeStats = {
  solved_total: number;
  solved_easy: number;
  solved_medium: number;
  solved_hard: number;
  current_contest_rating: number | null;
  attended_contest_count: number;
  global_problem_ranking: number | null;
  contest_top_percentage: number | null;
  updated_at: string;
};

export interface PublicProfileUser {
  id: number;
  username: string;
  full_name: string;
  avatar: string | null;
  bio: string | null;
  country: string | null;
  institution: string | null;
  github_url: string | null;
  linkedin_url: string | null;
}

export interface PublicProfilePlatform {
  id: number;
  platform: string;
  handle: string;
  profile_url: string;
  is_verified: boolean;
  handle_validated: boolean;
  handle_validated_at: string | null;
  ownership_verified: boolean;
  ownership_verified_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  stats: PublicCodeforcesStats | PublicAtCoderStats | PublicLeetCodeStats | CTFTeamProfile | null;
}

export interface PublicProfileResponse {
  user: PublicProfileUser;
  platforms: PublicProfilePlatform[];
  competitive_programming: {
    summary: CompetitiveOverviewSummary;
    platforms: CompetitivePlatformSummary[];
  };
  hackathons: PublicHackathonSummary;
}

export type PublicHackathonSummary = {
  published_projects: number;
  public_participations: number;
  public_achievements: number;
  verified_achievements: number;
};
export type PublicPage<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type PublicHackathonProject = {
  id: number; title: string; description: string; technologies: string[]; source: "manual" | "devpost";
  associations: Array<{ event_id: number; event_name: string; event_url: string | null }>;
  project_url: string | null; repository_url: string | null; demo_url: string | null;
  video_url: string | null; image_url: string | null;
};
export type PublicHackathonParticipation = {
  id: number; status: "registered" | "attended" | "submitted"; team_name: string; role: string;
  event: { id: number; name: string; organizer: string; start_date: string | null; end_date: string | null;
    format: "online" | "in_person" | "hybrid" | "unknown"; event_url: string | null };
};
export type PublicHackathonAchievement = {
  id: number; participation_id: number; project_id: number | null; achievement_type: string;
  title: string; rank: number | null; total_participants: number | null; description: string;
  verification_status: "self_reported" | "evidence_provided" | "verified";
};
export type PublicHackathonSubmission = {
  id: number; project_id: number; project_title: string; event_id: number; event_name: string; event_url: string | null; submission_url: string | null;
};
export type PublicHackathonProjectDetail = {
  project: PublicHackathonProject; submission_count: number; submissions: PublicHackathonSubmission[];
  achievement_count: number; achievements: PublicHackathonAchievement[];
};
export type PublicHackathonPortfolio = {
  summary: PublicHackathonSummary;
  projects: PublicPage<PublicHackathonProject>;
  participations: PublicPage<PublicHackathonParticipation>;
  achievements: PublicPage<PublicHackathonAchievement>;
  submissions: PublicPage<PublicHackathonSubmission>;
};
