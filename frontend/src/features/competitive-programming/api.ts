import api from "@/lib/api";
import type { AtCoderAnalyticsResponse, CodeforcesAnalyticsResponse, CompetitiveOverviewResponse } from "./types";

export async function getCodeforcesAnalytics(): Promise<CodeforcesAnalyticsResponse> {
  const { data } = await api.get<CodeforcesAnalyticsResponse>(
    "/competitive-programming/codeforces/",
  );
  return data;
}

export async function getAtCoderAnalytics(): Promise<AtCoderAnalyticsResponse> {
  const { data } = await api.get<AtCoderAnalyticsResponse>(
    "/competitive-programming/atcoder/",
  );
  return data;
}

export async function getCompetitiveProgrammingOverview(): Promise<CompetitiveOverviewResponse> {
  const { data } = await api.get<CompetitiveOverviewResponse>(
    "/competitive-programming/overview/",
  );
  return data;
}
