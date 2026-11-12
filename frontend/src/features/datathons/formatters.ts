import type { KaggleRankStatus } from "./types";

export function formatRank(value: number | null, status: KaggleRankStatus, collected: boolean): string {
  if (status === "ranked" && value !== null) return `#${value.toLocaleString("en-US")}`;
  if (status === "unranked") return "Unranked";
  return collected ? "Not available" : "Not collected";
}

export function formatNumber(value: number | null): string {
  return value === null ? "Not available" : value.toLocaleString("en-US");
}

export function formatPoints(value: string | number | null): string {
  if (value === null) return "Not available";
  const number = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(number) ? number.toLocaleString("en-US", { maximumFractionDigits: 4 }) : "Not available";
}

export function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "Not collected";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not available" : date.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });
}

export function formatTier(value: string | null): string {
  if (!value) return "Not available";
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}
