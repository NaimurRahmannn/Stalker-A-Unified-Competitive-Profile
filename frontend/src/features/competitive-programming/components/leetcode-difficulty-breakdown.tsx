import { BarChart3 } from "lucide-react";
import type { LeetCodeStats } from "../types";

function DifficultyRow({ label, count, total, color, bgColor }: { label: string; count: number; total: number; color: string; bgColor: string }) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-500">{label}</span>
        <span className="font-semibold text-slate-900">{count}</span>
      </div>
      <div className={`h-2 w-full overflow-hidden rounded-full ${bgColor}`}>
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

export function LeetCodeDifficultyBreakdown({ stats }: { stats: LeetCodeStats | null }) {
  if (!stats) {
    return (
      <aside className="grid gap-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
          <div className="flex items-center gap-2"><BarChart3 className="size-4.5 text-amber-600" /><h2 className="text-sm font-semibold text-slate-950">Difficulty Breakdown</h2></div>
          <p className="mt-4 rounded-xl bg-slate-50 px-4 py-5 text-xs leading-5 text-slate-500">Sync LeetCode to see your difficulty breakdown.</p>
        </section>
      </aside>
    );
  }

  const total = stats.solved_total;

  return (
    <aside className="grid gap-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
        <div className="flex items-center gap-2"><BarChart3 className="size-4.5 text-amber-600" /><h2 className="text-sm font-semibold text-slate-950">Difficulty Breakdown</h2></div>
        <dl className="mt-4 grid gap-4">
          <DifficultyRow label="Easy" count={stats.solved_easy} total={total} color="bg-emerald-500" bgColor="bg-emerald-100" />
          <DifficultyRow label="Medium" count={stats.solved_medium} total={total} color="bg-amber-500" bgColor="bg-amber-100" />
          <DifficultyRow label="Hard" count={stats.solved_hard} total={total} color="bg-red-500" bgColor="bg-red-100" />
        </dl>
        <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4 text-xs">
          <span className="text-slate-500">Total solved</span>
          <strong className="text-lg font-bold text-slate-950">{total}</strong>
        </div>
        {!stats.problem_stats_complete ? (
          <p className="mt-2 text-[9px] text-amber-700">Problem statistics may be incomplete.</p>
        ) : null}
      </section>

      {stats.contest_global_ranking !== null || stats.contest_top_percentage !== null ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
          <div className="flex items-center gap-2"><BarChart3 className="size-4.5 text-blue-600" /><h2 className="text-sm font-semibold text-slate-950">Contest Standing</h2></div>
          <div className="mt-4 space-y-3 text-xs">
            {stats.contest_global_ranking !== null ? (
              <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-3">
                <span className="text-slate-500">Global ranking</span>
                <strong className="text-slate-800">#{new Intl.NumberFormat("en").format(stats.contest_global_ranking)}</strong>
              </div>
            ) : null}
            {stats.contest_top_percentage !== null ? (
              <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-3">
                <span className="text-slate-500">Top percentage</span>
                <strong className="text-emerald-600">{stats.contest_top_percentage.toFixed(1)}%</strong>
              </div>
            ) : null}
            {stats.contest_total_participants !== null ? (
              <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-3">
                <span className="text-slate-500">Total participants</span>
                <strong className="text-slate-800">{new Intl.NumberFormat("en").format(stats.contest_total_participants)}</strong>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </aside>
  );
}
