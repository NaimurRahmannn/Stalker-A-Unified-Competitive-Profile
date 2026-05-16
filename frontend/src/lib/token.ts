const ACCESS_TOKEN_KEY = "stalker_access_token";
const REFRESH_TOKEN_KEY = "stalker_refresh_token";

function getStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

// TODO: Consider moving token storage to httpOnly cookies in production.
export function saveTokens(access: string, refresh: string): void {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.setItem(ACCESS_TOKEN_KEY, access);
  storage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function saveAccessToken(access: string): void {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.setItem(ACCESS_TOKEN_KEY, access);
}

export function getAccessToken(): string | null {
  return getStorage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
}

export function getRefreshToken(): string | null {
  return getStorage()?.getItem(REFRESH_TOKEN_KEY) ?? null;
}

export function clearTokens(): void {
  const storage = getStorage();

  if (!storage) {
    return;
  }

  storage.removeItem(ACCESS_TOKEN_KEY);
  storage.removeItem(REFRESH_TOKEN_KEY);
}

export function hasTokens(): boolean {
  return Boolean(getAccessToken() && getRefreshToken());
}
