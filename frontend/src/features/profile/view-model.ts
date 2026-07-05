import {
  BarChart3,
  BriefcaseBusiness,
  Link2,
  ShieldCheck,
  Trophy,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  formatDashboardPlatformName,
  getPlatformMark,
} from "@/features/dashboard/data";
import type {
  MetricAccent,
  PlatformMark,
  PlatformStatus,
} from "@/features/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";
import type {
  PublicCodeforcesStats,
  PublicProfilePlatform,
  PublicProfileResponse,
  PublicProfileUser,
} from "./types";

export type ProfileSocialLink = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export type ProfileHeroView = {
  displayName: string;
  username: string;
  initials: string;
  avatarUrl: string | null;
  bio: string | null;
  country: string | null;
  institution: string | null;
  socialLinks: ProfileSocialLink[];
};

export type PublicPlatformView = {
  id: number;
  name: string;
  handle: string;
  status: PlatformStatus;
  mark: PlatformMark | null;
  profileUrl: string;
  lastSyncedLabel: string;
};

export type ProfileStatView = {
  label: string;
  value: string;
};

export type CodeforcesSummaryView = {
  state: "not_connected" | "not_synced" | "synced";
  title: string;
  description: string;
  handle: string | null;
  profileUrl: string | null;
  primaryStats: ProfileStatView[];
  detailStats: ProfileStatView[];
};

export type ProfileDomainPlaceholder = {
  title: string;
  label: string;
  icon: LucideIcon;
  accent: MetricAccent;
};

export type PublicProfileViewModel = {
  hero: ProfileHeroView;
  platforms: PublicPlatformView[];
  codeforces: CodeforcesSummaryView;
  domainPlaceholders: ProfileDomainPlaceholder[];
};

function hasText(value: string | null): value is string {
  return value !== null && value.trim().length > 0;
}

function nullableText(value: string | null): string | null {
  return hasText(value) ? value.trim() : null;
}

function formatHandle(handle: string): string {
  return handle.startsWith("@") ? handle : `@${handle}`;
}

function formatNumber(value: number | null, fallback: string): string {
  return value === null ? fallback : String(value);
}

function isCodeforcesPlatform(platform: PublicProfilePlatform): boolean {
  return platform.platform.toLowerCase() === "codeforces";
}

function formatRelativeDateTime(value: string | null, fallback: string): string {
  if (!hasText(value)) {
    return fallback;
  }

  const timestamp = new Date(value).getTime();

  if (Number.isNaN(timestamp)) {
    return "Unknown";
  }

  return formatRelativeTime(value);
}

function formatAbsoluteDate(value: string | null): string | null {
  if (!hasText(value)) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function buildInitials(user: PublicProfileUser): string {
  const source = nullableText(user.full_name) ?? user.username;
  const parts = source.split(/\s+/).filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase();
  }

  return source.slice(0, 2).toUpperCase();
}

function buildHero(user: PublicProfileUser): ProfileHeroView {
  const socialLinks: ProfileSocialLink[] = [];

  if (hasText(user.github_url)) {
    socialLinks.push({
      label: "GitHub",
      href: user.github_url,
      icon: Link2,
    });
  }

  if (hasText(user.linkedin_url)) {
    socialLinks.push({
      label: "LinkedIn",
      href: user.linkedin_url,
      icon: BriefcaseBusiness,
    });
  }

  return {
    displayName: nullableText(user.full_name) ?? user.username,
    username: user.username,
    initials: buildInitials(user),
    avatarUrl: nullableText(user.avatar),
    bio: nullableText(user.bio),
    country: nullableText(user.country),
    institution: nullableText(user.institution),
    socialLinks,
  };
}

function buildPlatformView(platform: PublicProfilePlatform): PublicPlatformView {
  return {
    id: platform.id,
    name: formatDashboardPlatformName(platform.platform),
    handle: formatHandle(platform.handle),
    status: platform.is_verified ? "Verified" : "Unverified",
    mark: getPlatformMark(platform.platform),
    profileUrl: platform.profile_url,
    lastSyncedLabel: formatRelativeDateTime(
      platform.last_synced_at,
      "Never synced",
    ),
  };
}

function buildSyncedCodeforcesSummary(
  platform: PublicProfilePlatform,
  stats: PublicCodeforcesStats,
): CodeforcesSummaryView {
  const detailStats: ProfileStatView[] = [
    {
      label: "Rating",
      value: formatNumber(stats.rating, "Unrated"),
    },
    {
      label: "Max rating",
      value: formatNumber(stats.max_rating, "Unrated"),
    },
    {
      label: "Rank",
      value: stats.rank ?? "Unranked",
    },
    {
      label: "Max rank",
      value: stats.max_rank ?? "Unranked",
    },
    {
      label: "Last synced",
      value: formatRelativeDateTime(platform.last_synced_at, "Never synced"),
    },
  ];
  const lastOnline = formatRelativeDateTime(stats.last_online_at, "");
  const registeredAt = formatAbsoluteDate(stats.registered_at);

  if (lastOnline) {
    detailStats.push({
      label: "Last online",
      value: lastOnline,
    });
  }

  if (registeredAt) {
    detailStats.push({
      label: "Registered",
      value: registeredAt,
    });
  }

  return {
    state: "synced",
    title: "Competitive Programming",
    description: "Real Codeforces stats from the connected account.",
    handle: formatHandle(platform.handle),
    profileUrl: platform.profile_url || null,
    primaryStats: [
      {
        label: "Problems solved",
        value: String(stats.solved_count),
      },
      {
        label: "Attempted",
        value: String(stats.attempted_count),
      },
      {
        label: "Accepted submissions",
        value: String(stats.accepted_submission_count),
      },
      {
        label: "Contests",
        value: String(stats.contest_count),
      },
    ],
    detailStats,
  };
}

function buildCodeforcesSummary(
  platforms: PublicProfilePlatform[],
): CodeforcesSummaryView {
  const codeforcesAccount = platforms.find(isCodeforcesPlatform);

  if (!codeforcesAccount) {
    return {
      state: "not_connected",
      title: "Competitive Programming",
      description: "Codeforces not connected yet",
      handle: null,
      profileUrl: null,
      primaryStats: [],
      detailStats: [],
    };
  }

  if (!codeforcesAccount.stats) {
    return {
      state: "not_synced",
      title: "Competitive Programming",
      description: "Codeforces connected but not synced yet",
      handle: formatHandle(codeforcesAccount.handle),
      profileUrl: codeforcesAccount.profile_url || null,
      primaryStats: [],
      detailStats: [
        {
          label: "Status",
          value: codeforcesAccount.is_verified ? "Verified" : "Unverified",
        },
        {
          label: "Last synced",
          value: formatRelativeDateTime(
            codeforcesAccount.last_synced_at,
            "Never synced",
          ),
        },
      ],
    };
  }

  return buildSyncedCodeforcesSummary(codeforcesAccount, codeforcesAccount.stats);
}

const domainPlaceholders: ProfileDomainPlaceholder[] = [
  {
    title: "CTF",
    label: "Backend support pending",
    icon: ShieldCheck,
    accent: "blue",
  },
  {
    title: "Hackathon",
    label: "No public stats available yet",
    icon: Trophy,
    accent: "purple",
  },
  {
    title: "Datathon",
    label: "Backend support pending",
    icon: BarChart3,
    accent: "orange",
  },
];

export function buildPublicProfileViewModel(
  profile: PublicProfileResponse,
): PublicProfileViewModel {
  return {
    hero: buildHero(profile.user),
    platforms: profile.platforms.map(buildPlatformView),
    codeforces: buildCodeforcesSummary(profile.platforms),
    domainPlaceholders,
  };
}
