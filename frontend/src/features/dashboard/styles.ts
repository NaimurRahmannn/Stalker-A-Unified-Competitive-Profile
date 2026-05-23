import type { MetricAccent, WidgetAccent } from "./types";

type MetricAccentStyle = {
  icon: string;
  iconBg: string;
  barBg: string;
};

type JourneyAccentStyle = {
  border: string;
  icon: string;
  iconBg: string;
  value: string;
  button: string;
  buttonText: string;
  stroke: string;
};

type AchievementAccentStyle = {
  icon: string;
  iconBg: string;
  badge: string;
  border: string;
};

type WidgetAccentStyle = {
  icon: string;
  iconBg: string;
};

export const metricAccentStyles: Record<MetricAccent, MetricAccentStyle> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
    barBg: "bg-emerald-50",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
    barBg: "bg-blue-50",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
    barBg: "bg-violet-50",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
    barBg: "bg-orange-50",
  },
};

export const journeyAccentStyles: Record<MetricAccent, JourneyAccentStyle> = {
  green: {
    border: "border-emerald-100",
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
    value: "text-emerald-600",
    button: "border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50",
    buttonText: "text-emerald-700",
    stroke: "#059669",
  },
  blue: {
    border: "border-blue-100",
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
    value: "text-blue-600",
    button: "border-blue-200 bg-blue-50/50 hover:bg-blue-50",
    buttonText: "text-blue-700",
    stroke: "#2563eb",
  },
  purple: {
    border: "border-violet-100",
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
    value: "text-violet-600",
    button: "border-violet-200 bg-violet-50/50 hover:bg-violet-50",
    buttonText: "text-violet-700",
    stroke: "#7c3aed",
  },
  orange: {
    border: "border-orange-100",
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
    value: "text-orange-600",
    button: "border-orange-200 bg-orange-50/50 hover:bg-orange-50",
    buttonText: "text-orange-700",
    stroke: "#f97316",
  },
};

export const achievementAccentStyles: Record<
  MetricAccent,
  AchievementAccentStyle
> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
    badge: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
    border: "hover:border-emerald-100",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
    badge: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
    border: "hover:border-blue-100",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
    badge: "bg-violet-50 text-violet-700 ring-1 ring-violet-200",
    border: "hover:border-violet-100",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
    badge: "bg-orange-50 text-orange-700 ring-1 ring-orange-200",
    border: "hover:border-orange-100",
  },
};

export const widgetAccentStyles: Record<WidgetAccent, WidgetAccentStyle> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
  },
  cyan: {
    icon: "text-cyan-600",
    iconBg: "bg-cyan-50",
  },
  slate: {
    icon: "text-slate-600",
    iconBg: "bg-slate-50",
  },
};
