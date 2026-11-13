import { Code2, Database, Medal, Trophy } from "lucide-react";
import { formatNumber, formatPoints, formatRank, formatTier, formatTimestamp } from "../formatters";
import type { KaggleManualTrackStatistics, KaggleTrack, KaggleTrackStatistics } from "../types";
import { KaggleTierIcon } from "./kaggle-tier-icon";

const trackLabels: Record<KaggleTrack, string> = {
  competitions: "Competitions", code: "Code", datasets: "Datasets",
};
const trackIcons = { competitions: Trophy, code: Code2, datasets: Database };

export function KaggleTrackCard({ track, statistics, collected, manual }: {
  track: KaggleTrack; statistics: KaggleTrackStatistics | KaggleManualTrackStatistics; collected: boolean;
  manual?: boolean;
}) {
  const Icon = trackIcons[track];
  const medals = [
    { label: "Gold", value: statistics.gold_medals, color: "text-amber-600 bg-amber-50" },
    { label: "Silver", value: statistics.silver_medals, color: "text-slate-600 bg-slate-100" },
    { label: "Bronze", value: statistics.bronze_medals, color: "text-amber-800 bg-amber-50/80" },
  ];
  return <article className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6 transition hover:border-sky-200 hover:shadow-md">
    <div className="flex items-center gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#E8F8FE] text-[#087EA4] ring-1 ring-sky-100"><Icon className="size-5" /></span><div><h3 className="text-base font-semibold text-slate-950">{trackLabels[track]}</h3><p className="text-xs text-slate-500">{manual ? "Self reported · not verified" : "Kaggle track ranking"}</p></div></div>
    <div className="mt-5 border-t border-slate-100 pt-4"><p className="text-xs font-medium text-slate-500">Current global rank</p><p className="mt-1 break-words text-2xl font-semibold text-slate-950">{collected ? formatRank(statistics.global_rank, statistics.rank_status, true) : "Not entered"}</p><span className="mt-2 inline-flex rounded-full bg-[#E8F8FE] px-2.5 py-1 text-xs font-medium text-[#087EA4] ring-1 ring-sky-200/60">{statistics.rank_status === "ranked" ? "Ranked" : statistics.rank_status === "unranked" ? "Unranked" : collected ? "Rank unknown" : "Not entered"}</span></div>
    <dl className="mt-5 grid grid-cols-2 gap-3 text-sm"><div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Highest rank</dt><dd className="mt-1 font-semibold text-slate-950">{statistics.highest_rank === null ? "Not available" : `#${formatNumber(statistics.highest_rank)}`}</dd></div><div className="rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Tier</dt><dd className="mt-1 flex items-center gap-2 font-semibold text-slate-950"><KaggleTierIcon tier={statistics.tier} className="size-6 shrink-0" />{formatTier(statistics.tier)}</dd></div><div className="col-span-2 rounded-xl border border-slate-100 bg-slate-50 p-3"><dt className="text-xs text-slate-500">Ranking points</dt><dd className="mt-1 font-semibold text-slate-950">{formatPoints(statistics.points)}</dd></div></dl>
    <div className="mt-5 border-t border-slate-100 pt-4"><p className="text-xs font-medium text-slate-500">Medals in this track</p><div className="mt-3 grid grid-cols-3 gap-2">{medals.map(({ label, value, color }) => <div key={label} className={`min-w-0 rounded-xl p-2 text-center ${color}`}><Medal aria-hidden="true" className="mx-auto size-4" /><p className="mt-1 text-xs font-semibold">{value === null ? "—" : formatNumber(value)}</p><p className="text-[11px]">{label}</p></div>)}</div></div>
    {(manual || collected) && <p className="mt-4 text-xs text-slate-500">{manual ? "Last updated" : "Last collected"}: {formatTimestamp("updated_at" in statistics ? statistics.updated_at : statistics.data_collected_at)}</p>}
  </article>;
}

export { trackLabels };
