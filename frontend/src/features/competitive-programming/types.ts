import type { CodeforcesStats } from "@/features/platforms/types";

export type CodeforcesAnalyticsAccount = {
  id: number;
  platform: "codeforces";
  handle: string;
  profile_url: string;
  is_verified: boolean;
  last_synced_at: string | null;
  can_sync: boolean;
  sync_cooldown_seconds: number;
};

export type CodeforcesRatingHistoryEntry = {
  contest_id: number | null;
  contest_name: string | null;
  rank: number | null;
  old_rating: number | null;
  new_rating: number;
  rating_change: number | null;
  timestamp: string;
};

export type CodeforcesRecentActivityEntry = {
  submission_id: number | null;
  contest_id: number | null;
  problem_index: string | null;
  problem_name: string;
  problem_rating: number | null;
  verdict: string;
  language: string | null;
  submitted_at: string;
};

export type CodeforcesSnapshot = {
  captured_at: string;
  rating: number | null;
  solved_count: number;
  contest_count: number;
};

export type CodeforcesAnalyticsResponse = {
  platform: "codeforces";
  account: CodeforcesAnalyticsAccount | null;
  stats: CodeforcesStats | null;
  rating_history: CodeforcesRatingHistoryEntry[];
  recent_activity: CodeforcesRecentActivityEntry[];
  snapshots: CodeforcesSnapshot[];
};
