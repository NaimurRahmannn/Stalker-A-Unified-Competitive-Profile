import api from "@/lib/api";
import type { PublicHackathonPortfolio, PublicProfileResponse } from "./types";

export async function getPublicProfile(
  username: string,
): Promise<PublicProfileResponse> {
  const encodedUsername = encodeURIComponent(username);
  const { data } = await api.get<PublicProfileResponse>(
    `/profile/${encodedUsername}/`,
  );

  return data;
}

export async function getPublicHackathonPortfolio(username: string, pages: {
  projects: number; participations: number; achievements: number; submissions: number;
}): Promise<PublicHackathonPortfolio> {
  const { data } = await api.get<PublicHackathonPortfolio>(`/profile/${encodeURIComponent(username)}/hackathons/`, {
    params: {
      projects_page: pages.projects, participations_page: pages.participations,
      achievements_page: pages.achievements, submissions_page: pages.submissions,
    },
  });
  return data;
}

