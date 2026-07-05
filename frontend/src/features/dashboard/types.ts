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
  sparkline?: number[];
  trendLabel?: string;
  note?: string;
  actionLabel?: string;
  actionHref?: string;
  isActionDisabled?: boolean;
  isPlaceholder?: boolean;
};

export type PlatformStatus = "Verified" | "Unverified";

export type PlatformMark =
  | "codeforces"
  | "leetcode"
  | "atcoder"
  | "codechef"
  | "github"
  | "kaggle";

export type ConnectedPlatform = {
  id: number;
  name: string;
  handle: string;
  status: PlatformStatus;
  mark: PlatformMark | null;
  profileUrl: string;
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
