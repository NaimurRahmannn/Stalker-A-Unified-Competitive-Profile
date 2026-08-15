import Link from "next/link";
import { BarChart3, Code2, Target, Trophy } from "lucide-react";
import type { AtCoderAnalyticsResponse } from "../types";
import { atcoderActivity, atcoderRatingPoints } from "../adapters";
import { AtCoderPerformanceCard } from "./atcoder-performance-card";
import { AtCoderSyncHealth } from "./atcoder-sync-health";
import { CompetitiveActivityList } from "./competitive-activity-list";
import { RatingProgressChart } from "./rating-progress-chart";

const metrics = [
  { key: "solved", label: "Problems Solved", Icon: Target, style: "bg-emerald-50 text-emerald-600" },
  { key: "contests", label: "Rated Contests", Icon: BarChart3, style: "bg-blue-50 text-blue-600" },
  { key: "rating", label: "Current Rating", Icon: Code2, style: "bg-violet-50 text-violet-600" },
  { key: "max", label: "Max Rating", Icon: Trophy, style: "bg-orange-50 text-orange-600" },
] as const;

export function AtCoderAnalyticsView({ analytics, onSync, isSyncing, cooldownSeconds }: { analytics: AtCoderAnalyticsResponse; onSync: () => void; isSyncing: boolean; cooldownSeconds: number }) {
  if (!analytics.account) {
    return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm"><h2 className="text-lg font-semibold text-slate-950">Connect AtCoder to start tracking your progress</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Add your AtCoder handle, then sync to load Algorithm ratings and indexed submissions.</p><Link href="/platforms" className="mt-6 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white hover:bg-emerald-700">Connect AtCoder</Link></div>;
  }
  const stats = analytics.stats;
  const values = { solved: stats ? `${stats.solved_count}${stats.submission_stats_complete ? "" : "+"}` : "—", contests: stats ? String(stats.rated_contest_count) : "—", rating: stats ? (stats.current_rating === null ? "Unrated" : String(stats.current_rating)) : "—", max: stats ? (stats.max_rating === null ? "Unrated" : String(stats.max_rating)) : "—" };
  return <>
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{metrics.map(({ key, label, Icon, style }) => <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"><div className="flex min-h-16 items-center gap-4"><span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${style}`}><Icon className="size-5" /></span><div className="min-w-0"><strong className="block truncate text-2xl font-semibold text-slate-950">{values[key]}</strong><span className="mt-1 block truncate text-xs font-medium text-slate-600">{label}</span>{key === "solved" && stats && !stats.submission_stats_complete ? <span className="mt-0.5 block text-[9px] text-amber-700">Indexed; history in progress</span> : null}</div></div></article>)}</div>
    <div className="mt-6"><AtCoderSyncHealth sync={analytics.sync} /></div>
    <div className="mt-6"><AtCoderPerformanceCard account={analytics.account} stats={stats} onSync={onSync} isSyncing={isSyncing} cooldownSeconds={cooldownSeconds} /></div>
    <div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]"><div className="min-w-0 space-y-6"><RatingProgressChart points={atcoderRatingPoints(analytics)} platformName="AtCoder" /><CompetitiveActivityList activity={atcoderActivity(analytics)} /></div><aside className="space-y-4"><section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]"><h2 className="text-sm font-semibold text-slate-950">Submission indexing</h2><dl className="mt-4 space-y-3 text-xs"><div className="flex justify-between gap-3"><dt className="text-slate-500">Indexed submissions</dt><dd className="font-semibold text-slate-900">{stats?.indexed_submission_count ?? 0}</dd></div><div className="flex justify-between gap-3"><dt className="text-slate-500">Attempted problems</dt><dd className="font-semibold text-slate-900">{stats ? `${stats.attempted_count}${stats.submission_stats_complete ? "" : "+"}` : "—"}</dd></div><div className="flex justify-between gap-3"><dt className="text-slate-500">Accepted submissions</dt><dd className="font-semibold text-slate-900">{stats ? `${stats.accepted_submission_count}${stats.submission_stats_complete ? "" : "+ indexed"}` : "—"}</dd></div><div className="flex justify-between gap-3"><dt className="text-slate-500">Historical coverage</dt><dd className={`font-semibold ${stats?.submission_stats_complete ? "text-emerald-600" : "text-amber-700"}`}>{stats?.submission_stats_complete ? "Complete" : "In progress"}</dd></div></dl></section></aside></div>
  </>;
}
