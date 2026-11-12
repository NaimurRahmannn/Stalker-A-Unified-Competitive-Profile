import api from "@/lib/api";
import type { KaggleCapabilitiesResponse, KaggleOverviewResponse, KaggleSyncResponse, KaggleSyncStatusResponse } from "./types";

const root = "/datathons/kaggle";

export async function getKaggleOverview(): Promise<KaggleOverviewResponse> {
  const { data } = await api.get<KaggleOverviewResponse>(`${root}/overview/`);
  return data;
}

export async function getKaggleCapabilities(): Promise<KaggleCapabilitiesResponse> {
  const { data } = await api.get<KaggleCapabilitiesResponse>(`${root}/capabilities/`);
  return data;
}

export async function getKaggleSyncStatus(): Promise<KaggleSyncStatusResponse> {
  const { data } = await api.get<KaggleSyncStatusResponse>(`${root}/sync-status/`);
  return data;
}

export async function requestKaggleSync(): Promise<KaggleSyncResponse> {
  const { data } = await api.post<KaggleSyncResponse>(`${root}/sync/`);
  return data;
}
