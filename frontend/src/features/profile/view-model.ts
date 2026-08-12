import { Activity, CheckCircle2, CircleDot, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { formatDashboardPlatformName, getPlatformMark } from "@/features/dashboard/data";
import type { MetricAccent, PlatformMark } from "@/features/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";
import type { PublicCodeforcesStats, PublicProfilePlatform, PublicProfileResponse, PublicProfileUser } from "./types";

export type ProfileSocialLink = { label: string; href: string; kind: "github" | "linkedin" };
export type ProfileHeroView = {
  displayName: string; username: string; initials: string; avatarUrl: string | null;
  bio: string | null; country: string | null; institution: string | null; socialLinks: ProfileSocialLink[];
};
export type ProfileMetricView = { label: string; value: string; icon: LucideIcon; accent: MetricAccent };
export type PublicPlatformView = {
  id: number; slug: string; name: string; handle: string; isVerified: boolean;
  mark: PlatformMark | null; profileUrl: string | null; lastSyncedLabel: string;
  rating: string; maxRating: string; rank: string; solved: string; contests: string; hasDetailedStats: boolean;
};
export type CompetitiveMetricView = { label: string; value: string };
export type DomainAccountView = Pick<PublicPlatformView, "id" | "name" | "handle" | "isVerified" | "mark" | "profileUrl">;
export type DomainCardView = { key: "ctf" | "hackathon" | "datathon"; title: string; subtitle: string; accounts: DomainAccountView[] };
export type PerformanceSummaryView = { lastActive: string; memberSince: string };
export type PublicProfileViewModel = {
  hero: ProfileHeroView; summaryMetrics: ProfileMetricView[]; platforms: PublicPlatformView[];
  competitivePlatforms: PublicPlatformView[]; competitiveMetrics: CompetitiveMetricView[];
  domainCards: DomainCardView[]; performance: PerformanceSummaryView;
};

const competitiveSlugs = new Set(["codeforces", "atcoder", "leetcode", "codechef"]);
function hasText(value: string | null | undefined): value is string { return typeof value === "string" && value.trim().length > 0; }
function text(value: string | null | undefined): string | null { return hasText(value) ? value.trim() : null; }
function formatNumber(value: number | null | undefined, fallback = "\u2014") { return value == null ? fallback : new Intl.NumberFormat("en").format(value); }
function formatHandle(handle: string) { return handle.startsWith("@") ? handle : `@${handle}`; }
function validDate(value: string | null | undefined): Date | null { if (!hasText(value)) return null; const date = new Date(value); return Number.isNaN(date.getTime()) ? null : date; }
function relativeDate(value: string | null | undefined, fallback = "Never") { return validDate(value) ? formatRelativeTime(value as string) : fallback; }
function monthYear(value: string | null | undefined, fallback = "\u2014") { const date = validDate(value); return date ? new Intl.DateTimeFormat("en", { month: "short", year: "numeric" }).format(date) : fallback; }
function newestDate(values: Array<string | null | undefined>) { return values.reduce<string | null>((latest, value) => { const date = validDate(value); const current = validDate(latest); return date && (!current || date > current) ? (value as string) : latest; }, null); }
function oldestDate(values: Array<string | null | undefined>) { return values.reduce<string | null>((oldest, value) => { const date = validDate(value); const current = validDate(oldest); return date && (!current || date < current) ? (value as string) : oldest; }, null); }
function initialsFor(user: PublicProfileUser) { const source = text(user.full_name) ?? user.username; const parts = source.split(/\s+/).filter(Boolean); return (parts.length > 1 ? `${parts[0][0]}${parts[1][0]}` : source.slice(0, 2)).toUpperCase(); }

function buildHero(user: PublicProfileUser): ProfileHeroView {
  const socialLinks: ProfileSocialLink[] = [];
  if (hasText(user.github_url)) socialLinks.push({ label: "GitHub", href: user.github_url, kind: "github" });
  if (hasText(user.linkedin_url)) socialLinks.push({ label: "LinkedIn", href: user.linkedin_url, kind: "linkedin" });
  return { displayName: text(user.full_name) ?? user.username, username: user.username, initials: initialsFor(user), avatarUrl: text(user.avatar), bio: text(user.bio), country: text(user.country), institution: text(user.institution), socialLinks };
}

function buildPlatform(platform: PublicProfilePlatform): PublicPlatformView {
  const stats: PublicCodeforcesStats | null = platform.stats;
  return {
    id: platform.id, slug: platform.platform.toLowerCase(), name: formatDashboardPlatformName(platform.platform),
    handle: formatHandle(platform.handle), isVerified: platform.is_verified, mark: getPlatformMark(platform.platform),
    profileUrl: text(platform.profile_url), lastSyncedLabel: relativeDate(platform.last_synced_at),
    rating: formatNumber(stats?.rating, stats ? "Unrated" : "\u2014"),
    maxRating: formatNumber(stats?.max_rating, stats ? "Unrated" : "\u2014"), rank: text(stats?.rank) ?? "\u2014",
    solved: stats ? formatNumber(stats.solved_count) : "\u2014", contests: stats ? formatNumber(stats.contest_count) : "\u2014", hasDetailedStats: Boolean(stats),
  };
}

function sumStats(platforms: PublicProfilePlatform[], key: keyof Pick<PublicCodeforcesStats, "solved_count" | "attempted_count" | "accepted_submission_count" | "contest_count">) {
  const available = platforms.flatMap((platform) => platform.stats ? [platform.stats[key]] : []);
  return available.length ? new Intl.NumberFormat("en").format(available.reduce((total, value) => total + value, 0)) : "\u2014";
}

function buildDomains(platforms: PublicPlatformView[]): DomainCardView[] {
  const select = (slugs: string[]) => platforms.filter((platform) => slugs.includes(platform.slug)).map(({ id, name, handle, isVerified, mark, profileUrl }) => ({ id, name, handle, isVerified, mark, profileUrl }));
  return [
    { key: "ctf", title: "CTF / Cybersecurity", subtitle: "Security platforms and capture-the-flag profiles", accounts: select(["ctftime", "tryhackme", "hackthebox"]) },
    { key: "hackathon", title: "Hackathon", subtitle: "Hackathon profiles and project showcases", accounts: select(["devpost", "dorahacks"]) },
    { key: "datathon", title: "Datathon / Data Science", subtitle: "Data science and competition profiles", accounts: select(["kaggle"]) },
  ];
}

export function buildPublicProfileViewModel(profile: PublicProfileResponse): PublicProfileViewModel {
  const platformViews = profile.platforms.map(buildPlatform);
  const latestSync = newestDate(profile.platforms.map((item) => item.last_synced_at));
  const totalSolved = profile.platforms.reduce((sum, item) => sum + (item.stats?.solved_count ?? 0), 0);
  const lastActive = newestDate(profile.platforms.flatMap((item) => [item.stats?.last_online_at, item.last_synced_at]));
  const memberSince = oldestDate(profile.platforms.flatMap((item) => [item.stats?.registered_at, item.created_at]));
  const competitivePlatforms = platformViews.filter((item) => competitiveSlugs.has(item.slug));
  return {
    hero: buildHero(profile.user),
    summaryMetrics: [
      { label: "Platforms Connected", value: String(profile.platforms.length), icon: CircleDot, accent: "green" },
      { label: "Verified Platforms", value: String(profile.platforms.filter((item) => item.is_verified).length), icon: CheckCircle2, accent: "blue" },
      { label: "Total Problems Solved", value: new Intl.NumberFormat("en").format(totalSolved), icon: Activity, accent: "purple" },
      { label: "Last Synced", value: relativeDate(latestSync), icon: RefreshCw, accent: "orange" },
    ],
    platforms: platformViews, competitivePlatforms,
    competitiveMetrics: [
      { label: "Total Problems Solved", value: sumStats(profile.platforms, "solved_count") },
      { label: "Total Attempted", value: sumStats(profile.platforms, "attempted_count") },
      { label: "Accepted Submissions", value: sumStats(profile.platforms, "accepted_submission_count") },
      { label: "Contests Participated", value: sumStats(profile.platforms, "contest_count") },
      { label: "Platforms Active", value: String(competitivePlatforms.length) },
    ],
    domainCards: buildDomains(platformViews),
    performance: { lastActive: relativeDate(lastActive, "\u2014"), memberSince: monthYear(memberSince) },
  };
}
