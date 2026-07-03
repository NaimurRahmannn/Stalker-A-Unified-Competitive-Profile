import { AxiosError } from "axios";

/**
 * Extracts a human-readable message from an error thrown by the axios instance.
 *
 * Django REST Framework returns errors either as `{ "detail": "..." }` or as a
 * map of field errors like `{ "handle": ["..."] }`. This walks both shapes and
 * returns the first usable message, falling back to a generic string.
 */
export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data;

    if (typeof data === "string" && data.trim()) {
      return data;
    }

    if (data && typeof data === "object") {
      const record = data as Record<string, unknown>;

      if (typeof record.detail === "string" && record.detail.trim()) {
        return record.detail;
      }

      for (const value of Object.values(record)) {
        if (typeof value === "string" && value.trim()) {
          return value;
        }

        if (Array.isArray(value)) {
          const first = value.find(
            (item): item is string => typeof item === "string" && item.trim() !== "",
          );

          if (first) {
            return first;
          }
        }
      }
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

/**
 * Turns a platform slug like "codeforces" into a display label "Codeforces".
 */
export function formatPlatformName(platform: string): string {
  if (!platform) {
    return platform;
  }

  return platform.charAt(0).toUpperCase() + platform.slice(1);
}

const RELATIVE_UNITS: Array<[Intl.RelativeTimeFormatUnit, number]> = [
  ["year", 1000 * 60 * 60 * 24 * 365],
  ["month", 1000 * 60 * 60 * 24 * 30],
  ["week", 1000 * 60 * 60 * 24 * 7],
  ["day", 1000 * 60 * 60 * 24],
  ["hour", 1000 * 60 * 60],
  ["minute", 1000 * 60],
  ["second", 1000],
];

/**
 * Humanizes an ISO datetime into a relative string like "2 hours ago".
 * Returns the raw input if it cannot be parsed.
 */
export function formatRelativeTime(iso: string): string {
  const timestamp = new Date(iso).getTime();

  if (Number.isNaN(timestamp)) {
    return iso;
  }

  const diffMs = timestamp - Date.now();
  const absMs = Math.abs(diffMs);
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  for (const [unit, unitMs] of RELATIVE_UNITS) {
    if (absMs >= unitMs || unit === "second") {
      return formatter.format(Math.round(diffMs / unitMs), unit);
    }
  }

  return "just now";
}
