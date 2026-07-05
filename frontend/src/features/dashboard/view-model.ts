import {
  BarChart3,
  Code2,
  Link2,
  RefreshCw,
  ShieldCheck,
  Trophy,
  Users,
} from "lucide-react";
import type {
  DashboardPlatform,
  DashboardResponse,
  DashboardUser,
} from "./api";
import { formatDashboardPlatformName, getPlatformMark } from "./data";
import type {
  ChecklistItem,
  ConnectedPlatform,
  JourneyItem,
  MetricItem,
  NextStep,
} from "./types";
import { formatRelativeTime } from "@/lib/utils";

type ProfileField = {
  label: string;
  value: string | null;
  nextStep: NextStep;
};

export type DashboardViewModel = {
  displayName: string;
  username: string;
  platformSummary: string;
  metrics: MetricItem[];
  connectedPlatforms: ConnectedPlatform[];
  journeyItems: JourneyItem[];
  profileProgress: number;
  profileChecklist: ChecklistItem[];
  nextSteps: NextStep[];
};

function hasText(value: string | null): boolean {
  return value !== null && value.trim().length > 0;
}

function formatHandle(handle: string): string {
  return handle.startsWith("@") ? handle : `@${handle}`;
}

function formatNumber(value: number | null, fallback: string): string {
  return value === null ? fallback : String(value);
}

function isCodeforcesPlatform(platform: DashboardPlatform): boolean {
  return platform.platform.toLowerCase() === "codeforces";
}

function pluralize(value: number, singular: string, plural = `${singular}s`) {
  return value === 1 ? singular : plural;
}

function getLatestSyncedAt(platforms: DashboardPlatform[]): string | null {
  let latestTimestamp: number | null = null;
  let latestValue: string | null = null;

  for (const platform of platforms) {
    if (!platform.last_synced_at) {
      continue;
    }

    const timestamp = new Date(platform.last_synced_at).getTime();

    if (Number.isNaN(timestamp)) {
      continue;
    }

    if (latestTimestamp === null || timestamp > latestTimestamp) {
      latestTimestamp = timestamp;
      latestValue = platform.last_synced_at;
    }
  }

  return latestValue;
}

function getProfileFields(user: DashboardUser): ProfileField[] {
  return [
    {
      label: "Full name",
      value: user.full_name,
      nextStep: {
        title: "Add your full name",
        subtitle: "Make your public profile easier to recognize.",
        icon: Users,
        accent: "green",
      },
    },
    {
      label: "Bio",
      value: user.bio,
      nextStep: {
        title: "Add a short bio",
        subtitle: "Give visitors context about what you build.",
        icon: BarChart3,
        accent: "orange",
      },
    },
    {
      label: "Avatar",
      value: user.avatar,
      nextStep: {
        title: "Add an avatar",
        subtitle: "Personalize your Stalker profile.",
        icon: Users,
        accent: "blue",
      },
    },
    {
      label: "Country",
      value: user.country,
      nextStep: {
        title: "Add your country",
        subtitle: "Help people understand your background.",
        icon: Users,
        accent: "cyan",
      },
    },
    {
      label: "Institution",
      value: user.institution,
      nextStep: {
        title: "Add your institution",
        subtitle: "Show your school or organization.",
        icon: BarChart3,
        accent: "slate",
      },
    },
    {
      label: "GitHub link",
      value: user.github_url,
      nextStep: {
        title: "Add your GitHub",
        subtitle: "Connect your coding portfolio.",
        icon: Link2,
        accent: "slate",
      },
    },
    {
      label: "LinkedIn link",
      value: user.linkedin_url,
      nextStep: {
        title: "Add your LinkedIn",
        subtitle: "Connect your professional profile.",
        icon: Link2,
        accent: "blue",
      },
    },
  ];
}

function buildProfileCompletion(user: DashboardUser) {
  const fields = getProfileFields(user);
  const checklist = fields.map<ChecklistItem>((field) => ({
    label: field.label,
    done: hasText(field.value),
  }));
  const completedCount = checklist.filter((item) => item.done).length;
  const progress = Math.round((completedCount / fields.length) * 100);

  return { fields, checklist, progress };
}

function buildMetrics(
  platforms: DashboardPlatform[],
  profileProgress: number,
): MetricItem[] {
  const latestSyncedAt = getLatestSyncedAt(platforms);
  const verifiedCount = platforms.filter((platform) => platform.is_verified).length;

  return [
    {
      label: "Platforms Connected",
      value: String(platforms.length),
      icon: Users,
      accent: "green",
    },
    {
      label: "Verified",
      value: String(verifiedCount),
      icon: ShieldCheck,
      accent: "blue",
    },
    {
      label: "Last Synced",
      value: latestSyncedAt ? formatRelativeTime(latestSyncedAt) : "Never",
      icon: RefreshCw,
      accent: "purple",
    },
    {
      label: "Profile Completion",
      value: `${profileProgress}%`,
      icon: BarChart3,
      accent: "orange",
    },
  ];
}

function buildConnectedPlatforms(
  platforms: DashboardPlatform[],
): ConnectedPlatform[] {
  return platforms.map((platform) => ({
    id: platform.id,
    name: formatDashboardPlatformName(platform.platform),
    handle: formatHandle(platform.handle),
    status: platform.is_verified ? "Verified" : "Unverified",
    mark: getPlatformMark(platform.platform),
    profileUrl: platform.profile_url,
  }));
}

function buildCompetitiveProgrammingJourney(
  codeforcesAccount: DashboardPlatform | undefined,
): JourneyItem {
  const baseItem = {
    title: "Competitive Programming",
    icon: Code2,
    accent: "green",
    stats: [],
    trendLabel: "Trend history endpoint not available yet.",
  } satisfies Pick<
    JourneyItem,
    "accent" | "icon" | "stats" | "title" | "trendLabel"
  >;

  if (!codeforcesAccount) {
    return {
      ...baseItem,
      value: "Not connected",
      label: "Connect Codeforces to show real stats",
      note: "No Codeforces account is connected yet.",
      actionLabel: "Connect Platform",
      actionHref: "/platforms",
      isPlaceholder: true,
    };
  }

  if (!codeforcesAccount.stats) {
    return {
      ...baseItem,
      value: "Not synced",
      label: "Sync Codeforces to show real stats",
      note: `Codeforces ${formatHandle(codeforcesAccount.handle)}`,
      stats: [
        {
          value: codeforcesAccount.is_verified ? "Verified" : "Unverified",
          label: "Status",
        },
        {
          value: codeforcesAccount.last_synced_at
            ? formatRelativeTime(codeforcesAccount.last_synced_at)
            : "Never",
          label: "Last synced",
        },
      ],
      actionLabel: "Manage Platform",
      actionHref: "/platforms",
      isPlaceholder: true,
    };
  }

  const stats = codeforcesAccount.stats;

  return {
    ...baseItem,
    value: String(stats.solved_count),
    label: "Problems Solved",
    note: `Codeforces ${formatHandle(codeforcesAccount.handle)}`,
    stats: [
      {
        value: formatNumber(stats.rating, "Unrated"),
        label: "Rating",
      },
      {
        value: stats.rank ?? "Unranked",
        label: "Rank",
      },
      {
        value: formatNumber(stats.max_rating, "Unrated"),
        label: "Max rating",
      },
      {
        value: String(stats.contest_count),
        label: "Contests",
      },
    ],
    actionLabel: "View Details",
    actionHref: "/competitive-programming",
  };
}

function buildComingSoonJourneyItem(
  title: string,
  label: string,
  icon: JourneyItem["icon"],
  accent: JourneyItem["accent"],
): JourneyItem {
  return {
    title,
    value: "Coming soon",
    label,
    icon,
    accent,
    stats: [],
    trendLabel: "No trend data until this connector exists.",
    note: "No backend support yet.",
    actionLabel: "Coming Soon",
    isActionDisabled: true,
    isPlaceholder: true,
  };
}

function buildJourneyItems(platforms: DashboardPlatform[]): JourneyItem[] {
  const codeforcesAccount = platforms.find(isCodeforcesPlatform);

  return [
    buildCompetitiveProgrammingJourney(codeforcesAccount),
    buildComingSoonJourneyItem(
      "CTF / Cybersecurity",
      "Connector not available yet",
      ShieldCheck,
      "blue",
    ),
    buildComingSoonJourneyItem(
      "Hackathon",
      "Backend support pending",
      Trophy,
      "purple",
    ),
    buildComingSoonJourneyItem(
      "Datathon / Data Science",
      "Backend support pending",
      BarChart3,
      "orange",
    ),
  ];
}

function buildNextSteps(
  fields: ProfileField[],
  platforms: DashboardPlatform[],
): NextStep[] {
  const steps: NextStep[] = [];
  const codeforcesAccount = platforms.find(isCodeforcesPlatform);

  if (!codeforcesAccount) {
    steps.push({
      title: "Connect Codeforces",
      subtitle: "Pull solved count, rating, and rank into the dashboard.",
      icon: Code2,
      accent: "green",
    });
  } else if (!codeforcesAccount.stats) {
    steps.push({
      title: "Sync Codeforces",
      subtitle: "Load the real Codeforces stats for this account.",
      icon: RefreshCw,
      accent: "blue",
    });
  }

  if (platforms.some((platform) => !platform.is_verified)) {
    steps.push({
      title: "Verify connected handles",
      subtitle: "Mark your linked platform accounts as trusted.",
      icon: ShieldCheck,
      accent: "blue",
    });
  }

  const missingProfileField = fields.find((field) => !hasText(field.value));

  if (missingProfileField) {
    steps.push(missingProfileField.nextStep);
  }

  return steps.slice(0, 4);
}

function buildPlatformSummary(platforms: DashboardPlatform[]): string {
  if (platforms.length === 0) {
    return "Connect a platform to start tracking real progress.";
  }

  const verifiedCount = platforms.filter((platform) => platform.is_verified).length;

  return `Tracking ${platforms.length} connected ${pluralize(
    platforms.length,
    "platform",
  )} with ${verifiedCount} verified.`;
}

export function buildDashboardViewModel(
  dashboard: DashboardResponse,
): DashboardViewModel {
  const profileCompletion = buildProfileCompletion(dashboard.user);

  return {
    displayName:
      dashboard.user.full_name.trim() || dashboard.user.username || "there",
    username: dashboard.user.username,
    platformSummary: buildPlatformSummary(dashboard.platforms),
    metrics: buildMetrics(dashboard.platforms, profileCompletion.progress),
    connectedPlatforms: buildConnectedPlatforms(dashboard.platforms),
    journeyItems: buildJourneyItems(dashboard.platforms),
    profileProgress: profileCompletion.progress,
    profileChecklist: profileCompletion.checklist,
    nextSteps: buildNextSteps(profileCompletion.fields, dashboard.platforms),
  };
}
