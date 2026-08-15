import api from "@/lib/api";
import type { CodeforcesAnalyticsResponse } from "./types";

export async function getCodeforcesAnalytics(): Promise<CodeforcesAnalyticsResponse> {
  const { data } = await api.get<CodeforcesAnalyticsResponse>(
    "/competitive-programming/codeforces/",
  );
  return data;
}
