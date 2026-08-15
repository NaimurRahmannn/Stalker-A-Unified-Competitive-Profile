import type { AtCoderRatingColor, CodeforcesStats } from "@/features/platforms/types";
import type { CompetitiveOverviewSummary, CompetitivePlatformSummary } from "@/features/competitive-programming/types";
import api from "@/lib/api";

export type DashboardUser = {
  id: number;
  username: string;
  email: string;
  full_name: string;
  avatar: string | null;
  bio: string | null;
  country: string | null;
  institution: string | null;
  github_url: string | null;
  linkedin_url: string | null;
};

export type DashboardCodeforcesStats = Omit<
  CodeforcesStats,
  "created_at" | "handle"
>;

export type DashboardAtCoderStats = {
  current_rating: number | null;
  max_rating: number | null;
  rating_color: AtCoderRatingColor;
  rated_contest_count: number;
  solved_count: number;
  attempted_count: number;
  accepted_submission_count: number;
  indexed_submission_count: number;
  submission_stats_complete: boolean;
  rating_data_updated_at: string | null;
  submission_data_updated_at: string | null;
  updated_at: string;
};

export type DashboardPlatform = {
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
  stats: DashboardCodeforcesStats | DashboardAtCoderStats | null;
  can_sync: boolean;
  sync_cooldown_seconds: number;
};

export type DashboardResponse = {
  user: DashboardUser;
  platforms: DashboardPlatform[];
  competitive_programming: {
    summary: CompetitiveOverviewSummary;
    platforms: CompetitivePlatformSummary[];
  };
};

export async function getDashboard(): Promise<DashboardResponse> {
  const { data } = await api.get<DashboardResponse>("/dashboard/me/");

  return data;
}
