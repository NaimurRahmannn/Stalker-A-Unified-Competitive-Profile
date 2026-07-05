import type { CodeforcesStats } from "@/features/platforms/types";

export type PublicCodeforcesStats = Omit<
  CodeforcesStats,
  "created_at" | "handle"
>;

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
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  stats: PublicCodeforcesStats | null;
}

export interface PublicProfileResponse {
  user: PublicProfileUser;
  platforms: PublicProfilePlatform[];
}

