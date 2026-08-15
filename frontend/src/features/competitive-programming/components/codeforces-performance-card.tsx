import Image from "next/image";
import { CheckCircle2, ExternalLink, RefreshCw, ShieldAlert } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { CodeforcesAnalyticsAccount } from "../types";
import type { CodeforcesStats } from "@/features/platforms/types";

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-3"><dt className="text-[10px] font-medium uppercase tracking-[.05em] text-slate-500">{label}</dt><dd className="mt-1 truncate text-base font-semibold capitalize text-slate-950">{value}</dd></div>;
}

export function CodeforcesPerformanceCard({ account, stats, onSync, isSyncing, cooldownSeconds }: { account: CodeforcesAnalyticsAccount; stats: CodeforcesStats | null; onSync: () => void; isSyncing: boolean; cooldownSeconds: number }) {
  const disabled = isSyncing || cooldownSeconds > 0 || (!account.can_sync && account.sync_cooldown_seconds === 0);
  const syncLabel = isSyncing ? "Syncing Codeforces..." : cooldownSeconds > 0 ? `Sync available in ${cooldownSeconds}s` : !account.can_sync ? "Sync unavailable" : stats ? "Sync now" : "Run first sync";
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-center gap-3"><span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-slate-50 ring-1 ring-slate-100"><Image src="/images/codeforces_logo.png" alt="Codeforces logo" width={34} height={34} className="object-contain" /></span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 className="text-base font-semibold text-slate-950">Codeforces Performance</h2><span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${account.handle_validated ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" : "bg-orange-50 text-orange-700 ring-1 ring-orange-200"}`}>{account.handle_validated ? <CheckCircle2 className="size-3" /> : <ShieldAlert className="size-3" />}{account.handle_validated ? "Handle valid" : "Handle not validated"}</span></div>{account.profile_url ? <a href={account.profile_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-800">@{account.handle}<ExternalLink className="size-3" /></a> : <p className="mt-1 text-xs font-medium text-slate-500">@{account.handle}</p>}<p className="mt-1 text-[10px] text-slate-500">{account.ownership_verified ? "Ownership verified" : "Ownership not verified"}</p></div></div>
        <button type="button" onClick={onSync} disabled={disabled} className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"><RefreshCw className={`size-4 ${isSyncing ? "animate-spin" : ""}`} />{syncLabel}</button>
      </div>
      {stats ? <><dl className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6"><Stat label="Current rating" value={stats.rating === null ? "Unrated" : String(stats.rating)} /><Stat label="Max rating" value={stats.max_rating === null ? "Unrated" : String(stats.max_rating)} /><Stat label="Rank" value={stats.rank ?? "Unranked"} /><Stat label="Solved" value={String(stats.solved_count)} /><Stat label="Attempted" value={String(stats.attempted_count)} /><Stat label="Contests" value={String(stats.contest_count)} /></dl><div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-100 pt-4 text-[11px] text-slate-500"><span>Accepted submissions <strong className="font-semibold text-slate-800">{stats.accepted_submission_count}</strong></span><span>Last synced <strong className="font-semibold text-slate-800">{account.last_synced_at ? formatRelativeTime(account.last_synced_at) : "Never"}</strong></span></div></> : <div className="mt-5 rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 px-5 py-5"><p className="text-sm font-semibold text-emerald-800">Codeforces is connected and ready to sync</p><p className="mt-1 text-xs leading-5 text-emerald-700/80">Run the first sync to verify @{account.handle} and load real rating, contest, problem, and submission data.</p></div>}
    </section>
  );
}
