import Link from "next/link";
import { BarChart3, Code2, Target, Trophy } from "lucide-react";
import type { CodeforcesAnalyticsResponse } from "../types";
import { codeforcesActivity, codeforcesRatingPoints } from "../adapters";
import { CodeforcesGrowthSummary } from "./codeforces-growth-summary";
import { CodeforcesPerformanceCard } from "./codeforces-performance-card";
import { CompetitiveActivityList } from "./competitive-activity-list";
import { RatingProgressChart } from "./rating-progress-chart";

const metricConfig = [
  { key: "solved", label: "Problems Solved", Icon: Target, style: "bg-emerald-50 text-emerald-600" },
  { key: "contests", label: "Contests", Icon: BarChart3, style: "bg-blue-50 text-blue-600" },
  { key: "rating", label: "Current Rating", Icon: Code2, style: "bg-violet-50 text-violet-600" },
  { key: "max", label: "Max Rating", Icon: Trophy, style: "bg-orange-50 text-orange-600" },
] as const;

export function CodeforcesAnalyticsView({ analytics, onSync, isSyncing, cooldownSeconds }: { analytics: CodeforcesAnalyticsResponse; onSync: () => void; isSyncing: boolean; cooldownSeconds: number }) {
  if (!analytics.account) {
    return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm"><h2 className="text-lg font-semibold text-slate-950">Connect Codeforces to start tracking your progress</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Add your handle, then sync to load rating history, solved problems, contests, and recent submissions.</p><Link href="/platforms" className="mt-6 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white hover:bg-emerald-700">Connect Codeforces</Link></div>;
  }
  const stats = analytics.stats;
  const values = { solved: stats ? String(stats.solved_count) : "—", contests: stats ? String(stats.contest_count) : "—", rating: stats ? (stats.rating === null ? "Unrated" : String(stats.rating)) : "—", max: stats ? (stats.max_rating === null ? "Unrated" : String(stats.max_rating)) : "—" };
  return <>
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{metricConfig.map(({ key, label, Icon, style }) => <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"><div className="flex min-h-16 items-center gap-4"><span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${style}`}><Icon className="size-5" /></span><div className="min-w-0"><strong className="block truncate text-2xl font-semibold text-slate-950">{values[key]}</strong><span className="mt-1 block truncate text-xs font-medium text-slate-600">{label}</span></div></div></article>)}</div>
    <div className="mt-6"><CodeforcesPerformanceCard account={analytics.account} stats={stats} onSync={onSync} isSyncing={isSyncing} cooldownSeconds={cooldownSeconds} /></div>
    <div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]"><div className="min-w-0 space-y-6"><RatingProgressChart points={codeforcesRatingPoints(analytics)} platformName="Codeforces" /><CompetitiveActivityList activity={codeforcesActivity(analytics)} /></div><CodeforcesGrowthSummary account={analytics.account} snapshots={analytics.snapshots} historyCount={analytics.rating_history.length} /></div>
  </>;
}
