import { Activity, CheckCircle2, CircleDot, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { formatDashboardPlatformName, getPlatformMark } from "@/features/dashboard/data";
import type { MetricAccent, PlatformMark } from "@/features/dashboard/types";
import type { CTFTeamProfile } from "@/features/platforms/types";
import type { KaggleOverviewResponse } from "@/features/datathons/types";
import { formatTier } from "@/features/datathons/formatters";
import { formatRelativeTime } from "@/lib/utils";
import type { PublicAtCoderStats, PublicCodeforcesStats, PublicHackathonSummary, PublicKaggleStats, PublicLeetCodeStats, PublicProfilePlatform, PublicProfileResponse, PublicProfileUser } from "./types";

export type ProfileSocialLink = { label: string; href: string; kind: "github" | "linkedin" };
export type ProfileHeroView = { displayName: string; username: string; initials: string; avatarUrl: string | null; bio: string | null; country: string | null; institution: string | null; socialLinks: ProfileSocialLink[] };
export type ProfileMetricView = { label: string; value: string; icon: LucideIcon; accent: MetricAccent };
export type PublicPlatformView = { id: number; slug: string; name: string; handle: string; handleValid: boolean; mark: PlatformMark | null; profileUrl: string | null; lastSyncedLabel: string; rating: string; ratingLabel?: string; maxRating: string; rank: string; solved: string; contests: string; hasDetailedStats: boolean };
export type CompetitiveMetricView = { label: string; value: string };
export type DomainAccountView = Pick<PublicPlatformView, "id" | "name" | "handle" | "handleValid" | "mark" | "profileUrl" | "rating" | "rank" | "contests" | "solved">;
export type DomainCardView = { key: "ctf" | "hackathon" | "datathon"; title: string; subtitle: string; accounts: DomainAccountView[]; metrics?: Array<{ label: string; value: string }> };
export type PerformanceSummaryView = { lastActive: string; memberSince: string };
export type PublicProfileViewModel = { hero: ProfileHeroView; summaryMetrics: ProfileMetricView[]; platforms: PublicPlatformView[]; competitivePlatforms: PublicPlatformView[]; competitiveMetrics: CompetitiveMetricView[]; domainCards: DomainCardView[]; performance: PerformanceSummaryView };

const competitiveSlugs = new Set(["codeforces", "atcoder", "leetcode"]);
const TIER_ORDER: Record<string, number> = {
  grandmaster: 5,
  master: 4,
  expert: 3,
  contributor: 2,
  novice: 1,
};

function parseTier(value: string | null | undefined): string | null {
  if (!value || value === "Not available") return null;
  const formatted = formatTier(value);
  return formatted === "Not available" ? null : formatted;
}
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
function isLeetCodeStats(stats: PublicProfilePlatform["stats"]): stats is PublicLeetCodeStats { return stats !== null && "solved_total" in stats; }
function isCTFTeamProfile(stats: PublicProfilePlatform["stats"]): stats is CTFTeamProfile { return stats !== null && "yearly_rankings" in stats; }
function isKaggleStats(stats: PublicProfilePlatform["stats"]): stats is PublicKaggleStats { return stats !== null && "competitions_tier" in stats; }

function buildHero(user: PublicProfileUser): ProfileHeroView {
  const socialLinks: ProfileSocialLink[] = [];
  if (hasText(user.github_url)) socialLinks.push({ label: "GitHub", href: user.github_url, kind: "github" });
  if (hasText(user.linkedin_url)) socialLinks.push({ label: "LinkedIn", href: user.linkedin_url, kind: "linkedin" });
  return { displayName: text(user.full_name) ?? user.username, username: user.username, initials: initialsFor(user), avatarUrl: text(user.avatar), bio: text(user.bio), country: text(user.country), institution: text(user.institution), socialLinks };
}

function buildPlatform(platform: PublicProfilePlatform): PublicPlatformView {
  const stats = platform.stats;
  const isKaggle = platform.platform.toLowerCase() === "kaggle";
  const codeforces = isCodeforcesStats(stats) ? stats : null;
  const atcoder = isAtCoderStats(stats) ? stats : null;
  const leetcode = isLeetCodeStats(stats) ? stats : null;
  const ctftime = isCTFTeamProfile(stats) ? stats : null;
  const kaggle = isKaggleStats(stats) ? stats : null;
  const latestCTFRanking = ctftime?.yearly_rankings[0];

  let kaggleBestTier: string | null = null;
  let kaggleBestTierTrack = "Comp";
  if (kaggle) {
    const trackTiers = [
      { track: "Comp", tier: kaggle.competitions_tier },
      { track: "Code", tier: kaggle.code_tier },
      { track: "Data", tier: kaggle.datasets_tier },
    ].filter((t) => t.tier);
    trackTiers.sort((a, b) => (TIER_ORDER[b.tier!.toLowerCase()] ?? 0) - (TIER_ORDER[a.tier!.toLowerCase()] ?? 0));
    if (trackTiers[0]) {
      kaggleBestTier = parseTier(trackTiers[0].tier);
      kaggleBestTierTrack = trackTiers[0].track;
    }
  }

  let kaggleBestRank: { track: string; rank: number } | null = null;
  if (kaggle) {
    const ranks = [
      kaggle.competitions_rank ? { track: "Comp", rank: kaggle.competitions_rank } : null,
      kaggle.code_rank ? { track: "Code", rank: kaggle.code_rank } : null,
      kaggle.datasets_rank ? { track: "Data", rank: kaggle.datasets_rank } : null,
    ].filter(Boolean) as Array<{ track: string; rank: number }>;
    ranks.sort((a, b) => a.rank - b.rank);
    if (ranks[0]) kaggleBestRank = ranks[0];
  }

  const activeKaggleTracks = kaggle
    ? [
        kaggle.competitions_rank || kaggle.competitions_tier,
        kaggle.code_rank || kaggle.code_tier,
        kaggle.datasets_rank || kaggle.datasets_tier,
      ].filter(Boolean).length
    : 0;

  const solved = codeforces
    ? formatNumber(codeforces.solved_count)
    : atcoder
    ? `${formatNumber(atcoder.solved_count)}${atcoder.submission_stats_complete ? "" : " indexed"}`
    : leetcode
    ? formatNumber(leetcode.solved_total)
    : ctftime
    ? `${ctftime.yearly_rankings.length} ranked ${ctftime.yearly_rankings.length === 1 ? "year" : "years"}`
    : isKaggle
    ? kaggle && kaggle.total_medals > 0
      ? `${kaggle.total_medals} ${kaggle.total_medals === 1 ? "medal" : "medals"}`
      : activeKaggleTracks > 0
      ? `${activeKaggleTracks} ${activeKaggleTracks === 1 ? "track" : "tracks"} active`
      : "—"
    : "—";

  return {
    id: platform.id,
    slug: platform.platform.toLowerCase(),
    name: formatDashboardPlatformName(platform.platform),
    handle: platform.platform === "ctftime" ? `Team #${platform.handle}` : formatHandle(platform.handle),
    handleValid: isKaggle ? true : platform.handle_validated,
    mark: getPlatformMark(platform.platform),
    profileUrl: text(platform.profile_url),
    lastSyncedLabel: relativeDate(platform.last_synced_at),
    rating: codeforces
      ? formatNumber(codeforces.rating, "Unrated")
      : atcoder
      ? formatNumber(atcoder.current_rating, "Unrated")
      : leetcode
      ? (leetcode.current_contest_rating === null ? "Unrated" : formatNumber(Math.round(leetcode.current_contest_rating)))
      : latestCTFRanking
      ? formatNumber(latestCTFRanking.rating_points)
      : isKaggle
      ? (kaggleBestTier ?? (kaggleBestRank ? `#${formatNumber(kaggleBestRank.rank)}` : (kaggle?.total_medals ? `${kaggle.total_medals} medals` : "—")))
      : "—",
    ratingLabel: isKaggle ? (kaggleBestTier ? "Tier" : (kaggleBestRank ? "Rank" : "Rating")) : "Rating",
    maxRating: codeforces
      ? formatNumber(codeforces.max_rating, "Unrated")
      : atcoder
      ? formatNumber(atcoder.max_rating, "Unrated")
      : leetcode
      ? (leetcode.current_contest_rating === null ? "Unrated" : formatNumber(Math.round(leetcode.current_contest_rating)))
      : isKaggle
      ? (kaggleBestTier ?? "—")
      : "—",
    rank: codeforces
      ? text(codeforces.rank) ?? "Unranked"
      : atcoder
      ? atcoder.rating_color ?? "Unrated"
      : leetcode
      ? (leetcode.contest_top_percentage !== null ? `Top ${leetcode.contest_top_percentage.toFixed(1)}%` : "—")
      : latestCTFRanking
      ? (latestCTFRanking.global_rank === null ? "Unranked" : `#${latestCTFRanking.global_rank} global`)
      : isKaggle
      ? (kaggleBestRank ? `#${formatNumber(kaggleBestRank.rank)} ${kaggleBestRank.track}` : (kaggleBestTier ?? "Linked"))
      : "—",
    solved,
    contests: codeforces
      ? formatNumber(codeforces.contest_count)
      : atcoder
      ? formatNumber(atcoder.rated_contest_count)
      : leetcode
      ? formatNumber(leetcode.attended_contest_count)
      : ctftime
      ? String(ctftime.yearly_rankings.length)
      : isKaggle
      ? (kaggleBestRank ? `#${formatNumber(kaggleBestRank.rank)}` : "—")
      : "—",
    hasDetailedStats: Boolean(stats && (isKaggle ? kaggle?.has_data : true)),
  };
}

function buildDomains(platforms: PublicPlatformView[], hackathons: PublicHackathonSummary, datathons?: KaggleOverviewResponse | null): DomainCardView[] {
  const select = (slugs: string[]) => platforms.filter((platform) => slugs.includes(platform.slug)).map(({ id, name, handle, handleValid, mark, profileUrl, rating, rank, contests, solved }) => ({ id, name, handle, handleValid, mark, profileUrl, rating, rank, contests, solved }));
  const kaggleAccount = select(["kaggle"])[0];
  const summary = datathons?.summary;
  const manual = datathons?.manual_tracks ?? { competitions: null, code: null, datasets: null };
  const tracks = datathons?.tracks ?? { competitions: null, code: null, datasets: null };

  const comp = manual.competitions ?? tracks.competitions;
  const code = manual.code ?? tracks.code;
  const datasets = manual.datasets ?? tracks.datasets;

  const compRank = comp?.global_rank ?? summary?.competitions_rank;
  const compTier = parseTier(comp?.tier) ?? parseTier(summary?.competitions_tier);
  const codeRank = code?.global_rank ?? summary?.code_rank;
  const codeTier = parseTier(code?.tier) ?? parseTier(summary?.code_tier);
  const datasetsRank = datasets?.global_rank ?? summary?.datasets_rank;
  const datasetsTier = parseTier(datasets?.tier) ?? parseTier(summary?.datasets_tier);
  const totalMedals = summary?.total_medals ?? 0;

  const tierCandidates = [
    { track: "Comp", tier: compTier },
    { track: "Code", tier: codeTier },
    { track: "Data", tier: datasetsTier },
  ].filter((t) => t.tier);
  tierCandidates.sort((a, b) => (TIER_ORDER[b.tier!.toLowerCase()] ?? 0) - (TIER_ORDER[a.tier!.toLowerCase()] ?? 0));
  const bestTier = tierCandidates[0]?.tier ?? (kaggleAccount?.rating && kaggleAccount.rating !== "—" ? kaggleAccount.rating : null);

  let bestRankLabel = "Rank";
  let bestRankValue = "—";
  if (compRank != null) {
    bestRankLabel = "Comp Rank";
    bestRankValue = `#${formatNumber(compRank)}`;
  } else if (codeRank != null) {
    bestRankLabel = "Code Rank";
    bestRankValue = `#${formatNumber(codeRank)}`;
  } else if (datasetsRank != null) {
    bestRankLabel = "Data Rank";
    bestRankValue = `#${formatNumber(datasetsRank)}`;
  } else if (kaggleAccount?.contests && kaggleAccount.contests !== "—") {
    bestRankLabel = "Rank";
    bestRankValue = kaggleAccount.contests;
  }

  return [
    { key: "ctf", title: "CTF / Cybersecurity", subtitle: "Security platforms and capture-the-flag profiles", accounts: select(["ctftime", "tryhackme", "hackthebox"]) },
    { key: "hackathon", title: "Hackathon", subtitle: "Hackathon profiles and project showcases", accounts: select(["devpost", "dorahacks"]), metrics: [
      { label: "Projects", value: String(hackathons.published_projects) },
      { label: "Events", value: String(hackathons.public_participations) },
      { label: "Achievements", value: String(hackathons.public_achievements) },
    ] },
    { key: "datathon", title: "Datathon / Data Science", subtitle: "Data science and competition profiles", accounts: select(["kaggle"]), metrics: [
      { label: "Best Tier", value: bestTier ?? "—" },
      { label: bestRankLabel, value: bestRankValue },
      { label: "Medals", value: String(totalMedals) },
    ] },
  ];
}

export function buildPublicProfileViewModel(profile: PublicProfileResponse): PublicProfileViewModel {
  const supportedPlatforms = profile.platforms.filter((item) => competitiveSlugs.has(item.platform) || ["ctftime", "devpost", "dorahacks", "kaggle"].includes(item.platform));
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
      { label: "Validated Accounts", value: String(supportedPlatforms.filter((item) => item.handle_validated).length), icon: CheckCircle2, accent: "blue" },
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
    domainCards: buildDomains(platformViews, profile.hackathons, profile.datathons),
    performance: { lastActive: relativeDate(lastActive, "—"), memberSince: monthYear(memberSince) },
  };
}
