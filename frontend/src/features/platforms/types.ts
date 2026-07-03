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

export type PlatformAccount = {
  id: number;
  platform: string;
  handle: string;
  profile_url: string;
  is_verified: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  codeforces_stats: CodeforcesStats | null;
};

export type ConnectPlatformPayload = {
  platform: string;
  handle: string;
};
