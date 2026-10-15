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
import type { CompetitiveOverviewSummary, CompetitivePlatformSummary } from "@/features/competitive-programming/types";
import { formatDashboardPlatformName, getPlatformMark } from "./data";
import type {
  ChecklistItem,
  ConnectedPlatform,
  JourneyItem,
  MetricItem,
  NextStep,
} from "./types";

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

function isSupportedPlatform(platform: DashboardPlatform): boolean {
  return platform.platform === "codeforces" || platform.platform === "atcoder" || platform.platform === "leetcode";
}

function isManagedPlatform(platform: DashboardPlatform): boolean {
  return isSupportedPlatform(platform) || platform.platform === "ctftime";
}

function pluralize(value: number, singular: string, plural = `${singular}s`) {
  return value === 1 ? singular : plural;
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
  profileProgress: number,
  competitive: CompetitiveOverviewSummary,
): MetricItem[] {
  const incomplete = !competitive.solved_count_complete;

  return [
    {
      label: incomplete ? "Known Problems Solved" : "Problems Solved",
      value: `${competitive.solved_count}${incomplete ? "+" : ""}`,
      icon: Users,
      accent: "green",
    },
    {
      label: "Tracked Contests",
      value: String(competitive.contest_count),
      icon: ShieldCheck,
      accent: "blue",
    },
    {
      label: "Competitive Platforms",
      value: String(competitive.active_platforms),
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
  return platforms.filter(isManagedPlatform).map((platform) => ({
    id: platform.id,
    name: formatDashboardPlatformName(platform.platform),
    handle: platform.platform === "ctftime" ? `Team #${platform.handle}` : formatHandle(platform.handle),
    status: platform.platform === "ctftime"
      ? (platform.handle_validated ? "Team found" : "Team not validated")
      : (platform.handle_validated ? "Handle valid" : "Handle not validated"),
    mark: getPlatformMark(platform.platform),
    profileUrl: platform.profile_url,
  }));
}

function buildCompetitiveProgrammingJourney(
  platforms: CompetitivePlatformSummary[],
  summary: CompetitiveOverviewSummary,
): JourneyItem {
  const baseItem = {
    title: "Competitive Programming",
    icon: Code2,
    accent: "green",
    stats: [],
    platformMarks: ["codeforces", "atcoder", "leetcode"],
    trendLabel: "Trend history endpoint not available yet.",
  } satisfies Pick<
    JourneyItem,
    "accent" | "icon" | "stats" | "title" | "platformMarks" | "trendLabel"
  >;

  const connected = platforms.filter((platform) => platform.connected);
  if (connected.length === 0) {
    return {
      ...baseItem,
      value: "Not connected",
      label: "Connect Codeforces, AtCoder, or LeetCode",
      note: "No competitive platform is connected yet.",
      actionLabel: "Connect Platform",
      actionHref: "/platforms",
      isPlaceholder: true,
    };
  }

  if (connected.every((platform) => platform.solved_count === null)) {
    return {
      ...baseItem,
      value: "Not synced",
      label: "Sync a platform to show real stats",
      note: `${connected.length} competitive ${pluralize(connected.length, "platform")} connected`,
      actionLabel: "Manage Platform",
      actionHref: "/platforms",
      isPlaceholder: true,
    };
  }

  return {
    ...baseItem,
    value: `${summary.solved_count}${summary.solved_count_complete ? "" : "+"}`,
    label: summary.solved_count_complete ? "Problems Solved" : "Known Problems Solved",
    note: summary.solved_count_complete ? `${connected.length} active ${pluralize(connected.length, "platform")}` : "AtCoder history is still indexing.",
    stats: connected.flatMap((platform) => [
      { value: formatNumber(platform.rating, "Unrated"), label: `${platform.platform === "codeforces" ? "Codeforces" : platform.platform === "leetcode" ? "LeetCode" : "AtCoder"} rating` },
      { value: platform.rank ?? "Unranked", label: `${platform.platform === "codeforces" ? "CF" : platform.platform === "leetcode" ? "LC" : "AC"} rank` },
    ]),
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

function buildCTFJourneyItem(platforms: DashboardPlatform[]): JourneyItem {
  const baseItem = {
    title: "CTF / Cybersecurity",
    icon: ShieldCheck,
    accent: "blue",
    stats: [],
    platformMarks: ["ctftime"],
    actionHref: "/ctf",
  } satisfies Pick<JourneyItem, "title" | "icon" | "accent" | "stats" | "platformMarks" | "actionHref">;
  const account = platforms.find((platform) => platform.platform === "ctftime");

  if (!account) {
    return {
      ...baseItem,
      value: "Not connected",
      label: "Connect a CTFtime team",
      note: "No CTF platform is connected yet.",
      trendLabel: "Yearly ratings will appear after your first sync.",
      actionLabel: "Connect Team",
      actionHref: "/platforms",
      isPlaceholder: true,
    };
  }

  const profile = account.stats && "yearly_rankings" in account.stats
    ? account.stats
    : null;
  if (!profile) {
    return {
      ...baseItem,
      value: "Not synced",
      label: "Sync CTFtime to show real stats",
      note: `Team #${account.handle} is connected`,
      trendLabel: "Sync the team to load its profile and yearly rankings.",
      actionLabel: "View Details",
      isPlaceholder: true,
    };
  }

  const rankings = [...profile.yearly_rankings].sort((a, b) => b.year - a.year);
  const latest = rankings[0];
  if (!latest) {
    return {
      ...baseItem,
      value: "Team found",
      label: profile.name,
      note: "No yearly ranking is available for this team yet.",
      trendLabel: "Yearly ratings will appear when CTFtime publishes them.",
      actionLabel: "View Details",
      isPlaceholder: true,
    };
  }

  return {
    ...baseItem,
    value: latest.rating_points.toFixed(2),
    label: `${latest.year} Rating Points`,
    note: profile.name,
    stats: [
      { value: latest.global_rank === null ? "Unranked" : `#${latest.global_rank}`, label: "Global rank" },
      { value: latest.country_rank === null ? "Unranked" : `#${latest.country_rank}`, label: "Country rank" },
      { value: String(rankings.length), label: "Ranked years" },
      { value: latest.organizer_points.toFixed(2), label: "Organizer points" },
    ],
    trendLabel: "View yearly rating history in CTFtime analytics.",
    actionLabel: "View Details",
  };
}

function buildJourneyItems(platforms: DashboardPlatform[], competitivePlatforms: CompetitivePlatformSummary[], summary: CompetitiveOverviewSummary): JourneyItem[] {
  return [
    buildCompetitiveProgrammingJourney(competitivePlatforms, summary),
    buildCTFJourneyItem(platforms),
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
  const competitiveAccounts = platforms.filter(isSupportedPlatform);

  if (competitiveAccounts.length === 0) {
    steps.push({
      title: "Connect a competitive platform",
      subtitle: "Add Codeforces, AtCoder, or LeetCode progress to the dashboard.",
      icon: Code2,
      accent: "green",
    });
  } else if (competitiveAccounts.some((platform) => !platform.stats)) {
    steps.push({
      title: "Sync competitive data",
      subtitle: "Load real stats for your connected account.",
      icon: RefreshCw,
      accent: "blue",
    });
  }

  if (competitiveAccounts.some((platform) => !platform.is_verified)) {
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
  const supported = platforms.filter(isManagedPlatform);
  if (supported.length === 0) {
    return "Connect a platform to start tracking real progress.";
  }

  const validCount = supported.filter((platform) => platform.handle_validated).length;

  return `Tracking ${supported.length} connected ${pluralize(
    supported.length,
    "platform",
  )} with ${validCount} validated ${pluralize(validCount, "account")}.`;
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
    metrics: buildMetrics(profileCompletion.progress, dashboard.competitive_programming.summary),
    connectedPlatforms: buildConnectedPlatforms(dashboard.platforms),
    journeyItems: buildJourneyItems(dashboard.platforms, dashboard.competitive_programming.platforms, dashboard.competitive_programming.summary),
    profileProgress: profileCompletion.progress,
    profileChecklist: profileCompletion.checklist,
    nextSteps: buildNextSteps(profileCompletion.fields, dashboard.platforms),
  };
}
