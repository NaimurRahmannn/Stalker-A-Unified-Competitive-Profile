"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Box, CheckCircle2, ChevronDown, ClipboardList, Code2, ShieldCheck, Trophy } from "lucide-react";
import type { CompetitiveMetricView, PerformanceSummaryView, PublicPlatformView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";
import { PerformanceSummary } from "./performance-summary";

const tabs = [
  { label: "All Platforms", value: "all" }, { label: "Codeforces", value: "codeforces" },
  { label: "AtCoder", value: "atcoder" }, { label: "LeetCode", value: "leetcode" },
  { label: "CodeChef", value: "codechef" }, { label: "All Submissions", value: "submissions" },
];
const metricIcons = [CheckCircle2, ClipboardList, ShieldCheck, Trophy, Box];
const metricStyles = ["bg-emerald-50 text-emerald-600", "bg-blue-50 text-blue-600", "bg-violet-50 text-violet-600", "bg-orange-50 text-orange-600", "bg-sky-50 text-sky-600"];

function StatsTable({ platforms }: { platforms: PublicPlatformView[] }) {
  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
      <h3 className="px-4 py-4 text-xs font-semibold text-slate-900">Platform Statistics</h3>
      <div className="overflow-x-auto">
        <table className="w-full min-w-190 text-left">
          <thead className="bg-slate-50/80 text-[9px] font-medium text-slate-500"><tr><th className="px-4 py-3">Platform</th><th className="px-3 py-3">Rating / Score</th><th className="px-3 py-3">Max Rating / Score</th><th className="px-3 py-3">Rank</th><th className="px-3 py-3">Problems Solved</th><th className="px-3 py-3">Contests</th><th className="px-4 py-3 text-right">Last Synced</th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {platforms.length ? platforms.map((platform) => (
              <tr key={platform.id} className="text-[11px] text-slate-700">
                <td className="px-4 py-3"><div className="flex items-center gap-2"><ProfilePlatformLogo mark={platform.mark} slug={platform.slug} name={platform.name} size="sm" /><div><p className="font-semibold text-slate-900">{platform.name}</p><p className="mt-0.5 text-[9px] text-slate-500">{platform.handle}</p></div></div></td>
                <td className={`px-3 py-3 font-semibold ${platform.hasDetailedStats ? "text-emerald-600" : "text-slate-400"}`}>{platform.rating}</td>
                <td className="px-3 py-3 font-medium">{platform.maxRating}</td><td className="px-3 py-3 capitalize">{platform.rank}</td><td className="px-3 py-3 font-medium">{platform.solved}</td><td className="px-3 py-3">{platform.contests}</td><td className="px-4 py-3 text-right text-slate-500">{platform.lastSyncedLabel}</td>
              </tr>
            )) : <tr><td colSpan={7} className="px-4 py-12 text-center text-xs text-slate-500">No connected platforms match this filter.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="p-2"><button type="button" disabled className="inline-flex h-9 w-full cursor-not-allowed items-center justify-center gap-3 rounded-lg border border-emerald-200 text-[10px] font-semibold text-emerald-600 opacity-70">View Detailed Analytics <ArrowRight className="size-3.5" /></button></div>
    </div>
  );
}

function CompetitiveCard({ platforms, metrics }: { platforms: PublicPlatformView[]; metrics: CompetitiveMetricView[] }) {
  const [activeTab, setActiveTab] = useState("all");
  const visible = useMemo(() => activeTab === "all" || activeTab === "submissions" ? platforms : platforms.filter((platform) => platform.slug === activeTab), [activeTab, platforms]);
  return (
    <section aria-labelledby="competitive-heading" className="min-w-0 rounded-xl border border-slate-200 bg-white p-5 shadow-[0_10px_32px_rgba(15,23,42,.03)]">
      <div className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Code2 className="size-5" /></span><h2 id="competitive-heading" className="text-[15px] font-semibold text-slate-950">Competitive Programming</h2></div>
      <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div role="tablist" aria-label="Platform statistics filter" className="flex min-w-0 gap-1 overflow-x-auto pb-1">{tabs.map((tab) => <button key={tab.value} type="button" role="tab" aria-selected={activeTab === tab.value} onClick={() => setActiveTab(tab.value)} className={`h-8 shrink-0 rounded-lg px-4 text-[9px] font-medium transition ${activeTab === tab.value ? "bg-emerald-50 text-emerald-700" : "text-slate-600 hover:bg-slate-50"}`}>{tab.label}</button>)}</div>
        <button type="button" className="inline-flex h-8 w-fit shrink-0 items-center gap-2 rounded-lg border border-slate-200 px-3 text-[10px] font-semibold text-slate-700">All Time <ChevronDown className="size-3" /></button>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">{metrics.map((metric, index) => { const Icon = metricIcons[index]; return <div key={metric.label} className="flex min-h-19 items-center gap-3 rounded-xl border border-slate-200 px-3 py-3"><span className={`grid size-9 shrink-0 place-items-center rounded-lg ${metricStyles[index]}`}><Icon className="size-4.5" /></span><div className="min-w-0"><strong className="block truncate text-lg font-bold text-slate-950">{metric.value}</strong><span className="mt-1 block text-[8px] leading-3 text-slate-500">{metric.label}</span></div></div>; })}</div>
      <StatsTable platforms={visible} />
    </section>
  );
}

export function CompetitiveProgrammingSection({ platforms, metrics, performance }: { platforms: PublicPlatformView[]; metrics: CompetitiveMetricView[]; performance: PerformanceSummaryView }) {
  return <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(260px,1fr)]"><CompetitiveCard platforms={platforms} metrics={metrics} /><PerformanceSummary performance={performance} /></div>;
}
