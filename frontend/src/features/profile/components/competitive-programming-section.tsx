"use client";

import { useMemo, useState } from "react";
import type { CompetitiveMetricView, PerformanceSummaryView, PublicPlatformView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";
import { PerformanceSummary } from "./performance-summary";

const filters = [
  { label: "All platforms", value: "all" },
  { label: "Codeforces", value: "codeforces" },
  { label: "AtCoder", value: "atcoder" },
  { label: "LeetCode", value: "leetcode" },
];

function StatsTable({ platforms }: { platforms: PublicPlatformView[] }) {
  return (
    <div className="mt-7 overflow-x-auto border-t border-slate-300">
      <table className="w-full min-w-190 text-left">
        <thead className="border-b border-slate-200 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          <tr>
            <th scope="col" className="py-4 pr-4">Platform</th>
            <th scope="col" className="px-3 py-4">Rating / score</th>
            <th scope="col" className="px-3 py-4">Best</th>
            <th scope="col" className="px-3 py-4">Rank</th>
            <th scope="col" className="px-3 py-4">Solved</th>
            <th scope="col" className="px-3 py-4">Contests</th>
            <th scope="col" className="py-4 pl-3 text-right">Last synced</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {platforms.length ? platforms.map((platform) => (
            <tr key={platform.id} className="text-xs text-slate-600">
              <td className="py-4 pr-4"><div className="flex items-center gap-3"><ProfilePlatformLogo mark={platform.mark} slug={platform.slug} name={platform.name} size="sm" /><div><p className="font-semibold text-[#102c46]">{platform.name}</p><p className="mt-0.5 text-[11px] text-slate-500">{platform.handle}</p></div></div></td>
              <td className="px-3 py-4 font-semibold text-[#1769b0]">{platform.rating}</td>
              <td className="px-3 py-4">{platform.maxRating}</td>
              <td className="px-3 py-4 capitalize">{platform.rank}</td>
              <td className="px-3 py-4 font-medium text-[#102c46]">{platform.solved}</td>
              <td className="px-3 py-4">{platform.contests}</td>
              <td className="py-4 pl-3 text-right">{platform.lastSyncedLabel}</td>
            </tr>
          )) : <tr><td colSpan={7} className="py-9 text-center text-sm text-slate-500">No connected platforms match this filter.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export function CompetitiveProgrammingSection({ platforms, metrics, performance }: { platforms: PublicPlatformView[]; metrics: CompetitiveMetricView[]; performance: PerformanceSummaryView }) {
  const [activeFilter, setActiveFilter] = useState("all");
  const visible = useMemo(() => activeFilter === "all" ? platforms : platforms.filter((platform) => platform.slug === activeFilter), [activeFilter, platforms]);
  return (
    <section aria-labelledby="competitive-heading" className="border-t border-slate-200 py-12 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-[#1769b0]">02 / Performance</p>
          <h2 id="competitive-heading" className="mt-2 text-2xl font-bold tracking-tight text-[#102c46] sm:text-[28px]">Competitive programming</h2>
          <p className="mt-2 text-sm text-slate-500">Ratings, solved problems, and contest history at a glance.</p>
        </div>
        <PerformanceSummary performance={performance} />
      </div>

      <dl className="mt-8 grid grid-cols-2 gap-x-8 gap-y-5 border-y border-slate-200 py-5 sm:grid-cols-4">
        {metrics.map((metric) => <div key={metric.label} className="min-w-0"><dt className="text-xs text-slate-500">{metric.label}</dt><dd className="mt-1 text-xl font-bold tracking-tight text-[#102c46] sm:text-2xl">{metric.value}</dd></div>)}
      </dl>

      <div aria-label="Filter platform statistics" className="mt-8 flex gap-6 overflow-x-auto border-b border-slate-200">
        {filters.map((filter) => <button key={filter.value} type="button" aria-pressed={activeFilter === filter.value} onClick={() => setActiveFilter(filter.value)} className={`shrink-0 border-b-2 pb-3 text-sm font-medium transition ${activeFilter === filter.value ? "border-[#1769b0] text-[#1769b0]" : "border-transparent text-slate-500 hover:text-[#102c46]"}`}>{filter.label}</button>)}
      </div>
      <StatsTable platforms={visible} />
    </section>
  );
}
