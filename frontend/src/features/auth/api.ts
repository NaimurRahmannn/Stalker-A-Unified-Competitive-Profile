import api from "@/lib/api";
import { saveAccessToken, saveTokens } from "@/lib/token";
import type {
  LoginPayload,
  LoginResponse,
  RefreshTokenPayload,
  RefreshTokenResponse,
  RegisterPayload,
  RegisterResponse,
  User,
} from "@/features/auth/types";

export async function registerUser(
  payload: RegisterPayload,
): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>(
    "/accounts/register/",
    payload,
  );

  if (data.tokens.access && data.tokens.refresh) {
    saveTokens(data.tokens.access, data.tokens.refresh);
  }

  return data;
}

export async function loginUser(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/accounts/login/", payload);

  saveTokens(data.access, data.refresh);

  return data;
}

export async function refreshAccessToken(
  payload: RefreshTokenPayload,
): Promise<RefreshTokenResponse> {
  const { data } = await api.post<RefreshTokenResponse>(
    "/accounts/token/refresh/",
    payload,
  );

  saveAccessToken(data.access);

  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/accounts/me/");

  return data;
}
