export type KaggleTrack = "competitions" | "code" | "datasets";
export type KaggleRankStatus = "ranked" | "unranked" | "unknown";
export type KaggleCollectionStatus = "not_collected" | "success" | "failed";
export type KaggleCollectionRunStatus = "not_started" | "queued" | "running" | "retrying" | "succeeded" | "failed" | "cancelled";

export type KaggleTrackStatistics = {
  rank_status: KaggleRankStatus;
  global_rank: number | null;
  highest_rank: number | null;
  tier: string | null;
  points: string | number | null;
  gold_medals: number | null;
  silver_medals: number | null;
  bronze_medals: number | null;
  source: string | null;
  data_collected_at: string | null;
};

export type KaggleManualTrackStatistics = Omit<KaggleTrackStatistics, "source" | "data_collected_at"> & {
  track: KaggleTrack;
  updated_at: string;
};

export type KaggleManualTrackInput = Omit<KaggleManualTrackStatistics, "track" | "updated_at">;

export type KaggleSummary = {
  competitions_rank: number | null;
  competitions_tier: string | null;
  code_rank: number | null;
  code_tier: string | null;
  datasets_rank: number | null;
  datasets_tier: string | null;
  total_medals: number;
  gold_medals: number;
  silver_medals: number;
  bronze_medals: number;
  has_data: boolean;
};

export type KaggleOverviewResponse = {
  linked: boolean;
  username: string | null;
  profile_url: string | null;
  collection_status: KaggleCollectionStatus;
  last_attempted_at: string | null;
  last_successful_at: string | null;
  tracks: Record<KaggleTrack, KaggleTrackStatistics>;
  manual_tracks: Record<KaggleTrack, KaggleManualTrackStatistics | null>;
  summary?: KaggleSummary;
};

export type KaggleCapabilitiesResponse = {
  collection_enabled: boolean;
  provider_available: boolean;
  can_request_sync: boolean;
  reason: string | null;
};

export type KaggleSyncResponse = {
  run_id: number;
  status: KaggleCollectionRunStatus;
  username: string;
  deduplicated: boolean;
  queued_at: string;
};

export type KaggleSyncStatusResponse = {
  run_id: number | null;
  username: string;
  status: KaggleCollectionRunStatus;
  trigger?: string;
  attempt_count?: number;
  queued_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  next_attempt_at?: string | null;
  error_code?: string | null;
  dispatch_state?: "pending" | "dispatched" | "failed";
};
