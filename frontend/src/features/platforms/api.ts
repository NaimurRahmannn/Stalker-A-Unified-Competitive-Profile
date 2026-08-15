import api from "@/lib/api";
import type {
  ConnectPlatformPayload,
  PlatformAccount,
  PlatformSyncResponse,
} from "@/features/platforms/types";

export async function listPlatformAccounts(): Promise<PlatformAccount[]> {
  const { data } = await api.get<PlatformAccount[]>("/platform-accounts/");

  return data;
}

export async function connectPlatformAccount(
  payload: ConnectPlatformPayload,
): Promise<PlatformAccount> {
  const { data } = await api.post<PlatformAccount>(
    "/platform-accounts/",
    payload,
  );

  return data;
}

export async function syncPlatformAccount(
  id: number,
): Promise<PlatformSyncResponse> {
  const { data } = await api.post<PlatformSyncResponse>(
    `/platform-accounts/${id}/sync/`,
  );

  return data;
}

export async function deletePlatformAccount(id: number): Promise<void> {
  await api.delete(`/platform-accounts/${id}/`);
}
