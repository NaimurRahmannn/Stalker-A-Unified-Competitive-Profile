import { Code2, Database, Medal, Trophy } from "lucide-react";
import { formatNumber, formatPoints, formatRank, formatTier, formatTimestamp } from "../formatters";
import type { KaggleTrack, KaggleTrackStatistics } from "../types";

const trackLabels: Record<KaggleTrack, string> = {
  competitions: "Competitions", code: "Code", datasets: "Datasets",
};
const trackIcons = { competitions: Trophy, code: Code2, datasets: Database };

export function KaggleTrackCard({ track, statistics, collected }: {
  track: KaggleTrack; statistics: KaggleTrackStatistics; collected: boolean;
}) {
  const Icon = trackIcons[track];
  const medals = [
    { label: "Gold", value: statistics.gold_medals, color: "text-amber-600 bg-amber-50" },
    { label: "Silver", value: statistics.silver_medals, color: "text-slate-600 bg-slate-100" },
    { label: "Bronze", value: statistics.bronze_medals, color: "text-orange-700 bg-orange-50" },
  ];
  return <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <div className="flex items-center gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-orange-50 text-orange-600 ring-1 ring-orange-100"><Icon className="size-5" /></span><div><h3 className="text-base font-semibold text-slate-950">{trackLabels[track]}</h3><p className="text-xs text-slate-500">Kaggle track ranking</p></div></div>
    <div className="mt-5 border-t border-slate-100 pt-4"><p className="text-xs font-medium text-slate-500">Current global rank</p><p className="mt-1 break-words text-2xl font-semibold text-orange-600">{formatRank(statistics.global_rank, statistics.rank_status, collected)}</p><span className="mt-2 inline-flex rounded-full bg-orange-50 px-2.5 py-1 text-xs font-medium text-orange-700">{statistics.rank_status === "ranked" ? "Ranked" : statistics.rank_status === "unranked" ? "Unranked" : collected ? "Rank unknown" : "Not collected"}</span></div>
    <dl className="mt-5 grid grid-cols-2 gap-3 text-sm"><div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Highest rank</dt><dd className="mt-1 font-semibold text-slate-950">{statistics.highest_rank === null ? "Not available" : `#${formatNumber(statistics.highest_rank)}`}</dd></div><div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Tier</dt><dd className="mt-1 font-semibold text-slate-950">{formatTier(statistics.tier)}</dd></div><div className="col-span-2 rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Ranking points</dt><dd className="mt-1 font-semibold text-slate-950">{formatPoints(statistics.points)}</dd></div></dl>
    <div className="mt-5 border-t border-slate-100 pt-4"><p className="text-xs font-medium text-slate-500">Medals in this track</p><div className="mt-3 grid grid-cols-3 gap-2">{medals.map(({ label, value, color }) => <div key={label} className={`min-w-0 rounded-xl p-2 text-center ${color}`}><Medal aria-hidden="true" className="mx-auto size-4" /><p className="mt-1 text-xs font-semibold">{value === null ? "—" : formatNumber(value)}</p><p className="text-[11px]">{label}</p></div>)}</div></div>
    <p className="mt-4 text-xs text-slate-500">Last collected: {formatTimestamp(statistics.data_collected_at)}</p>
  </article>;
}

export { trackLabels };
