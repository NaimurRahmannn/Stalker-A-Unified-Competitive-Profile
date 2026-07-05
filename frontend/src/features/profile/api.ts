import api from "@/lib/api";
import type { PublicProfileResponse } from "./types";

export async function getPublicProfile(
  username: string,
): Promise<PublicProfileResponse> {
  const encodedUsername = encodeURIComponent(username);
  const { data } = await api.get<PublicProfileResponse>(
    `/profile/${encodedUsername}/`,
  );

  return data;
}

