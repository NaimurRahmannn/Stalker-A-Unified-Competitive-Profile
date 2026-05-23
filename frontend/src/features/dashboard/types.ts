import type { LucideIcon } from "lucide-react";

export type MetricAccent = "green" | "blue" | "purple" | "orange";
export type WidgetAccent = MetricAccent | "cyan" | "slate";

export type MetricItem = {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: MetricAccent;
};

export type JourneyItem = {
  title: string;
  value: string;
  label: string;
  icon: LucideIcon;
  accent: MetricAccent;
  stats: Array<{
    value: string;
    label: string;
  }>;
  sparkline: number[];
};

export type PlatformStatus = "Verified" | "Unverified";

export type ConnectedPlatform = {
  name: string;
  handle: string;
  status: PlatformStatus;
  mark: "codeforces" | "leetcode" | "atcoder" | "codechef" | "github" | "kaggle";
};

export type RecentAchievement = {
  platform: string;
  title: string;
  time: string;
  icon: LucideIcon;
  accent: MetricAccent;
  badge?: string;
  description?: string;
};

export type ChecklistItem = {
  label: string;
  done: boolean;
};

export type NextStep = {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  accent: WidgetAccent;
};

export type StreakItem = {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: MetricAccent;
};
