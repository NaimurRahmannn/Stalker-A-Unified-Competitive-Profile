import api from "@/lib/api";
import type { KaggleCapabilitiesResponse, KaggleManualTrackInput, KaggleManualTrackStatistics, KaggleOverviewResponse, KaggleSyncResponse, KaggleSyncStatusResponse, KaggleTrack } from "./types";

const root = "/datathons/kaggle";

export async function getKaggleOverview(): Promise<KaggleOverviewResponse> {
  const { data } = await api.get<KaggleOverviewResponse>(`${root}/overview/`);
  return data;
}

export async function saveKaggleManualTrack(track: KaggleTrack, values: KaggleManualTrackInput): Promise<KaggleManualTrackStatistics> {
  const { data } = await api.put<KaggleManualTrackStatistics>(`${root}/manual/${track}/`, values);
  return data;
}

export async function deleteKaggleManualTrack(track: KaggleTrack): Promise<void> {
  await api.delete(`${root}/manual/${track}/`);
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
