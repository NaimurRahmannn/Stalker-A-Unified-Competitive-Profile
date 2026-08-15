import { Activity, CheckCircle2, CircleDot, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { formatDashboardPlatformName, getPlatformMark } from "@/features/dashboard/data";
import type { MetricAccent, PlatformMark } from "@/features/dashboard/types";
import { formatRelativeTime } from "@/lib/utils";
import type { PublicAtCoderStats, PublicCodeforcesStats, PublicProfilePlatform, PublicProfileResponse, PublicProfileUser } from "./types";

export type ProfileSocialLink = { label: string; href: string; kind: "github" | "linkedin" };
export type ProfileHeroView = { displayName: string; username: string; initials: string; avatarUrl: string | null; bio: string | null; country: string | null; institution: string | null; socialLinks: ProfileSocialLink[] };
export type ProfileMetricView = { label: string; value: string; icon: LucideIcon; accent: MetricAccent };
export type PublicPlatformView = { id: number; slug: string; name: string; handle: string; handleValid: boolean; mark: PlatformMark | null; profileUrl: string | null; lastSyncedLabel: string; rating: string; maxRating: string; rank: string; solved: string; contests: string; hasDetailedStats: boolean };
export type CompetitiveMetricView = { label: string; value: string };
export type DomainAccountView = Pick<PublicPlatformView, "id" | "name" | "handle" | "handleValid" | "mark" | "profileUrl">;
export type DomainCardView = { key: "ctf" | "hackathon" | "datathon"; title: string; subtitle: string; accounts: DomainAccountView[] };
export type PerformanceSummaryView = { lastActive: string; memberSince: string };
export type PublicProfileViewModel = { hero: ProfileHeroView; summaryMetrics: ProfileMetricView[]; platforms: PublicPlatformView[]; competitivePlatforms: PublicPlatformView[]; competitiveMetrics: CompetitiveMetricView[]; domainCards: DomainCardView[]; performance: PerformanceSummaryView };

const competitiveSlugs = new Set(["codeforces", "atcoder"]);
function hasText(value: string | null | undefined): value is string { return typeof value === "string" && value.trim().length > 0; }
function text(value: string | null | undefined): string | null { return hasText(value) ? value.trim() : null; }
function formatNumber(value: number | null | undefined, fallback = "—") { return value == null ? fallback : new Intl.NumberFormat("en").format(value); }
function formatHandle(handle: string) { return handle.startsWith("@") ? handle : `@${handle}`; }
function validDate(value: string | null | undefined): Date | null { if (!hasText(value)) return null; const date = new Date(value); return Number.isNaN(date.getTime()) ? null : date; }
function relativeDate(value: string | null | undefined, fallback = "Never") { return validDate(value) ? formatRelativeTime(value as string) : fallback; }
function monthYear(value: string | null | undefined, fallback = "—") { const date = validDate(value); return date ? new Intl.DateTimeFormat("en", { month: "short", year: "numeric" }).format(date) : fallback; }
function newestDate(values: Array<string | null | undefined>) { return values.reduce<string | null>((latest, value) => { const date = validDate(value); const current = validDate(latest); return date && (!current || date > current) ? (value as string) : latest; }, null); }
function oldestDate(values: Array<string | null | undefined>) { return values.reduce<string | null>((oldest, value) => { const date = validDate(value); const current = validDate(oldest); return date && (!current || date < current) ? (value as string) : oldest; }, null); }
function initialsFor(user: PublicProfileUser) { const source = text(user.full_name) ?? user.username; const parts = source.split(/\s+/).filter(Boolean); return (parts.length > 1 ? `${parts[0][0]}${parts[1][0]}` : source.slice(0, 2)).toUpperCase(); }
function isCodeforcesStats(stats: PublicProfilePlatform["stats"]): stats is PublicCodeforcesStats { return stats !== null && "rating" in stats; }
function isAtCoderStats(stats: PublicProfilePlatform["stats"]): stats is PublicAtCoderStats { return stats !== null && "current_rating" in stats; }

function buildHero(user: PublicProfileUser): ProfileHeroView {
  const socialLinks: ProfileSocialLink[] = [];
  if (hasText(user.github_url)) socialLinks.push({ label: "GitHub", href: user.github_url, kind: "github" });
  if (hasText(user.linkedin_url)) socialLinks.push({ label: "LinkedIn", href: user.linkedin_url, kind: "linkedin" });
  return { displayName: text(user.full_name) ?? user.username, username: user.username, initials: initialsFor(user), avatarUrl: text(user.avatar), bio: text(user.bio), country: text(user.country), institution: text(user.institution), socialLinks };
}

function buildPlatform(platform: PublicProfilePlatform): PublicPlatformView {
  const stats = platform.stats;
  const codeforces = isCodeforcesStats(stats) ? stats : null;
  const atcoder = isAtCoderStats(stats) ? stats : null;
  const solved = codeforces ? formatNumber(codeforces.solved_count) : atcoder ? `${formatNumber(atcoder.solved_count)}${atcoder.submission_stats_complete ? "" : " indexed"}` : "—";
  return {
    id: platform.id, slug: platform.platform.toLowerCase(), name: formatDashboardPlatformName(platform.platform), handle: formatHandle(platform.handle), handleValid: platform.handle_validated, mark: getPlatformMark(platform.platform), profileUrl: text(platform.profile_url), lastSyncedLabel: relativeDate(platform.last_synced_at),
    rating: codeforces ? formatNumber(codeforces.rating, "Unrated") : atcoder ? formatNumber(atcoder.current_rating, "Unrated") : "—",
    maxRating: codeforces ? formatNumber(codeforces.max_rating, "Unrated") : atcoder ? formatNumber(atcoder.max_rating, "Unrated") : "—",
    rank: codeforces ? text(codeforces.rank) ?? "Unranked" : atcoder ? atcoder.rating_color ?? "Unrated" : "—",
    solved, contests: codeforces ? formatNumber(codeforces.contest_count) : atcoder ? formatNumber(atcoder.rated_contest_count) : "—", hasDetailedStats: Boolean(stats),
  };
}

function buildDomains(platforms: PublicPlatformView[]): DomainCardView[] {
  const select = (slugs: string[]) => platforms.filter((platform) => slugs.includes(platform.slug)).map(({ id, name, handle, handleValid, mark, profileUrl }) => ({ id, name, handle, handleValid, mark, profileUrl }));
  return [
    { key: "ctf", title: "CTF / Cybersecurity", subtitle: "Security platforms and capture-the-flag profiles", accounts: select(["ctftime", "tryhackme", "hackthebox"]) },
    { key: "hackathon", title: "Hackathon", subtitle: "Hackathon profiles and project showcases", accounts: select(["devpost", "dorahacks"]) },
    { key: "datathon", title: "Datathon / Data Science", subtitle: "Data science and competition profiles", accounts: select(["kaggle"]) },
  ];
}

export function buildPublicProfileViewModel(profile: PublicProfileResponse): PublicProfileViewModel {
  const supportedPlatforms = profile.platforms.filter((item) => competitiveSlugs.has(item.platform));
  const platformViews = supportedPlatforms.map(buildPlatform);
  const summary = profile.competitive_programming.summary;
  const latestSync = newestDate(supportedPlatforms.map((item) => item.last_synced_at));
  const lastActive = newestDate(supportedPlatforms.flatMap((item) => [item.stats?.updated_at, item.last_synced_at]));
  const memberSince = oldestDate(supportedPlatforms.map((item) => item.created_at));
  const competitivePlatforms = platformViews.filter((item) => competitiveSlugs.has(item.slug));
  const solvedLabel = summary.solved_count_complete ? "Total Problems Solved" : "Known Problems Solved";
  return {
    hero: buildHero(profile.user),
    summaryMetrics: [
      { label: "Platforms Connected", value: String(supportedPlatforms.length), icon: CircleDot, accent: "green" },
      { label: "Valid Handles", value: String(supportedPlatforms.filter((item) => item.handle_validated).length), icon: CheckCircle2, accent: "blue" },
      { label: solvedLabel, value: `${formatNumber(summary.solved_count)}${summary.solved_count_complete ? "" : "+"}`, icon: Activity, accent: "purple" },
      { label: "Last Synced", value: relativeDate(latestSync), icon: RefreshCw, accent: "orange" },
    ],
    platforms: platformViews, competitivePlatforms,
    competitiveMetrics: [
      { label: solvedLabel, value: `${formatNumber(summary.solved_count)}${summary.solved_count_complete ? "" : "+"}` },
      { label: summary.accepted_submission_count_complete ? "Accepted Submissions" : "Known Accepted Submissions", value: `${formatNumber(summary.accepted_submission_count)}${summary.accepted_submission_count_complete ? "" : "+"}` },
      { label: "Tracked Contest Participations", value: formatNumber(summary.contest_count) },
      { label: "Platforms Active", value: String(summary.active_platforms) },
    ],
    domainCards: buildDomains(platformViews),
    performance: { lastActive: relativeDate(lastActive, "—"), memberSince: monthYear(memberSince) },
  };
}
