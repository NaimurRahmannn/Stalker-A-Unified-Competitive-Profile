import Image from "next/image";
import { CheckCircle2, ExternalLink, RefreshCw, ShieldAlert } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { LeetCodeAnalyticsAccount, LeetCodeStats } from "../types";

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-3"><dt className="text-[10px] font-medium uppercase tracking-[.05em] text-slate-500">{label}</dt><dd className="mt-1 truncate text-base font-semibold capitalize text-slate-950">{value}</dd></div>;
}

export function LeetCodePerformanceCard({ account, stats, onSync, isSyncing, cooldownSeconds }: { account: LeetCodeAnalyticsAccount; stats: LeetCodeStats | null; onSync: () => void; isSyncing: boolean; cooldownSeconds: number }) {
  const disabled = isSyncing || cooldownSeconds > 0 || (!account.can_sync && account.sync_cooldown_seconds === 0);
  const syncLabel = isSyncing ? "Syncing LeetCode..." : cooldownSeconds > 0 ? `Sync available in ${cooldownSeconds}s` : !account.can_sync ? "Sync unavailable" : stats ? "Sync now" : "Run first sync";
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-slate-50 ring-1 ring-slate-100"><Image src="/images/leetcode_logo.png" alt="LeetCode logo" width={34} height={34} className="object-contain" /></span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold text-slate-950">LeetCode Performance</h2>
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${account.handle_validated ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" : "bg-orange-50 text-orange-700 ring-1 ring-orange-200"}`}>{account.handle_validated ? <CheckCircle2 className="size-3" /> : <ShieldAlert className="size-3" />}{account.handle_validated ? "Handle valid" : "Handle not validated"}</span>
            </div>
            {account.profile_url ? <a href={account.profile_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-800">@{account.handle}<ExternalLink className="size-3" /></a> : <p className="mt-1 text-xs font-medium text-slate-500">@{account.handle}</p>}
            <p className="mt-1 text-[10px] text-slate-500">{account.ownership_verified ? "Ownership verified" : "Ownership not verified"}</p>
          </div>
        </div>
        <button type="button" onClick={onSync} disabled={disabled} className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"><RefreshCw className={`size-4 ${isSyncing ? "animate-spin" : ""}`} />{syncLabel}</button>
      </div>
      {stats ? <>
        <dl className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-7">
          <Stat label="Contest rating" value={stats.current_contest_rating === null ? "Unrated" : String(Math.round(stats.current_contest_rating))} />
          <Stat label="Total solved" value={String(stats.solved_total)} />
          <Stat label="Easy" value={String(stats.solved_easy)} />
          <Stat label="Medium" value={String(stats.solved_medium)} />
          <Stat label="Hard" value={String(stats.solved_hard)} />
          <Stat label="Contests" value={String(stats.attended_contest_count)} />
          {stats.contest_top_percentage !== null ? <Stat label="Top %" value={`${stats.contest_top_percentage.toFixed(1)}%`} /> : <Stat label="Global rank" value={stats.global_problem_ranking !== null ? `#${new Intl.NumberFormat("en").format(stats.global_problem_ranking)}` : "—"} />}
        </dl>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-100 pt-4 text-[11px] text-slate-500">
          {stats.global_problem_ranking !== null ? <span>Global problem ranking <strong className="font-semibold text-slate-800">#{new Intl.NumberFormat("en").format(stats.global_problem_ranking)}</strong></span> : null}
          <span>Last synced <strong className="font-semibold text-slate-800">{account.last_synced_at ? formatRelativeTime(account.last_synced_at) : "Never"}</strong></span>
          {stats.data_updated_at ? <span>Data updated <strong className="font-semibold text-slate-800">{formatRelativeTime(stats.data_updated_at)}</strong></span> : null}
        </div>
      </> : <div className="mt-5 rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 px-5 py-5"><p className="text-sm font-semibold text-emerald-800">LeetCode is connected and ready to sync</p><p className="mt-1 text-xs leading-5 text-emerald-700/80">Run the first sync to verify @{account.handle} and load real problem statistics, contest data, and rating history.</p></div>}
    </section>
  );
}
