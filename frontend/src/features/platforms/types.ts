export type CodeforcesStats = {
  handle: string;
  rating: number | null;
  max_rating: number | null;
  rank: string | null;
  max_rank: string | null;
  solved_count: number;
  attempted_count: number;
  accepted_submission_count: number;
  contest_count: number;
  last_online_at: string | null;
  registered_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ImplementedCompetitivePlatform = "codeforces" | "atcoder";

export type AtCoderRatingColor =
  | "gray"
  | "brown"
  | "green"
  | "cyan"
  | "blue"
  | "yellow"
  | "orange"
  | "red"
  | null;

export type AtCoderSourceSyncStatus =
  | "never"
  | "success"
  | "skipped_fresh"
  | "failed"
  | "blocked"
  | "disabled";

export type AtCoderOverallSyncStatus =
  | "never_synced"
  | "success"
  | "partial"
  | "failed";

export type AtCoderSyncErrorCode =
  | "provider_disabled"
  | "rate_limited"
  | "access_denied"
  | "timeout"
  | "upstream_server_error"
  | "schema_changed"
  | "network_error"
  | "invalid_account"
  | "saturated_timestamp_boundary"
  | "provider_error"
  | "cooldown_active";

export type AtCoderStats = {
  discipline: "algorithm";
  current_rating: number | null;
  max_rating: number | null;
  rating_color: AtCoderRatingColor;
  rated_contest_count: number;
  last_rated_at: string | null;
  last_performance: number | null;
  rating_data_updated_at: string | null;
  solved_count: number;
  attempted_count: number;
  accepted_submission_count: number;
  indexed_submission_count: number;
  submission_data_updated_at: string | null;
  submission_backfill_complete: boolean;
  created_at: string;
  updated_at: string;
};

export type AtCoderSyncState = {
  overall_status: "never" | "success" | "partial" | "failed";
  rating_status: AtCoderSourceSyncStatus;
  rating_error_code: AtCoderSyncErrorCode | "";
  rating_sync_attempted_at: string | null;
  submission_status: AtCoderSourceSyncStatus;
  submission_error_code: AtCoderSyncErrorCode | "";
  submission_sync_attempted_at: string | null;
};

export type PlatformAccount = {
  id: number;
  platform: ImplementedCompetitivePlatform | string;
  handle: string;
  profile_url: string;
  is_verified: boolean;
  handle_validated: boolean;
  handle_validated_at: string | null;
  ownership_verified: boolean;
  ownership_verified_at: string | null;
  last_sync_attempted_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  codeforces_stats: CodeforcesStats | null;
  atcoder_stats: AtCoderStats | null;
  atcoder_sync_state: AtCoderSyncState | null;
  can_sync: boolean;
  sync_cooldown_seconds: number;
};

export type ConnectPlatformPayload = {
  platform: ImplementedCompetitivePlatform;
  handle: string;
};

export type AtCoderSyncSourceResult = {
  status: Exclude<AtCoderSourceSyncStatus, "never">;
  updated: boolean;
  updated_at: string | null;
  attempted_at: string | null;
  using_cached_data: boolean;
  error_code: AtCoderSyncErrorCode | null;
  message: string | null;
  details?: Record<string, unknown>;
};

export type PlatformSyncResponse = PlatformAccount & {
  status?: Exclude<AtCoderOverallSyncStatus, "never_synced">;
  attempted_at?: string;
  sources?: {
    rating: AtCoderSyncSourceResult;
    submissions: AtCoderSyncSourceResult;
  };
};
