import { TrendingUp } from "lucide-react";
import type { CodeforcesRatingHistoryEntry } from "../types";

const WIDTH = 760;
const HEIGHT = 300;
const PADDING = { top: 28, right: 24, bottom: 42, left: 52 };

function formatChartDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en", { month: "short", year: "2-digit" }).format(date);
}

export function RatingProgressChart({ history }: { history: CodeforcesRatingHistoryEntry[] }) {
  if (history.length === 0) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
        <div className="flex items-center gap-2"><TrendingUp className="size-4.5 text-emerald-600" /><h2 className="text-sm font-semibold text-slate-950">Rating Progress</h2></div>
        <div className="mt-4 grid min-h-64 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center"><div><p className="text-sm font-semibold text-slate-800">No rated contests yet</p><p className="mt-1 text-xs leading-5 text-slate-500">Codeforces rating changes will appear after a rated contest and the next sync.</p></div></div>
      </section>
    );
  }

  const ratings = history.map((item) => item.new_rating);
  const rawMin = Math.min(...ratings);
  const rawMax = Math.max(...ratings);
  const range = Math.max(100, rawMax - rawMin);
  const minRating = Math.max(0, Math.floor((rawMin - range * 0.15) / 100) * 100);
  const maxRating = Math.ceil((rawMax + range * 0.15) / 100) * 100;
  const chartWidth = WIDTH - PADDING.left - PADDING.right;
  const chartHeight = HEIGHT - PADDING.top - PADDING.bottom;
  const xFor = (index: number) => history.length === 1 ? PADDING.left + chartWidth / 2 : PADDING.left + (index / (history.length - 1)) * chartWidth;
  const yFor = (rating: number) => PADDING.top + ((maxRating - rating) / Math.max(1, maxRating - minRating)) * chartHeight;
  const points = history.map((item, index) => `${xFor(index)},${yFor(item.new_rating)}`).join(" ");
  const gridValues = Array.from({ length: 5 }, (_, index) => Math.round(maxRating - ((maxRating - minRating) / 4) * index));
  const xLabels = Array.from(new Set([0, Math.floor((history.length - 1) / 2), history.length - 1]));

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><TrendingUp className="size-4.5 text-emerald-600" /><h2 className="text-sm font-semibold text-slate-950">Rating Progress</h2></div><p className="text-[11px] font-medium text-slate-500">{history.length} rated {history.length === 1 ? "contest" : "contests"}</p></div>
      <div className="mt-4 overflow-hidden rounded-xl border border-slate-100 bg-[linear-gradient(to_bottom,#ffffff,#f8fafc)] p-2">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`Codeforces rating progression across ${history.length} rated contests`} className="h-auto min-h-64 w-full">
          <defs><linearGradient id="rating-area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#10b981" stopOpacity=".2" /><stop offset="1" stopColor="#10b981" stopOpacity="0" /></linearGradient></defs>
          {gridValues.map((value) => { const y = yFor(value); return <g key={value}><line x1={PADDING.left} x2={WIDTH - PADDING.right} y1={y} y2={y} stroke="#e2e8f0" strokeDasharray="4 5" /><text x={PADDING.left - 10} y={y + 4} textAnchor="end" className="fill-slate-400 text-[10px]">{value}</text></g>; })}
          <polygon points={`${PADDING.left},${HEIGHT - PADDING.bottom} ${points} ${WIDTH - PADDING.right},${HEIGHT - PADDING.bottom}`} fill="url(#rating-area)" />
          <polyline points={points} fill="none" stroke="#059669" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          {history.map((item, index) => <circle key={`${item.contest_id ?? "contest"}-${item.timestamp}`} cx={xFor(index)} cy={yFor(item.new_rating)} r={history.length === 1 ? 6 : 4} fill="#fff" stroke="#059669" strokeWidth="3"><title>{`${item.contest_name ?? "Rated contest"}: ${item.new_rating}${item.rating_change === null ? "" : ` (${item.rating_change >= 0 ? "+" : ""}${item.rating_change})`}`}</title></circle>)}
          {xLabels.map((index) => <text key={index} x={xFor(index)} y={HEIGHT - 15} textAnchor={index === 0 ? "start" : index === history.length - 1 ? "end" : "middle"} className="fill-slate-400 text-[10px]">{formatChartDate(history[index].timestamp)}</text>)}
        </svg>
      </div>
      <p className="mt-3 text-[11px] text-slate-500">Hover a point to see its contest and rating change.</p>
    </section>
  );
}
