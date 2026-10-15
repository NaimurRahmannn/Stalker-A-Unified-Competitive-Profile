import Image from "next/image";
import Link from "next/link";
import { CheckCircle2, ExternalLink, History, RefreshCw, ShieldAlert, TrendingUp } from "lucide-react";
import type { CTFYearlyRanking, PlatformAccount } from "@/features/platforms/types";
import { formatRelativeTime } from "@/lib/utils";

function TeamPerformanceCard({ account, onSync, isSyncing, cooldownSeconds }: {
  account: PlatformAccount;
  onSync: () => void;
  isSyncing: boolean;
  cooldownSeconds: number;
}) {
  const profile = account.ctf_team_profile;
  const unavailable = !account.can_sync && account.sync_cooldown_seconds === 0;
  const disabled = isSyncing || cooldownSeconds > 0 || unavailable;
  const syncLabel = isSyncing ? "Syncing CTFtime..." : cooldownSeconds > 0
    ? `Sync available in ${cooldownSeconds}s`
    : unavailable ? "Sync unavailable" : profile ? "Sync now" : "Run first sync";

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-slate-50 ring-1 ring-slate-100">
            <Image src="/images/ctf_time.png" alt="CTFtime logo" width={34} height={34} className="size-8 object-contain" />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-semibold text-slate-950">CTFtime Performance</h2>
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${account.handle_validated ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" : "bg-orange-50 text-orange-700 ring-1 ring-orange-200"}`}>
                {account.handle_validated ? <CheckCircle2 className="size-3" /> : <ShieldAlert className="size-3" />}
                {account.handle_validated ? "Team found" : "Team not validated"}
              </span>
            </div>
            {account.profile_url ? (
              <a href={account.profile_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-blue-700 hover:text-blue-800">
                Team #{account.handle} <ExternalLink className="size-3" />
              </a>
            ) : <p className="mt-1 text-xs font-medium text-slate-500">Team #{account.handle}</p>}
            {profile ? <p className="mt-1 truncate text-[10px] text-slate-500">{profile.name}{profile.country ? ` · ${profile.country}` : ""}</p> : null}
          </div>
        </div>
        <button type="button" onClick={onSync} disabled={disabled} className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300">
          <RefreshCw className={`size-4 ${isSyncing ? "animate-spin" : ""}`} />{syncLabel}
        </button>
      </div>
      {profile ? (
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-100 pt-4 text-[11px] text-slate-500">
          <span>Ranked years <strong className="font-semibold text-slate-800">{profile.yearly_rankings.length}</strong></span>
          <span>Last synced <strong className="font-semibold text-slate-800">{account.last_synced_at ? formatRelativeTime(account.last_synced_at) : "Never"}</strong></span>
          {profile.data_updated_at ? <span>CTFtime data updated <strong className="font-semibold text-slate-800">{formatRelativeTime(profile.data_updated_at)}</strong></span> : null}
        </div>
      ) : (
        <div className="mt-5 rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 px-5 py-5">
          <p className="text-sm font-semibold text-emerald-800">CTFtime is connected and ready to sync</p>
          <p className="mt-1 text-xs leading-5 text-emerald-700/80">Run the first sync to find team #{account.handle} and load its yearly rankings.</p>
        </div>
      )}
    </section>
  );
}

function YearlyRatingChart({ rankings }: { rankings: CTFYearlyRanking[] }) {
  const history = [...rankings].sort((a, b) => a.year - b.year);
  if (!history.length) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
        <div className="flex items-center gap-2"><TrendingUp className="size-4.5 text-emerald-600" /><h2 className="text-sm font-semibold text-slate-950">Rating Progress</h2></div>
        <div className="mt-4 grid min-h-64 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center">
          <div><p className="text-sm font-semibold text-slate-800">No yearly ratings yet</p><p className="mt-1 text-xs leading-5 text-slate-500">CTFtime ratings will appear here when this team has a ranked year.</p></div>
        </div>
      </section>
    );
  }

  const width = 760;
  const height = 300;
  const left = 52;
  const right = 24;
  const top = 28;
  const bottom = 42;
  const ratings = history.map((item) => item.rating_points);
  const rawMin = Math.min(...ratings);
  const rawMax = Math.max(...ratings);
  const range = Math.max(100, rawMax - rawMin);
  const min = Math.max(0, Math.floor((rawMin - range * 0.15) / 100) * 100);
  const max = Math.ceil((rawMax + range * 0.15) / 100) * 100;
  const xFor = (index: number) => history.length === 1 ? left + (width - left - right) / 2 : left + (index / (history.length - 1)) * (width - left - right);
  const yFor = (rating: number) => top + ((max - rating) / Math.max(1, max - min)) * (height - top - bottom);
  const linePoints = history.map((item, index) => `${xFor(index)},${yFor(item.rating_points)}`).join(" ");
  const areaPoints = `${xFor(0)},${height - bottom} ${linePoints} ${xFor(history.length - 1)},${height - bottom}`;
  const gridValues = Array.from({ length: 5 }, (_, index) => Math.round(max - ((max - min) / 4) * index));
  const yearLabels = Array.from(new Set([0, Math.floor((history.length - 1) / 2), history.length - 1]));

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2"><TrendingUp className="size-4.5 text-emerald-600" /><h2 className="text-sm font-semibold text-slate-950">Rating Progress</h2></div>
        <p className="text-[11px] font-medium text-slate-500">{history.length} ranked {history.length === 1 ? "year" : "years"}</p>
      </div>
      <div className="mt-4 overflow-hidden rounded-xl border border-slate-100 bg-[linear-gradient(to_bottom,#ffffff,#f8fafc)] p-2">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`CTFtime rating points across ${history.length} ranked years`} className="h-auto min-h-64 w-full">
          <defs><linearGradient id="ctf-rating-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#10b981" stopOpacity=".2" /><stop offset="1" stopColor="#10b981" stopOpacity="0" /></linearGradient></defs>
          {gridValues.map((value, index) => <g key={index}><line x1={left} x2={width - right} y1={yFor(value)} y2={yFor(value)} stroke="#e2e8f0" strokeDasharray="4 5" /><text x={left - 10} y={yFor(value) + 4} textAnchor="end" className="fill-slate-400 text-[10px]">{value}</text></g>)}
          <polygon points={areaPoints} fill="url(#ctf-rating-area)" />
          <polyline points={linePoints} fill="none" stroke="#059669" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          {history.map((item, index) => <circle key={item.year} cx={xFor(index)} cy={yFor(item.rating_points)} r={history.length === 1 ? 6 : 4} fill="#fff" stroke="#059669" strokeWidth="3"><title>{`${item.year}: ${item.rating_points.toFixed(2)} rating points`}</title></circle>)}
          {yearLabels.map((index) => <text key={index} x={xFor(index)} y={height - 15} textAnchor={index === 0 ? "start" : index === history.length - 1 ? "end" : "middle"} className="fill-slate-400 text-[10px]">{history[index].year}</text>)}
        </svg>
      </div>
      <p className="mt-3 text-[11px] text-slate-500">Hover a point to see that year&apos;s rating.</p>
    </section>
  );
}

function SyncSummary({ account }: { account: PlatformAccount }) {
  const state = account.ctftime_sync_state;
  const entries = [
    { label: "Sync status", value: state?.status ? state.status.charAt(0).toUpperCase() + state.status.slice(1) : "Never synced" },
    { label: "Last attempt", value: state?.last_attempted_at ? formatRelativeTime(state.last_attempted_at) : "Never" },
    { label: "Last success", value: state?.last_successful_at ? formatRelativeTime(state.last_successful_at) : "Never" },
    { label: "Team country", value: account.ctf_team_profile?.country ?? "Not available" },
  ];
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-2"><History className="size-4.5 text-blue-600" /><h2 className="text-sm font-semibold text-slate-950">Team and Sync</h2></div>
      <dl className="mt-4 divide-y divide-slate-100">
        {entries.map(({ label, value }) => <div key={label} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"><dt className="text-xs text-slate-500">{label}</dt><dd className="text-right text-xs font-semibold text-slate-900">{value}</dd></div>)}
      </dl>
    </section>
  );
}

function YearlyRankingsTable({ rankings }: { rankings: CTFYearlyRanking[] }) {
  const sorted = [...rankings].sort((a, b) => b.year - a.year);
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h2 className="text-sm font-semibold text-slate-950">Yearly Rankings</h2>
      {sorted.length ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-130 text-left text-xs">
            <thead className="border-b border-slate-200 text-slate-500"><tr><th className="pb-3 font-semibold">Year</th><th className="pb-3 font-semibold">Global rank</th><th className="pb-3 font-semibold">Country rank</th><th className="pb-3 font-semibold">Rating points</th><th className="pb-3 font-semibold">Organizer points</th></tr></thead>
            <tbody>{sorted.map((ranking) => <tr key={ranking.year} className="border-b border-slate-100 last:border-0"><td className="py-3 font-semibold text-slate-900">{ranking.year}</td><td className="py-3">{ranking.global_rank === null ? "—" : `#${ranking.global_rank}`}</td><td className="py-3">{ranking.country_rank === null ? "—" : `#${ranking.country_rank}`}</td><td className="py-3">{ranking.rating_points.toFixed(2)}</td><td className="py-3">{ranking.organizer_points.toFixed(2)}</td></tr>)}</tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 grid min-h-36 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center"><div><p className="text-sm font-semibold text-slate-800">No yearly rankings yet</p><p className="mt-1 text-xs text-slate-500">Rankings will appear when CTFtime publishes them for this team.</p></div></div>
      )}
    </section>
  );
}

export function CTFtimeAnalyticsView({ account, onSync, isSyncing, cooldownSeconds }: {
  account: PlatformAccount | null;
  onSync: () => void;
  isSyncing: boolean;
  cooldownSeconds: number;
}) {
  if (!account) {
    return <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm"><h2 className="text-lg font-semibold text-slate-950">Connect CTFtime to start tracking your team</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Add your numeric team ID, then sync to load the team profile and yearly rankings.</p><Link href="/platforms" className="mt-6 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white hover:bg-emerald-700">Connect CTFtime</Link></div>;
  }

  return (
    <>
      <TeamPerformanceCard account={account} onSync={onSync} isSyncing={isSyncing} cooldownSeconds={cooldownSeconds} />
      <div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <YearlyRatingChart rankings={account.ctf_team_profile?.yearly_rankings ?? []} />
        <SyncSummary account={account} />
      </div>
      <div className="mt-6"><YearlyRankingsTable rankings={account.ctf_team_profile?.yearly_rankings ?? []} /></div>
    </>
  );
}
