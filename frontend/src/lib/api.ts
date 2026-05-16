import axios, {
  AxiosError,
  AxiosHeaders,
  type InternalAxiosRequestConfig,
} from "axios";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveAccessToken,
} from "@/lib/token";
import type { RefreshTokenResponse } from "@/features/auth/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const AUTH_ENDPOINTS = [
  "/accounts/register/",
  "/accounts/login/",
  "/accounts/token/refresh/",
];

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const accessToken = getAccessToken();

  if (accessToken) {
    config.headers = AxiosHeaders.from(config.headers);
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const isUnauthorized = error.response?.status === 401;
    const requestUrl = originalRequest?.url;
    const isRefreshRequest = requestUrl?.includes("/accounts/token/refresh/");
    const isAuthRequest = AUTH_ENDPOINTS.some((endpoint) =>
      requestUrl?.includes(endpoint),
    );

    if (!isUnauthorized || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshRequest) {
      clearTokens();
      return Promise.reject(error);
    }

    if (isAuthRequest) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      clearTokens();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const response = await axios.post<RefreshTokenResponse>(
        "/accounts/token/refresh/",
        { refresh: refreshToken },
        {
          baseURL: API_BASE_URL,
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      saveAccessToken(response.data.access);
      originalRequest.headers = AxiosHeaders.from(originalRequest.headers);
      originalRequest.headers.set(
        "Authorization",
        `Bearer ${response.data.access}`,
      );

      return api(originalRequest);
    } catch (refreshError) {
      clearTokens();
      return Promise.reject(refreshError);
    }
  },
);

export default api;
