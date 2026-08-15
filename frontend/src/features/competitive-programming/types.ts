import type {
  AtCoderOverallSyncStatus,
  AtCoderRatingColor,
  AtCoderSourceSyncStatus,
  AtCoderSyncErrorCode,
  CodeforcesStats,
} from "@/features/platforms/types";

export type CodeforcesAnalyticsAccount = {
  id: number;
  platform: "codeforces";
  handle: string;
  profile_url: string;
  is_verified: boolean;
  handle_validated: boolean;
  handle_validated_at: string | null;
  ownership_verified: boolean;
  ownership_verified_at: string | null;
  last_sync_attempted_at: string | null;
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

export type AtCoderAnalyticsAccount = {
  id: number;
  handle: string;
  profile_url: string;
  handle_validated: boolean;
  handle_validated_at: string | null;
  ownership_verified: boolean;
  ownership_verified_at: string | null;
  last_sync_attempted_at: string | null;
  last_synced_at: string | null;
  can_sync: boolean;
  sync_cooldown_remaining_seconds: number;
};

export type AtCoderStats = {
  discipline: "algorithm";
  current_rating: number | null;
  max_rating: number | null;
  rating_color: AtCoderRatingColor;
  rated_contest_count: number;
  last_rated_at: string | null;
  last_performance: number | null;
  solved_count: number;
  attempted_count: number;
  accepted_submission_count: number;
  indexed_submission_count: number;
  submission_stats_complete: boolean;
};

export type AtCoderSubmissionProgress = {
  status: "not_started" | "backfilling" | "caught_up" | "blocked";
  stats_complete: boolean;
  error_code: AtCoderSyncErrorCode | null;
};

export type AtCoderSourceSyncState = {
  status: AtCoderSourceSyncStatus;
  updated_at: string | null;
  attempted_at: string | null;
  using_cached_data: boolean;
  error_code: AtCoderSyncErrorCode | null;
};

export type AtCoderSyncState = {
  status: AtCoderOverallSyncStatus;
  rating: AtCoderSourceSyncState;
  submissions: AtCoderSourceSyncState & {
    progress: AtCoderSubmissionProgress;
  };
};

export type AtCoderRatingEvent = {
  contest_id: string;
  contest_name: string | null;
  rank: number | null;
  performance: number | null;
  inner_performance: number | null;
  old_rating: number | null;
  new_rating: number | null;
  rating_change: number | null;
  rated: boolean;
  occurred_at: string;
};

export type AtCoderRecentActivity = {
  submission_id: number;
  contest_id: string;
  problem_id: string;
  verdict: string;
  accepted: boolean;
  language: string | null;
  submitted_at: string;
  execution_time_ms: number | null;
  code_size_bytes: number | null;
};

export type AtCoderSnapshot = {
  captured_at: string;
  rating: number | null;
  solved_count: number | null;
  rated_contest_count: number;
  submission_stats_complete: boolean;
};

export type AtCoderAnalyticsResponse = {
  platform: "atcoder";
  account: AtCoderAnalyticsAccount | null;
  sync: AtCoderSyncState | null;
  stats: AtCoderStats | null;
  rating_history: AtCoderRatingEvent[];
  recent_activity: AtCoderRecentActivity[];
  snapshots: AtCoderSnapshot[];
};

export type RatingChartPoint = {
  contestId: string;
  contestName: string;
  rating: number;
  ratingChange: number | null;
  performance?: number | null;
  occurredAt: string;
};

export type CompetitiveActivity = {
  id: string;
  platform: "codeforces" | "atcoder";
  type: "submission" | "problem_solved" | "rating_change" | "contest";
  title: string;
  subtitle: string | null;
  verdict: string | null;
  accepted: boolean | null;
  ratingChange: number | null;
  occurredAt: string;
};

export type CompetitiveOverviewSummary = {
  active_platforms: number;
  solved_count: number;
  solved_count_complete: boolean;
  contest_count: number;
  contest_count_complete: boolean;
  accepted_submission_count: number;
  accepted_submission_count_complete: boolean;
};

export type CompetitivePlatformSummary = {
  platform: "codeforces" | "atcoder";
  connected: boolean;
  account_id: number | null;
  handle: string | null;
  profile_url: string | null;
  rating: number | null;
  max_rating: number | null;
  rank: string | null;
  solved_count: number | null;
  solved_count_complete: boolean;
  contest_count: number | null;
  contest_label: "Contests" | "Rated contests";
  accepted_submission_count: number | null;
  accepted_submission_count_complete: boolean;
};

export type CompetitiveOverviewActivity = {
  id: string;
  platform: "codeforces" | "atcoder";
  type: CompetitiveActivity["type"];
  title: string;
  subtitle: string | null;
  verdict: string | null;
  accepted: boolean | null;
  rating_change: number | null;
  occurred_at: string;
};

export type CompetitiveOverviewResponse = {
  summary: CompetitiveOverviewSummary;
  platforms: CompetitivePlatformSummary[];
  recent_activity: CompetitiveOverviewActivity[];
};
