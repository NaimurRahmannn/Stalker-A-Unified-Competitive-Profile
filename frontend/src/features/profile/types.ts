import type { AtCoderRatingColor, CodeforcesStats } from "@/features/platforms/types";
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
  stats: PublicCodeforcesStats | PublicAtCoderStats | null;
}

export interface PublicProfileResponse {
  user: PublicProfileUser;
  platforms: PublicProfilePlatform[];
  competitive_programming: {
    summary: CompetitiveOverviewSummary;
    platforms: CompetitivePlatformSummary[];
  };
}
