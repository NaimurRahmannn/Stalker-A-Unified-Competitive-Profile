import type { CodeforcesStats } from "@/features/platforms/types";
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

export type DashboardPlatform = {
  id: number;
  platform: string;
  handle: string;
  profile_url: string;
  is_verified: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  stats: DashboardCodeforcesStats | null;
  can_sync?: boolean;
  sync_cooldown_seconds?: number;
};

export type DashboardResponse = {
  user: DashboardUser;
  platforms: DashboardPlatform[];
};

export async function getDashboard(): Promise<DashboardResponse> {
  const { data } = await api.get<DashboardResponse>("/dashboard/me/");

  return data;
}
